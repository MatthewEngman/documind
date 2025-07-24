#!/usr/bin/env python3
"""
Test setup script for DocuMind - validates complete system setup
"""
import sys
import os
import logging
import asyncio
import requests
from typing import Dict, Any, List
import json

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

from app.database.redis_client import redis_client
from app.services.embedding_service import EmbeddingService
from app.services.search_service import SearchService
from app.services.document_processor import DocumentProcessor

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SetupTester:
    """Comprehensive setup testing for DocuMind"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.test_results = {}
        self.failed_tests = []
        self.passed_tests = []
    
    def test_redis_connection(self) -> bool:
        """Test Redis connection and basic operations"""
        try:
            logger.info("Testing Redis connection...")
            
            # Basic connection test
            if not redis_client.health_check():
                self.failed_tests.append("Redis health check failed")
                return False
            
            # Test basic operations
            test_key = "test:setup_validation"
            test_value = "test_value_12345"
            
            # SET operation
            redis_client.client.set(test_key, test_value, ex=60)
            
            # GET operation
            retrieved_value = redis_client.client.get(test_key)
            if retrieved_value != test_value:
                self.failed_tests.append("Redis SET/GET operations failed")
                return False
            
            # JSON operations
            test_json = {"test": True, "timestamp": "2025-01-01"}
            redis_client.set_json(f"{test_key}_json", test_json, ttl=60)
            retrieved_json = redis_client.get_json(f"{test_key}_json")
            
            if not retrieved_json or retrieved_json.get("test") != True:
                self.failed_tests.append("Redis JSON operations failed")
                return False
            
            # Cleanup
            redis_client.client.delete(test_key, f"{test_key}_json")
            
            self.passed_tests.append("Redis connection and operations")
            return True
            
        except Exception as e:
            self.failed_tests.append(f"Redis connection test failed: {e}")
            return False
    
    def test_api_endpoints(self) -> bool:
        """Test API endpoints availability and functionality"""
        try:
            logger.info("Testing API endpoints...")
            
            endpoints_to_test = [
                ("/health", "GET"),
                ("/api/stats", "GET"),
                ("/api/test", "GET"),
                ("/docs", "GET"),  # FastAPI docs
            ]
            
            all_passed = True
            
            for endpoint, method in endpoints_to_test:
                try:
                    if method == "GET":
                        response = requests.get(f"{self.api_base_url}{endpoint}", timeout=10)
                    
                    if response.status_code not in [200, 307]:  # 307 for redirects
                        self.failed_tests.append(f"API endpoint {endpoint} returned status {response.status_code}")
                        all_passed = False
                    else:
                        logger.debug(f"✅ {endpoint}: {response.status_code}")
                        
                except requests.exceptions.RequestException as e:
                    self.failed_tests.append(f"API endpoint {endpoint} failed: {e}")
                    all_passed = False
            
            if all_passed:
                self.passed_tests.append("API endpoints accessibility")
            
            return all_passed
            
        except Exception as e:
            self.failed_tests.append(f"API endpoint testing failed: {e}")
            return False
    
    async def test_embedding_service(self) -> bool:
        """Test embedding service functionality"""
        try:
            logger.info("Testing embedding service...")
            
            embedding_service = EmbeddingService()
            
            # Test single embedding generation
            test_text = "This is a test document for embedding generation."
            embedding = await embedding_service.generate_embedding(test_text)
            
            if not embedding or not isinstance(embedding, list) or len(embedding) == 0:
                self.failed_tests.append("Embedding generation failed")
                return False
            
            # Test batch embedding generation
            test_texts = [
                "First test document",
                "Second test document", 
                "Third test document"
            ]
            
            batch_embeddings = await embedding_service.generate_embeddings_batch(test_texts)
            
            if not batch_embeddings or len(batch_embeddings) != len(test_texts):
                self.failed_tests.append("Batch embedding generation failed")
                return False
            
            # Test similarity calculation
            similarity = embedding_service.calculate_similarity(embedding, batch_embeddings[0])
            
            if not isinstance(similarity, (int, float)) or similarity < 0 or similarity > 1:
                self.failed_tests.append("Similarity calculation failed")
                return False
            
            self.passed_tests.append("Embedding service functionality")
            return True
            
        except Exception as e:
            self.failed_tests.append(f"Embedding service test failed: {e}")
            return False
    
    async def test_document_processing(self) -> bool:
        """Test document processing functionality"""
        try:
            logger.info("Testing document processing...")
            
            doc_processor = DocumentProcessor()
            
            # Test text extraction (TXT)
            test_content = "This is a test document with multiple sentences. It contains various information for testing purposes."
            test_bytes = test_content.encode('utf-8')
            
            extracted_text = await doc_processor.extract_text(test_bytes, 'txt')
            
            if not extracted_text or extracted_text.strip() != test_content:
                self.failed_tests.append("Text extraction failed")
                return False
            
            # Test text chunking
            chunks = doc_processor.chunk_text(extracted_text, chunk_size=50, overlap=10)
            
            if not chunks or len(chunks) == 0:
                self.failed_tests.append("Text chunking failed")
                return False
            
            # Test metadata extraction
            metadata = doc_processor.extract_metadata(extracted_text, "test.txt")
            
            if not metadata or "word_count" not in metadata:
                self.failed_tests.append("Metadata extraction failed")
                return False
            
            # Test document validation
            validation = doc_processor.validate_document(test_bytes, "test.txt")
            
            if not validation or not validation.get("valid"):
                self.failed_tests.append("Document validation failed")
                return False
            
            self.passed_tests.append("Document processing functionality")
            return True
            
        except Exception as e:
            self.failed_tests.append(f"Document processing test failed: {e}")
            return False
    
    async def test_search_functionality(self) -> bool:
        """Test search service functionality"""
        try:
            logger.info("Testing search functionality...")
            
            search_service = SearchService()
            embedding_service = EmbeddingService()
            
            # Create a test query embedding
            test_query = "machine learning algorithms"
            query_embedding = await embedding_service.generate_embedding(test_query)
            
            if not query_embedding:
                self.failed_tests.append("Query embedding generation failed")
                return False
            
            # Test search (may return empty results if no documents are indexed)
            search_results = await search_service.search_similar_documents(
                query_embedding=query_embedding,
                limit=5,
                threshold=0.5
            )
            
            # Search should return a list (even if empty)
            if not isinstance(search_results, list):
                self.failed_tests.append("Search results format invalid")
                return False
            
            # Test index stats
            index_stats = search_service.get_index_stats()
            
            if not isinstance(index_stats, dict):
                self.failed_tests.append("Index stats retrieval failed")
                return False
            
            # Test keyword search fallback
            keyword_results = await search_service.search_by_keywords(["test", "document"])
            
            if not isinstance(keyword_results, list):
                self.failed_tests.append("Keyword search failed")
                return False
            
            self.passed_tests.append("Search functionality")
            return True
            
        except Exception as e:
            self.failed_tests.append(f"Search functionality test failed: {e}")
            return False
    
    def test_configuration(self) -> bool:
        """Test configuration and environment setup"""
        try:
            logger.info("Testing configuration...")
            
            from app.config import settings
            
            # Check required configuration
            required_configs = [
                'redis_host',
                'redis_port', 
                'api_host',
                'api_port',
                'embedding_dimensions'
            ]
            
            missing_configs = []
            for config in required_configs:
                if not hasattr(settings, config):
                    missing_configs.append(config)
            
            if missing_configs:
                self.failed_tests.append(f"Missing configurations: {missing_configs}")
                return False
            
            # Check Redis configuration
            if not settings.redis_host or not settings.redis_port:
                self.failed_tests.append("Redis configuration incomplete")
                return False
            
            self.passed_tests.append("Configuration validation")
            return True
            
        except Exception as e:
            self.failed_tests.append(f"Configuration test failed: {e}")
            return False
    
    def test_file_structure(self) -> bool:
        """Test that all required files exist"""
        try:
            logger.info("Testing file structure...")
            
            backend_path = os.path.join(os.path.dirname(__file__), '..', 'backend')
            
            required_files = [
                'app/__init__.py',
                'app/main.py',
                'app/config.py',
                'app/database/__init__.py',
                'app/database/redis_client.py',
                'app/database/models.py',
                'app/api/__init__.py',
                'app/api/documents.py',
                'app/api/search.py',
                'app/api/analytics.py',
                'app/services/__init__.py',
                'app/services/document_processor.py',
                'app/services/embedding_service.py',
                'app/services/search_service.py',
                'app/utils/__init__.py',
                'app/utils/file_handlers.py',
                'app/utils/cache.py',
                'requirements.txt',
                '.env.example'
            ]
            
            missing_files = []
            for file_path in required_files:
                full_path = os.path.join(backend_path, file_path)
                if not os.path.exists(full_path):
                    missing_files.append(file_path)
            
            if missing_files:
                self.failed_tests.append(f"Missing files: {missing_files}")
                return False
            
            self.passed_tests.append("File structure validation")
            return True
            
        except Exception as e:
            self.failed_tests.append(f"File structure test failed: {e}")
            return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all setup tests"""
        logger.info("🧪 Running DocuMind Setup Tests")
        
        test_results = {
            "timestamp": "2025-01-01T00:00:00Z",
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "success_rate": 0.0,
            "details": {}
        }
        
        # Define tests to run
        tests = [
            ("File Structure", self.test_file_structure),
            ("Configuration", self.test_configuration),
            ("Redis Connection", self.test_redis_connection),
            ("API Endpoints", self.test_api_endpoints),
            ("Embedding Service", self.test_embedding_service),
            ("Document Processing", self.test_document_processing),
            ("Search Functionality", self.test_search_functionality)
        ]
        
        # Run tests
        for test_name, test_func in tests:
            try:
                logger.info(f"Running: {test_name}")
                
                if asyncio.iscoroutinefunction(test_func):
                    result = await test_func()
                else:
                    result = test_func()
                
                test_results["tests_run"] += 1
                
                if result:
                    test_results["tests_passed"] += 1
                    test_results["details"][test_name] = "PASSED"
                    logger.info(f"✅ {test_name}: PASSED")
                else:
                    test_results["tests_failed"] += 1
                    test_results["details"][test_name] = "FAILED"
                    logger.error(f"❌ {test_name}: FAILED")
                    
            except Exception as e:
                test_results["tests_run"] += 1
                test_results["tests_failed"] += 1
                test_results["details"][test_name] = f"ERROR: {e}"
                logger.error(f"❌ {test_name}: ERROR - {e}")
        
        # Calculate success rate
        if test_results["tests_run"] > 0:
            test_results["success_rate"] = test_results["tests_passed"] / test_results["tests_run"]
        
        # Add summary
        test_results["passed_tests"] = self.passed_tests
        test_results["failed_tests"] = self.failed_tests
        
        return test_results
    
    def print_test_summary(self, results: Dict[str, Any]):
        """Print formatted test results"""
        print("\n📋 DocuMind Setup Test Results")
        print("=" * 50)
        
        print(f"\nTests Run: {results['tests_run']}")
        print(f"Tests Passed: {results['tests_passed']}")
        print(f"Tests Failed: {results['tests_failed']}")
        print(f"Success Rate: {results['success_rate']*100:.1f}%")
        
        print(f"\n✅ Passed Tests:")
        for test in results.get('passed_tests', []):
            print(f"  - {test}")
        
        if results.get('failed_tests'):
            print(f"\n❌ Failed Tests:")
            for test in results['failed_tests']:
                print(f"  - {test}")
        
        print(f"\n📊 Detailed Results:")
        for test_name, status in results['details'].items():
            status_icon = "✅" if status == "PASSED" else "❌"
            print(f"  {status_icon} {test_name}: {status}")

async def main():
    """Main test function"""
    print("🧪 DocuMind Setup Validation")
    print("=" * 50)
    
    # Initialize tester
    tester = SetupTester()
    
    # Run all tests
    results = await tester.run_all_tests()
    
    # Print results
    tester.print_test_summary(results)
    
    # Save results
    try:
        results_file = "setup_test_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Test results saved to: {results_file}")
    except Exception as e:
        logger.warning(f"Failed to save test results: {e}")
    
    # Exit with appropriate code
    if results['success_rate'] == 1.0:
        print("\n🎉 All tests passed! Your DocuMind setup is ready.")
        sys.exit(0)
    elif results['success_rate'] >= 0.8:
        print("\n⚠️  Most tests passed, but some issues were found. Check the failed tests above.")
        sys.exit(1)
    else:
        print("\n❌ Multiple tests failed. Please review your setup and configuration.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
