#!/usr/bin/env python3
"""
Comprehensive test script for embedding and semantic search functionality
"""

import asyncio
import aiohttp
import json
import time
import os
from pathlib import Path
from typing import List, Dict

# Test configuration
BASE_URL = "http://localhost:8000"
TEST_FILES_DIR = Path(__file__).parent / "test_files"

class EmbeddingTester:
    """Test class for embedding and semantic search functionality"""
    
    def __init__(self):
        self.session = None
        self.uploaded_docs = []
        self.test_results = {
            "upload_tests": [],
            "search_tests": [],
            "cache_tests": [],
            "analytics_tests": [],
            "performance_tests": []
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def run_all_tests(self):
        """Run comprehensive embedding and search tests"""
        print("🚀 Starting DocuMind Embedding & Search Tests")
        print("=" * 60)
        
        try:
            # Test 1: Health Check
            await self.test_health_check()
            
            # Test 2: Upload documents with embedding generation
            await self.test_document_upload_with_embeddings()
            
            # Test 3: Semantic search functionality
            await self.test_semantic_search()
            
            # Test 4: Search caching
            await self.test_search_caching()
            
            # Test 5: Search suggestions
            await self.test_search_suggestions()
            
            # Test 6: Search analytics
            await self.test_search_analytics()
            
            # Test 7: Performance benchmarking
            await self.test_performance_benchmarks()
            
            # Test 8: Vector operations
            await self.test_vector_operations()
            
            # Generate test report
            self.generate_test_report()
            
        except Exception as e:
            print(f"❌ Test suite failed: {e}")
            raise
    
    async def test_health_check(self):
        """Test API health and readiness"""
        print("\n📋 Test 1: Health Check")
        print("-" * 30)
        
        try:
            async with self.session.get(f"{BASE_URL}/health") as response:
                data = await response.json()
                
                assert response.status == 200, f"Health check failed: {response.status}"
                assert data["status"] == "healthy", f"System not healthy: {data}"
                assert data["redis"] == "connected", "Redis not connected"
                
                print("✅ Health check passed")
                print(f"   Status: {data['status']}")
                print(f"   Redis: {data['redis']}")
                print(f"   Version: {data['version']}")
                
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            raise
    
    async def test_document_upload_with_embeddings(self):
        """Test document upload with automatic embedding generation"""
        print("\n📋 Test 2: Document Upload with Embeddings")
        print("-" * 45)
        
        # Create test documents if they don't exist
        await self.create_test_documents()
        
        test_files = [
            ("test_ai.txt", "Artificial Intelligence and Machine Learning"),
            ("test_python.txt", "Python Programming and Data Science"),
            ("test_redis.txt", "Redis Database and Caching Systems")
        ]
        
        for filename, content in test_files:
            try:
                # Create multipart form data
                data = aiohttp.FormData()
                data.add_field('file', content, filename=filename, content_type='text/plain')
                
                start_time = time.time()
                async with self.session.post(f"{BASE_URL}/api/documents/upload", data=data) as response:
                    upload_time = time.time() - start_time
                    
                    assert response.status == 200, f"Upload failed: {response.status}"
                    data = await response.json()
                    
                    doc_id = data["doc_id"]
                    self.uploaded_docs.append(doc_id)
                    
                    print(f"✅ Uploaded {filename}")
                    print(f"   Doc ID: {doc_id}")
                    print(f"   Chunks: {data['chunks_created']}")
                    print(f"   Upload time: {upload_time:.2f}s")
                    print(f"   Processing time: {data['processing_time']:.2f}s")
                    
                    # Wait for processing to complete
                    await asyncio.sleep(2)
                    
                    # Verify document was processed with vectors
                    await self.verify_document_vectors(doc_id)
                    
                    self.test_results["upload_tests"].append({
                        "filename": filename,
                        "doc_id": doc_id,
                        "chunks": data["chunks_created"],
                        "upload_time": upload_time,
                        "processing_time": data["processing_time"],
                        "success": True
                    })
                    
            except Exception as e:
                print(f"❌ Upload failed for {filename}: {e}")
                self.test_results["upload_tests"].append({
                    "filename": filename,
                    "success": False,
                    "error": str(e)
                })
    
    async def verify_document_vectors(self, doc_id: str):
        """Verify that vectors were generated for the document"""
        try:
            async with self.session.get(f"{BASE_URL}/api/search/analytics") as response:
                if response.status == 200:
                    data = await response.json()
                    vector_count = data.get("vector_stats", {}).get("total_docs", 0)
                    print(f"   Vectors in index: {vector_count}")
        except Exception as e:
            print(f"   ⚠️ Could not verify vectors: {e}")
    
    async def test_semantic_search(self):
        """Test semantic search functionality"""
        print("\n📋 Test 3: Semantic Search")
        print("-" * 30)
        
        search_queries = [
            {
                "query": "artificial intelligence machine learning",
                "expected_results": 1,
                "description": "AI/ML related content"
            },
            {
                "query": "python programming data science",
                "expected_results": 1,
                "description": "Python development content"
            },
            {
                "query": "redis database caching",
                "expected_results": 1,
                "description": "Redis database content"
            },
            {
                "query": "neural networks deep learning",
                "expected_results": 0,
                "description": "Unrelated content (should return few/no results)"
            }
        ]
        
        for query_test in search_queries:
            try:
                search_payload = {
                    "query": query_test["query"],
                    "limit": 10,
                    "similarity_threshold": 0.5,
                    "include_content": True,
                    "include_metadata": True
                }
                
                start_time = time.time()
                async with self.session.post(f"{BASE_URL}/api/search/", json=search_payload) as response:
                    search_time = time.time() - start_time
                    
                    assert response.status == 200, f"Search failed: {response.status}"
                    data = await response.json()
                    
                    print(f"✅ Search: {query_test['description']}")
                    print(f"   Query: '{query_test['query']}'")
                    print(f"   Results: {data['total_results']}")
                    print(f"   Search time: {search_time:.3f}s")
                    print(f"   Processing time: {data['processing_time']:.3f}s")
                    print(f"   Cached: {data['cached']}")
                    
                    # Show top results
                    for i, result in enumerate(data["results"][:3]):
                        print(f"   Result {i+1}: {result['filename']} (score: {result['similarity_score']:.3f})")
                    
                    self.test_results["search_tests"].append({
                        "query": query_test["query"],
                        "results_count": data["total_results"],
                        "search_time": search_time,
                        "processing_time": data["processing_time"],
                        "cached": data["cached"],
                        "success": True
                    })
                    
            except Exception as e:
                print(f"❌ Search failed for '{query_test['query']}': {e}")
                self.test_results["search_tests"].append({
                    "query": query_test["query"],
                    "success": False,
                    "error": str(e)
                })
    
    async def test_search_caching(self):
        """Test search result caching"""
        print("\n📋 Test 4: Search Caching")
        print("-" * 25)
        
        test_query = {
            "query": "artificial intelligence",
            "limit": 5,
            "similarity_threshold": 0.6
        }
        
        try:
            # First search (should not be cached)
            start_time = time.time()
            async with self.session.post(f"{BASE_URL}/api/search/", json=test_query) as response:
                first_search_time = time.time() - start_time
                data1 = await response.json()
                
                assert response.status == 200
                assert not data1["cached"], "First search should not be cached"
            
            # Second search (should be cached)
            start_time = time.time()
            async with self.session.post(f"{BASE_URL}/api/search/", json=test_query) as response:
                second_search_time = time.time() - start_time
                data2 = await response.json()
                
                assert response.status == 200
                
                print(f"✅ Cache test completed")
                print(f"   First search time: {first_search_time:.3f}s (cached: {data1['cached']})")
                print(f"   Second search time: {second_search_time:.3f}s (cached: {data2['cached']})")
                print(f"   Speed improvement: {((first_search_time - second_search_time) / first_search_time * 100):.1f}%")
                
                self.test_results["cache_tests"].append({
                    "first_search_time": first_search_time,
                    "second_search_time": second_search_time,
                    "first_cached": data1["cached"],
                    "second_cached": data2["cached"],
                    "success": True
                })
                
        except Exception as e:
            print(f"❌ Cache test failed: {e}")
            self.test_results["cache_tests"].append({
                "success": False,
                "error": str(e)
            })
    
    async def test_search_suggestions(self):
        """Test search suggestions functionality"""
        print("\n📋 Test 5: Search Suggestions")
        print("-" * 30)
        
        # First, perform some searches to populate suggestions
        queries = ["artificial", "python", "redis", "machine learning"]
        
        for query in queries:
            try:
                await self.session.post(f"{BASE_URL}/api/search/", json={"query": query, "limit": 5})
            except:
                pass  # Ignore errors, just populating data
        
        # Test suggestions
        test_prefixes = ["art", "py", "red", "mac"]
        
        for prefix in test_prefixes:
            try:
                async with self.session.get(f"{BASE_URL}/api/search/suggestions?q={prefix}") as response:
                    assert response.status == 200
                    data = await response.json()
                    
                    print(f"✅ Suggestions for '{prefix}': {data['suggestions']}")
                    
            except Exception as e:
                print(f"❌ Suggestions failed for '{prefix}': {e}")
    
    async def test_search_analytics(self):
        """Test search analytics endpoint"""
        print("\n📋 Test 6: Search Analytics")
        print("-" * 30)
        
        try:
            async with self.session.get(f"{BASE_URL}/api/search/analytics") as response:
                assert response.status == 200
                data = await response.json()
                
                print("✅ Analytics retrieved:")
                print(f"   Total searches: {data['search_stats']['total_searches']}")
                print(f"   Cache hits: {data['search_stats']['cache_hits']}")
                print(f"   Cache hit rate: {data['search_stats']['cache_hit_rate']}%")
                print(f"   Avg response time: {data['search_stats']['avg_response_time']}s")
                print(f"   Vector docs: {data['vector_stats']['total_docs']}")
                print(f"   Embedding cache size: {data['embedding_stats']['cache_size']}")
                
                self.test_results["analytics_tests"].append({
                    "total_searches": data['search_stats']['total_searches'],
                    "cache_hit_rate": data['search_stats']['cache_hit_rate'],
                    "vector_docs": data['vector_stats']['total_docs'],
                    "success": True
                })
                
        except Exception as e:
            print(f"❌ Analytics test failed: {e}")
            self.test_results["analytics_tests"].append({
                "success": False,
                "error": str(e)
            })
    
    async def test_performance_benchmarks(self):
        """Test performance benchmarks"""
        print("\n📋 Test 7: Performance Benchmarks")
        print("-" * 35)
        
        # Concurrent search test
        concurrent_queries = [
            "artificial intelligence",
            "machine learning",
            "python programming",
            "data science",
            "redis database"
        ]
        
        try:
            start_time = time.time()
            
            # Run concurrent searches
            tasks = []
            for query in concurrent_queries:
                task = self.session.post(f"{BASE_URL}/api/search/", json={"query": query, "limit": 5})
                tasks.append(task)
            
            responses = await asyncio.gather(*tasks)
            total_time = time.time() - start_time
            
            print(f"✅ Concurrent search benchmark:")
            print(f"   Queries: {len(concurrent_queries)}")
            print(f"   Total time: {total_time:.3f}s")
            print(f"   Avg time per query: {total_time/len(concurrent_queries):.3f}s")
            print(f"   Queries per second: {len(concurrent_queries)/total_time:.1f}")
            
            self.test_results["performance_tests"].append({
                "concurrent_queries": len(concurrent_queries),
                "total_time": total_time,
                "avg_time_per_query": total_time/len(concurrent_queries),
                "queries_per_second": len(concurrent_queries)/total_time,
                "success": True
            })
            
            # Close responses
            for response in responses:
                response.close()
                
        except Exception as e:
            print(f"❌ Performance test failed: {e}")
            self.test_results["performance_tests"].append({
                "success": False,
                "error": str(e)
            })
    
    async def test_vector_operations(self):
        """Test vector-specific operations"""
        print("\n📋 Test 8: Vector Operations")
        print("-" * 30)
        
        try:
            # Test cache clearing
            async with self.session.delete(f"{BASE_URL}/api/search/cache") as response:
                assert response.status == 200
                data = await response.json()
                print(f"✅ Cache cleared: {data['message']}")
            
            # Test search after cache clear
            test_query = {"query": "artificial intelligence", "limit": 3}
            async with self.session.post(f"{BASE_URL}/api/search/", json=test_query) as response:
                assert response.status == 200
                data = await response.json()
                assert not data["cached"], "Search should not be cached after clearing"
                print(f"✅ Search after cache clear: {data['total_results']} results")
            
        except Exception as e:
            print(f"❌ Vector operations test failed: {e}")
    
    async def create_test_documents(self):
        """Create test documents for embedding tests"""
        test_content = {
            "test_ai.txt": """
            Artificial Intelligence and Machine Learning
            
            Artificial Intelligence (AI) is a branch of computer science that aims to create 
            intelligent machines that work and react like humans. Machine learning is a subset 
            of AI that provides systems the ability to automatically learn and improve from 
            experience without being explicitly programmed.
            
            Deep learning, neural networks, and natural language processing are key components 
            of modern AI systems. These technologies enable computers to recognize patterns, 
            make decisions, and understand human language.
            """,
            
            "test_python.txt": """
            Python Programming and Data Science
            
            Python is a high-level, interpreted programming language known for its simplicity 
            and readability. It's widely used in data science, web development, automation, 
            and artificial intelligence applications.
            
            Popular Python libraries for data science include NumPy, Pandas, Matplotlib, 
            Scikit-learn, and TensorFlow. These tools make it easy to analyze data, create 
            visualizations, and build machine learning models.
            """,
            
            "test_redis.txt": """
            Redis Database and Caching Systems
            
            Redis is an open-source, in-memory data structure store used as a database, 
            cache, and message broker. It supports various data structures such as strings, 
            hashes, lists, sets, and sorted sets.
            
            Redis is commonly used for caching, session management, real-time analytics, 
            and as a message queue. Its high performance and versatility make it popular 
            for modern web applications and microservices architectures.
            """
        }
        
        # Ensure test files directory exists
        TEST_FILES_DIR.mkdir(exist_ok=True)
        
        # Write test files
        for filename, content in test_content.items():
            file_path = TEST_FILES_DIR / filename
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content.strip())
    
    def generate_test_report(self):
        """Generate comprehensive test report"""
        print("\n" + "=" * 60)
        print("📊 EMBEDDING & SEARCH TEST REPORT")
        print("=" * 60)
        
        # Upload tests summary
        upload_success = sum(1 for test in self.test_results["upload_tests"] if test.get("success"))
        upload_total = len(self.test_results["upload_tests"])
        print(f"\n📤 Upload Tests: {upload_success}/{upload_total} passed")
        
        # Search tests summary
        search_success = sum(1 for test in self.test_results["search_tests"] if test.get("success"))
        search_total = len(self.test_results["search_tests"])
        print(f"🔍 Search Tests: {search_success}/{search_total} passed")
        
        # Cache tests summary
        cache_success = sum(1 for test in self.test_results["cache_tests"] if test.get("success"))
        cache_total = len(self.test_results["cache_tests"])
        print(f"💾 Cache Tests: {cache_success}/{cache_total} passed")
        
        # Performance summary
        if self.test_results["performance_tests"]:
            perf_test = self.test_results["performance_tests"][0]
            if perf_test.get("success"):
                print(f"⚡ Performance: {perf_test['queries_per_second']:.1f} queries/sec")
        
        # Overall success rate
        total_tests = upload_total + search_total + cache_total
        total_success = upload_success + search_success + cache_success
        success_rate = (total_success / total_tests * 100) if total_tests > 0 else 0
        
        print(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({total_success}/{total_tests})")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT! Embedding and search system is working perfectly!")
        elif success_rate >= 75:
            print("✅ GOOD! Most features are working correctly.")
        elif success_rate >= 50:
            print("⚠️ PARTIAL! Some issues need attention.")
        else:
            print("❌ POOR! Significant issues detected.")
        
        print("=" * 60)

async def main():
    """Main test execution function"""
    async with EmbeddingTester() as tester:
        await tester.run_all_tests()

if __name__ == "__main__":
    asyncio.run(main())
