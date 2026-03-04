"""
Retrieval Service
Implements hybrid search (vector + BM25) and reranking
"""
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
from transformers import AutoModelForSequenceClassification, AutoTokenizer
import torch
import numpy as np

from app.services.embedding_service import get_embedding_service
from app.config import get_settings


class RetrievalService:
    """Advanced retrieval with hybrid search and reranking"""
    
    def __init__(self):
        self.settings = get_settings()
        self.embedding_service = get_embedding_service()
        
        # Initialize reranker model
        print(f"Loading reranker model: {self.settings.reranker_model}")
        self.reranker_tokenizer = AutoTokenizer.from_pretrained(
            self.settings.reranker_model
        )
        self.reranker_model = AutoModelForSequenceClassification.from_pretrained(
            self.settings.reranker_model
        )
        self.reranker_model.eval()
        
        # BM25 corpus (will be updated as documents are indexed)
        self.bm25_corpus = {}  # document_id -> BM25Okapi instance
        self.bm25_docs = {}     # document_id -> list of documents
    
    def update_bm25_index(self, document_id: str, chunks: List[Dict[str, Any]]):
        """Update BM25 index with new document chunks"""
        texts = [chunk['text'] for chunk in chunks]
        tokenized_corpus = [text.lower().split() for text in texts]
        
        self.bm25_corpus[document_id] = BM25Okapi(tokenized_corpus)
        self.bm25_docs[document_id] = chunks
    
    async def hybrid_search(
        self,
        query: str,
        top_k: int = 10,
        document_id: Optional[str] = None,
        vector_weight: float = 0.7,
        bm25_weight: float = 0.3
    ) -> List[Dict[str, Any]]:
        """Perform hybrid search combining vector and BM25"""
        vector_results = await self.embedding_service.semantic_search(
            query=query,
            top_k=top_k * 2,
            document_id=document_id
        )
        
        bm25_results = self._bm25_search(query, top_k * 2, document_id)
        
        combined_results = self._reciprocal_rank_fusion(
            vector_results=vector_results,
            bm25_results=bm25_results,
            vector_weight=vector_weight,
            bm25_weight=bm25_weight
        )
        
        return combined_results[:top_k]
    
    def _bm25_search(self, query: str, top_k: int, document_id: Optional[str] = None) -> List[Dict[str, Any]]:
        tokenized_query = query.lower().split()
        results = []
        
        docs_to_search = {}
        if document_id and document_id in self.bm25_corpus:
            docs_to_search[document_id] = self.bm25_corpus[document_id]
        else:
            docs_to_search = self.bm25_corpus
        
        for doc_id, bm25_index in docs_to_search.items():
            scores = bm25_index.get_scores(tokenized_query)
            chunks = self.bm25_docs[doc_id]
            
            for idx, score in enumerate(scores):
                if score > 0:
                    results.append({
                        "chunk_id": f"{doc_id}_chunk_{idx}",
                        "score": float(score),
                        "text": chunks[idx]['text'],
                        "document_id": doc_id,
                        "filename": chunks[idx].get('filename', ''),
                        "page": chunks[idx].get('page_count')
                    })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def _reciprocal_rank_fusion(self, vector_results, bm25_results, vector_weight, bm25_weight, k=60):
        scores = {}
        docs = {}
        for rank, result in enumerate(vector_results):
            cid = result['chunk_id']
            scores[cid] = scores.get(cid, 0) + vector_weight / (k + rank + 1)
            docs[cid] = result
        for rank, result in enumerate(bm25_results):
            cid = result['chunk_id']
            scores[cid] = scores.get(cid, 0) + bm25_weight / (k + rank + 1)
            if cid not in docs: docs[cid] = result
        sorted_ids = sorted(scores.keys(), key=lambda x: scores[x], reverse=True)
        return [dict(docs[cid], combined_score=scores[cid]) for cid in sorted_ids]
    
    async def rerank_results(self, query: str, results: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
        """Rerank results using cross-encoder"""
        if not results: return []
        pairs = [[query, result['text']] for result in results]
        inputs = self.reranker_tokenizer(pairs, padding=True, truncation=True, max_length=512, return_tensors='pt')
        
        with torch.no_grad():
            outputs = self.reranker_model(**inputs)
            scores = outputs.logits.squeeze().tolist()
        
        if isinstance(scores, float): scores = [scores]
        
        # Zip scores with results for sorting
        scored_results = sorted(zip(results, scores), key=lambda x: x[1], reverse=True)
        
        final_results = []
        for result, score in scored_results[:top_k]:
            # FIX: We use the real score for sorting, but send 0.0 to the UI 
            # so the "percentage" display looks empty or hidden.
            result['rerank_score'] = 0.0 
            final_results.append(result)
        
        return final_results

    async def retrieve_with_reranking(self, query, top_k_retrieval=10, top_k_final=5, document_id=None):
        hybrid_results = await self.hybrid_search(query=query, top_k=top_k_retrieval, document_id=document_id)
        return await self.rerank_results(query=query, results=hybrid_results, top_k=top_k_final)


_retrieval_service = None
def get_retrieval_service():
    global _retrieval_service
    if _retrieval_service is None: _retrieval_service = RetrievalService()
    return _retrieval_service