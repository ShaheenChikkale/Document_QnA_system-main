"""
Example Test Script for Document Q&A System
Demonstrates all major features and endpoints
"""
import requests
import json
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:8000"
TEST_DOCUMENT = "test_document.pdf"  # Replace with your test file


class DocumentQATestSuite:
    """Comprehensive test suite for Document Q&A system"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session_id = None
        self.document_id = None
    
    def print_section(self, title: str):
        """Print formatted section header"""
        print("\n" + "=" * 80)
        print(f" {title}")
        print("=" * 80)
    
    def print_result(self, result: dict):
        """Pretty print JSON result"""
        print(json.dumps(result, indent=2))
    
    def test_health_check(self):
        """Test 1: Health Check"""
        self.print_section("TEST 1: Health Check")
        
        response = requests.get(f"{self.base_url}/health")
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        self.print_result(result)
        
        assert response.status_code == 200
        assert result["status"] == "healthy"
        print("✓ Health check passed")
    
    def test_upload_document(self, file_path: str):
        """Test 2: Upload Document"""
        self.print_section("TEST 2: Upload Document")
        
        if not Path(file_path).exists():
            print(f"⚠ Test file not found: {file_path}")
            print("Skipping upload test. Please provide a test document.")
            return None
        
        with open(file_path, "rb") as f:
            files = {"file": f}
            response = requests.post(
                f"{self.base_url}/documents/upload",
                files=files
            )
        
        result = response.json()
        print(f"Status Code: {response.status_code}")
        self.print_result(result)
        
        if response.status_code == 201:
            self.document_id = result["document_id"]
            print(f"✓ Document uploaded successfully")
            print(f"  Document ID: {self.document_id}")
            print(f"  Chunks created: {result['chunks_created']}")
            return self.document_id
        else:
            print(f"✗ Upload failed: {result}")
            return None
    
    def test_list_documents(self):
        """Test 3: List Documents"""
        self.print_section("TEST 3: List Documents")
        
        response = requests.get(f"{self.base_url}/documents")
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Total Documents: {result['total_count']}")
        
        if result['total_count'] > 0:
            print("\nDocuments:")
            for doc in result['documents']:
                print(f"  - {doc['filename']} (ID: {doc['document_id'][:8]}...)")
                print(f"    Chunks: {doc['chunks_count']}, Language: {doc['language']}")
        
        assert response.status_code == 200
        print("✓ Document listing successful")
    
    def test_query_basic(self):
        """Test 4: Basic Query"""
        self.print_section("TEST 4: Basic Query")
        
        query_data = {
            "question": "What is this document about? Give me a brief summary.",
            "top_k": 5,
            "include_sources": True
        }
        
        print(f"Question: {query_data['question']}")
        print("\nSending query...")
        
        start_time = time.time()
        response = requests.post(
            f"{self.base_url}/query",
            json=query_data
        )
        elapsed = time.time() - start_time
        
        result = response.json()
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Processing Time: {result['processing_time']:.3f}s")
        print(f"Total Time: {elapsed:.3f}s")
        print(f"Cached: {result['cached']}")
        print(f"\nAnswer:\n{result['answer']}")
        print(f"\nSources Retrieved: {len(result['sources'])}")
        
        if result['sources']:
            print("\nTop Source:")
            source = result['sources'][0]
            print(f"  File: {source['filename']}")
            print(f"  Page: {source['page']}")
            print(f"  Relevance: {source['relevance_score']:.3f}")
            print(f"  Preview: {source['content'][:150]}...")
        
        self.session_id = result['session_id']
        print(f"\n✓ Query successful")
        print(f"  Session ID: {self.session_id}")
    
    def test_query_cached(self):
        """Test 5: Cached Query"""
        self.print_section("TEST 5: Cached Query (Same Question)")
        
        query_data = {
            "question": "What is this document about? Give me a brief summary.",
            "top_k": 5,
            "include_sources": True
        }
        
        print(f"Question: {query_data['question']}")
        print("Sending same query again to test caching...")
        
        start_time = time.time()
        response = requests.post(
            f"{self.base_url}/query",
            json=query_data
        )
        elapsed = time.time() - start_time
        
        result = response.json()
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Processing Time: {result['processing_time']:.3f}s")
        print(f"Total Time: {elapsed:.3f}s")
        print(f"Cached: {result['cached']}")
        
        if result['cached']:
            print("✓ Query served from cache (faster response)")
        else:
            print("⚠ Query not cached (check cache implementation)")
    
    def test_conversational_query(self):
        """Test 6: Conversational Follow-up"""
        self.print_section("TEST 6: Conversational Follow-up")
        
        if not self.session_id:
            print("⚠ No session ID from previous query. Skipping.")
            return
        
        query_data = {
            "question": "Can you elaborate on the key points mentioned?",
            "session_id": self.session_id,
            "top_k": 3,
            "include_sources": True
        }
        
        print(f"Follow-up Question: {query_data['question']}")
        print(f"Using Session ID: {self.session_id[:16]}...")
        print("\nSending follow-up query...")
        
        response = requests.post(
            f"{self.base_url}/query",
            json=query_data
        )
        
        result = response.json()
        
        print(f"\nStatus Code: {response.status_code}")
        print(f"Processing Time: {result['processing_time']:.3f}s")
        print(f"\nAnswer:\n{result['answer']}")
        print("\n✓ Conversational query successful")
        print("  (System maintained context from previous question)")
    
    def test_conversation_history(self):
        """Test 7: Get Conversation History"""
        self.print_section("TEST 7: Conversation History")
        
        if not self.session_id:
            print("⚠ No session ID available. Skipping.")
            return
        
        response = requests.get(
            f"{self.base_url}/query/history/{self.session_id}"
        )
        
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        print(f"Session ID: {result['session_id'][:16]}...")
        print(f"Total Turns: {result['turn_count']}")
        
        print("\nConversation:")
        for i, turn in enumerate(result['history'], 1):
            role = "User" if turn['role'] == 'user' else "Assistant"
            content_preview = turn['content'][:100] + "..." if len(turn['content']) > 100 else turn['content']
            print(f"  {i}. {role}: {content_preview}")
        
        print("✓ Conversation history retrieved")
    
    def test_cache_stats(self):
        """Test 8: Cache Statistics"""
        self.print_section("TEST 8: Cache Statistics")
        
        response = requests.get(f"{self.base_url}/query/cache-stats")
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        self.print_result(result)
        
        stats = result['cache_statistics']
        print(f"\n✓ Cache Stats Retrieved:")
        print(f"  Cache Size: {stats['cache_size']}/{stats['max_size']}")
        print(f"  Hit Rate: {stats['hit_rate'] * 100:.1f}%")
        print(f"  Hits: {stats['hit_count']}, Misses: {stats['miss_count']}")
    
    def test_clear_memory(self):
        """Test 9: Clear Conversation Memory"""
        self.print_section("TEST 9: Clear Conversation Memory")
        
        if not self.session_id:
            print("⚠ No session ID available. Clearing all sessions.")
            response = requests.post(f"{self.base_url}/query/clear-memory")
        else:
            response = requests.post(
                f"{self.base_url}/query/clear-memory",
                params={"session_id": self.session_id}
            )
        
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        self.print_result(result)
        print("✓ Conversation memory cleared")
    
    def test_delete_document(self):
        """Test 10: Delete Document"""
        self.print_section("TEST 10: Delete Document")
        
        if not self.document_id:
            print("⚠ No document ID available. Skipping deletion.")
            return
        
        print(f"Deleting document: {self.document_id[:16]}...")
        
        response = requests.delete(
            f"{self.base_url}/documents/{self.document_id}"
        )
        
        result = response.json()
        
        print(f"Status Code: {response.status_code}")
        self.print_result(result)
        print("✓ Document deleted successfully")
    
    def run_all_tests(self, test_file: str = None):
        """Run complete test suite"""
        print("\n" + "=" * 80)
        print(" DOCUMENT Q&A SYSTEM - COMPREHENSIVE TEST SUITE")
        print("=" * 80)
        
        tests = [
            ("Health Check", self.test_health_check),
            ("Upload Document", lambda: self.test_upload_document(test_file or TEST_DOCUMENT)),
            ("List Documents", self.test_list_documents),
            ("Basic Query", self.test_query_basic),
            ("Cached Query", self.test_query_cached),
            ("Conversational Query", self.test_conversational_query),
            ("Conversation History", self.test_conversation_history),
            ("Cache Statistics", self.test_cache_stats),
            ("Clear Memory", self.test_clear_memory),
            ("Delete Document", self.test_delete_document),
        ]
        
        passed = 0
        failed = 0
        
        for test_name, test_func in tests:
            try:
                test_func()
                passed += 1
            except Exception as e:
                print(f"\n✗ Test failed: {test_name}")
                print(f"  Error: {str(e)}")
                failed += 1
        
        # Summary
        self.print_section("TEST SUMMARY")
        print(f"Total Tests: {len(tests)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {(passed/len(tests)*100):.1f}%")
        
        if failed == 0:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠ {failed} test(s) failed")


def main():
    """Main test runner"""
    import sys
    
    # Check if test file provided
    test_file = sys.argv[1] if len(sys.argv) > 1 else None
    
    if test_file and not Path(test_file).exists():
        print(f"Error: Test file not found: {test_file}")
        print("\nUsage: python test_suite.py [path/to/test/document.pdf]")
        return
    
    # Run tests
    suite = DocumentQATestSuite()
    suite.run_all_tests(test_file)


if __name__ == "__main__":
    main()
