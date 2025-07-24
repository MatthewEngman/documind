#!/usr/bin/env python3
"""
Benchmark script for DocuMind performance testing
"""
import sys
import os
import logging
import asyncio
import time
import statistics
from typing import List, Dict, Any
import requests
import json

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database.redis_client import redis_client
from app.services.embedding_service import EmbeddingService
from app.services.search_service import SearchService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DocuMindBenchmark:
    """Benchmark suite for DocuMind performance"""
    
    def __init__(self, api_base_url: str = "http://localhost:8000"):
        self.api_base_url = api_base_url
        self.embedding_service = EmbeddingService()
        self.search_service = SearchService()
        self.results = {}
    
    def test_api_connectivity(self) -> bool:
        """Test if API is accessible"""
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"API connectivity test failed: {e}")
            return False
    
    def benchmark_redis_operations(self, iterations: int = 1000) -> Dict[str, Any]:
        """Benchmark basic Redis operations"""
        logger.info(f"Benchmarking Redis operations ({iterations} iterations)...")
        
        try:
            # Test SET operations
            set_times = []
            for i in range(iterations):
                start_time = time.time()
                redis_client.client.set(f"benchmark:set:{i}", f"value_{i}")
                set_times.append(time.time() - start_time)
            
            # Test GET operations
            get_times = []
            for i in range(iterations):
                start_time = time.time()
                redis_client.client.get(f"benchmark:set:{i}")
                get_times.append(time.time() - start_time)
            
            # Test JSON operations
            json_set_times = []
            test_data = {"key": "value", "number": 42, "list": [1, 2, 3]}
            for i in range(min(iterations, 100)):  # Fewer iterations for JSON
                start_time = time.time()
                redis_client.set_json(f"benchmark:json:{i}", test_data)
                json_set_times.append(time.time() - start_time)
            
            json_get_times = []
            for i in range(min(iterations, 100)):
                start_time = time.time()
                redis_client.get_json(f"benchmark:json:{i}")
                json_get_times.append(time.time() - start_time)
            
            # Cleanup
            keys_to_delete = redis_client.client.keys("benchmark:*")
            if keys_to_delete:
                redis_client.client.delete(*keys_to_delete)
            
            return {
                "set_operations": {
                    "iterations": len(set_times),
                    "avg_time": statistics.mean(set_times),
                    "min_time": min(set_times),
                    "max_time": max(set_times),
                    "ops_per_second": 1 / statistics.mean(set_times)
                },
                "get_operations": {
                    "iterations": len(get_times),
                    "avg_time": statistics.mean(get_times),
                    "min_time": min(get_times),
                    "max_time": max(get_times),
                    "ops_per_second": 1 / statistics.mean(get_times)
                },
                "json_set_operations": {
                    "iterations": len(json_set_times),
                    "avg_time": statistics.mean(json_set_times),
                    "ops_per_second": 1 / statistics.mean(json_set_times)
                },
                "json_get_operations": {
                    "iterations": len(json_get_times),
                    "avg_time": statistics.mean(json_get_times),
                    "ops_per_second": 1 / statistics.mean(json_get_times)
                }
            }
            
        except Exception as e:
            logger.error(f"Redis benchmark failed: {e}")
            return {"error": str(e)}
    
    async def benchmark_embedding_generation(self, iterations: int = 50) -> Dict[str, Any]:
        """Benchmark embedding generation performance"""
        logger.info(f"Benchmarking embedding generation ({iterations} iterations)...")
        
        try:
            test_texts = [
                "Machine learning is a subset of artificial intelligence.",
                "Python is a popular programming language for data science.",
                "Database design requires careful consideration of relationships.",
                "Natural language processing enables computers to understand text.",
                "Deep learning uses neural networks with multiple layers."
            ]
            
            # Single embedding generation
            single_times = []
            for i in range(iterations):
                text = test_texts[i % len(test_texts)]
                start_time = time.time()
                await self.embedding_service.generate_embedding(text)
                single_times.append(time.time() - start_time)
            
            # Batch embedding generation
            batch_sizes = [5, 10, 20]
            batch_results = {}
            
            for batch_size in batch_sizes:
                batch_texts = test_texts * (batch_size // len(test_texts) + 1)
                batch_texts = batch_texts[:batch_size]
                
                batch_times = []
                for _ in range(min(10, iterations // 5)):  # Fewer iterations for batches
                    start_time = time.time()
                    await self.embedding_service.generate_embeddings_batch(batch_texts)
                    batch_times.append(time.time() - start_time)
                
                if batch_times:
                    batch_results[f"batch_size_{batch_size}"] = {
                        "avg_time": statistics.mean(batch_times),
                        "avg_time_per_text": statistics.mean(batch_times) / batch_size,
                        "texts_per_second": batch_size / statistics.mean(batch_times)
                    }
            
            return {
                "single_embeddings": {
                    "iterations": len(single_times),
                    "avg_time": statistics.mean(single_times),
                    "min_time": min(single_times),
                    "max_time": max(single_times),
                    "embeddings_per_second": 1 / statistics.mean(single_times)
                },
                "batch_embeddings": batch_results,
                "model_info": self.embedding_service.get_model_info()
            }
            
        except Exception as e:
            logger.error(f"Embedding benchmark failed: {e}")
            return {"error": str(e)}
    
    def benchmark_api_endpoints(self, iterations: int = 100) -> Dict[str, Any]:
        """Benchmark API endpoint performance"""
        logger.info(f"Benchmarking API endpoints ({iterations} iterations)...")
        
        try:
            endpoints = [
                "/health",
                "/api/stats",
                "/api/test"
            ]
            
            results = {}
            
            for endpoint in endpoints:
                endpoint_times = []
                successful_requests = 0
                
                for _ in range(iterations):
                    try:
                        start_time = time.time()
                        response = requests.get(f"{self.api_base_url}{endpoint}", timeout=10)
                        request_time = time.time() - start_time
                        
                        if response.status_code == 200:
                            endpoint_times.append(request_time)
                            successful_requests += 1
                            
                    except Exception as e:
                        logger.warning(f"Request to {endpoint} failed: {e}")
                        continue
                
                if endpoint_times:
                    results[endpoint] = {
                        "successful_requests": successful_requests,
                        "success_rate": successful_requests / iterations,
                        "avg_response_time": statistics.mean(endpoint_times),
                        "min_response_time": min(endpoint_times),
                        "max_response_time": max(endpoint_times),
                        "requests_per_second": 1 / statistics.mean(endpoint_times)
                    }
                else:
                    results[endpoint] = {
                        "successful_requests": 0,
                        "success_rate": 0,
                        "error": "No successful requests"
                    }
            
            return results
            
        except Exception as e:
            logger.error(f"API benchmark failed: {e}")
            return {"error": str(e)}
    
    async def benchmark_search_operations(self, iterations: int = 20) -> Dict[str, Any]:
        """Benchmark search performance"""
        logger.info(f"Benchmarking search operations ({iterations} iterations)...")
        
        try:
            # Test queries
            test_queries = [
                "machine learning algorithms",
                "python programming",
                "database design",
                "artificial intelligence",
                "data science methods"
            ]
            
            search_times = []
            successful_searches = 0
            
            for i in range(iterations):
                query = test_queries[i % len(test_queries)]
                
                try:
                    start_time = time.time()
                    
                    # Generate query embedding
                    query_embedding = await self.embedding_service.generate_embedding(query)
                    
                    # Perform search
                    results = await self.search_service.search_similar_documents(
                        query_embedding=query_embedding,
                        limit=10,
                        threshold=0.5
                    )
                    
                    search_time = time.time() - start_time
                    search_times.append(search_time)
                    successful_searches += 1
                    
                except Exception as e:
                    logger.warning(f"Search failed for query '{query}': {e}")
                    continue
            
            if search_times:
                return {
                    "successful_searches": successful_searches,
                    "success_rate": successful_searches / iterations,
                    "avg_search_time": statistics.mean(search_times),
                    "min_search_time": min(search_times),
                    "max_search_time": max(search_times),
                    "searches_per_second": 1 / statistics.mean(search_times),
                    "index_stats": self.search_service.get_index_stats()
                }
            else:
                return {
                    "successful_searches": 0,
                    "success_rate": 0,
                    "error": "No successful searches"
                }
                
        except Exception as e:
            logger.error(f"Search benchmark failed: {e}")
            return {"error": str(e)}
    
    def benchmark_memory_usage(self) -> Dict[str, Any]:
        """Benchmark memory usage"""
        logger.info("Analyzing memory usage...")
        
        try:
            redis_info = redis_client.client.info("memory")
            
            return {
                "redis_memory": {
                    "used_memory": redis_info.get("used_memory", 0),
                    "used_memory_human": redis_info.get("used_memory_human", "0B"),
                    "used_memory_peak": redis_info.get("used_memory_peak", 0),
                    "used_memory_peak_human": redis_info.get("used_memory_peak_human", "0B"),
                    "memory_fragmentation_ratio": redis_info.get("mem_fragmentation_ratio", 0)
                },
                "key_statistics": {
                    "total_keys": redis_client.client.dbsize(),
                    "document_keys": len(redis_client.client.keys("doc:*")),
                    "cache_keys": len(redis_client.client.keys("cache:*")),
                    "stats_keys": len(redis_client.client.keys("stats:*"))
                }
            }
            
        except Exception as e:
            logger.error(f"Memory usage benchmark failed: {e}")
            return {"error": str(e)}
    
    async def run_full_benchmark(self) -> Dict[str, Any]:
        """Run complete benchmark suite"""
        logger.info("🚀 Starting DocuMind Performance Benchmark")
        
        # Check API connectivity
        if not self.test_api_connectivity():
            return {"error": "API is not accessible"}
        
        benchmark_results = {
            "timestamp": time.time(),
            "system_info": {
                "api_base_url": self.api_base_url,
                "redis_connected": redis_client.health_check()
            }
        }
        
        # Run benchmarks
        benchmark_results["redis_operations"] = self.benchmark_redis_operations(1000)
        benchmark_results["embedding_generation"] = await self.benchmark_embedding_generation(50)
        benchmark_results["api_endpoints"] = self.benchmark_api_endpoints(100)
        benchmark_results["search_operations"] = await self.benchmark_search_operations(20)
        benchmark_results["memory_usage"] = self.benchmark_memory_usage()
        
        return benchmark_results
    
    def print_benchmark_results(self, results: Dict[str, Any]):
        """Print formatted benchmark results"""
        print("\n📊 DocuMind Performance Benchmark Results")
        print("=" * 60)
        
        # System info
        if "system_info" in results:
            print(f"\n🔧 System Information:")
            for key, value in results["system_info"].items():
                print(f"  {key}: {value}")
        
        # Redis operations
        if "redis_operations" in results and "error" not in results["redis_operations"]:
            print(f"\n⚡ Redis Operations:")
            redis_ops = results["redis_operations"]
            for op_type, metrics in redis_ops.items():
                if isinstance(metrics, dict) and "ops_per_second" in metrics:
                    print(f"  {op_type}: {metrics['ops_per_second']:.2f} ops/sec (avg: {metrics['avg_time']*1000:.2f}ms)")
        
        # Embedding generation
        if "embedding_generation" in results and "error" not in results["embedding_generation"]:
            print(f"\n🧠 Embedding Generation:")
            embed_results = results["embedding_generation"]
            if "single_embeddings" in embed_results:
                single = embed_results["single_embeddings"]
                print(f"  Single embeddings: {single['embeddings_per_second']:.2f} embeddings/sec")
            
            if "batch_embeddings" in embed_results:
                print(f"  Batch embeddings:")
                for batch_type, metrics in embed_results["batch_embeddings"].items():
                    print(f"    {batch_type}: {metrics['texts_per_second']:.2f} texts/sec")
        
        # API endpoints
        if "api_endpoints" in results and "error" not in results["api_endpoints"]:
            print(f"\n🌐 API Endpoints:")
            for endpoint, metrics in results["api_endpoints"].items():
                if "requests_per_second" in metrics:
                    print(f"  {endpoint}: {metrics['requests_per_second']:.2f} req/sec (success: {metrics['success_rate']*100:.1f}%)")
        
        # Search operations
        if "search_operations" in results and "error" not in results["search_operations"]:
            print(f"\n🔍 Search Operations:")
            search_results = results["search_operations"]
            if "searches_per_second" in search_results:
                print(f"  Search performance: {search_results['searches_per_second']:.2f} searches/sec")
                print(f"  Average search time: {search_results['avg_search_time']*1000:.2f}ms")
                print(f"  Success rate: {search_results['success_rate']*100:.1f}%")
        
        # Memory usage
        if "memory_usage" in results and "error" not in results["memory_usage"]:
            print(f"\n💾 Memory Usage:")
            memory = results["memory_usage"]
            if "redis_memory" in memory:
                redis_mem = memory["redis_memory"]
                print(f"  Redis memory used: {redis_mem.get('used_memory_human', 'N/A')}")
                print(f"  Memory fragmentation: {redis_mem.get('memory_fragmentation_ratio', 'N/A')}")
            
            if "key_statistics" in memory:
                key_stats = memory["key_statistics"]
                print(f"  Total keys: {key_stats.get('total_keys', 0)}")
                print(f"  Document keys: {key_stats.get('document_keys', 0)}")

async def main():
    """Main benchmark function"""
    print("🚀 DocuMind Performance Benchmark")
    print("=" * 50)
    
    # Initialize benchmark
    benchmark = DocuMindBenchmark()
    
    # Run benchmarks
    print("\nRunning benchmark suite...")
    results = await benchmark.run_full_benchmark()
    
    # Print results
    benchmark.print_benchmark_results(results)
    
    # Save results to file
    try:
        results_file = "benchmark_results.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n💾 Results saved to: {results_file}")
    except Exception as e:
        logger.warning(f"Failed to save results: {e}")
    
    print("\n🎉 Benchmark completed!")

if __name__ == "__main__":
    asyncio.run(main())
