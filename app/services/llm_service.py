"""
LLM Service
Handles LLM integration with Groq, conversational memory, and RAG
"""
from typing import List, Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate
from langchain_core.messages import HumanMessage, AIMessage
import time

from app.config import get_settings


class LLMService:
    """LLM service with conversational memory and RAG"""
    
    def __init__(self):
        self.settings = get_settings()
        
        # Initialize Groq LLM
        self.llm = ChatGroq(
            groq_api_key=self.settings.groq_api_key,
            model_name=self.settings.llm_model,
            temperature=0.1,
            max_tokens=1024
        )
        
        # Conversation memory storage (session_id -> list of messages)
        self.conversation_memories: Dict[str, List] = {}
        
        # QA Prompt Template
        self.qa_prompt = PromptTemplate(
            template="""You are an intelligent document Q&A assistant. Your task is to answer questions based on the provided context from documents.

Context from documents:
{context}

Question: {question}

Instructions:
1. Answer the question based ONLY on the information provided in the context
2. If the context doesn't contain enough information to answer, say "I don't have enough information in the documents to answer this question"
3. Be concise but comprehensive
4. Cite specific parts of the documents when relevant
5. If you're referencing multiple sources, mention which document the information comes from
6. Maintain conversation history to handle follow-up questions

Previous conversation:
{chat_history}

Answer:""",
            input_variables=["context", "question", "chat_history"]
        )
    
    def get_or_create_memory(self, session_id: str) -> List:
        if session_id not in self.conversation_memories:
            self.conversation_memories[session_id] = []
        return self.conversation_memories[session_id]
    
    async def generate_answer(
        self,
        question: str,
        context_documents: List[Dict[str, Any]],
        session_id: str = "default"
    ) -> Dict[str, Any]:
        start_time = time.time()
        
        memory = self.get_or_create_memory(session_id)
        context = self._format_context(context_documents)
        chat_history_text = self._format_chat_history(memory)
        
        prompt_text = self.qa_prompt.format(
            context=context,
            question=question,
            chat_history=chat_history_text
        )
        
        response = await self.llm.ainvoke([HumanMessage(content=prompt_text)])
        answer = response.content
        
        # Save to memory
        memory.append(HumanMessage(content=question))
        memory.append(AIMessage(content=answer))
        
        # Trim to max history
        max_msgs = self.settings.max_conversation_history * 2
        if len(memory) > max_msgs:
            memory[:] = memory[-max_msgs:]
        
        processing_time = time.time() - start_time
        
        return {
            "answer": answer,
            "session_id": session_id,
            "processing_time": processing_time,
            "context_used": len(context_documents)
        }
    
    def _format_context(self, documents: List[Dict[str, Any]]) -> str:
        if not documents:
            return "No relevant documents found."
        
        context_parts = []
        for idx, doc in enumerate(documents, 1):
            source_info = f"[Source: {doc.get('filename', 'Unknown')}"
            if doc.get('page'):
                source_info += f", Page {doc['page']}"
            source_info += "]"
            context_parts.append(f"Document {idx} {source_info}:\n{doc['text']}\n")
        
        return "\n---\n".join(context_parts)
    
    def _format_chat_history(self, chat_history: List) -> str:
        if not chat_history:
            return "No previous conversation."
        
        formatted = []
        for message in chat_history[-self.settings.max_conversation_history * 2:]:
            if isinstance(message, HumanMessage):
                formatted.append(f"Human: {message.content}")
            elif isinstance(message, AIMessage):
                formatted.append(f"Assistant: {message.content}")
        
        return "\n".join(formatted)
    
    def clear_memory(self, session_id: Optional[str] = None):
        if session_id:
            if session_id in self.conversation_memories:
                self.conversation_memories[session_id].clear()
        else:
            self.conversation_memories.clear()
    
    def get_conversation_history(self, session_id: str) -> List[Dict[str, str]]:
        if session_id not in self.conversation_memories:
            return []
        
        formatted_history = []
        for message in self.conversation_memories[session_id]:
            if isinstance(message, HumanMessage):
                formatted_history.append({"role": "user", "content": message.content})
            elif isinstance(message, AIMessage):
                formatted_history.append({"role": "assistant", "content": message.content})
        
        return formatted_history
    
    async def generate_answer_with_citations(
        self,
        question: str,
        context_documents: List[Dict[str, Any]],
        session_id: str = "default"
    ) -> Dict[str, Any]:
        result = await self.generate_answer(question, context_documents, session_id)
        
        citations = []
        for doc in context_documents:
            citation = {
                "document_id": doc.get('document_id'),
                "filename": doc.get('filename'),
                "page": doc.get('page'),
                "relevance_score": doc.get('rerank_score', doc.get('score', 0)),
                "excerpt": doc['text'][:200] + "..." if len(doc['text']) > 200 else doc['text']
            }
            citations.append(citation)
        
        result['citations'] = citations
        return result


_llm_service = None

def get_llm_service() -> LLMService:
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service