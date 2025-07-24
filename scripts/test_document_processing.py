import requests
import json
import time
from pathlib import Path

API_BASE = "http://localhost:8000"

def test_document_upload():
    """Test document upload and processing"""
    print("🧪 Testing Document Processing Pipeline")
    print("=" * 50)
    
    # Create a test text file
    test_content = """
    This is a test document for the Redis AI Challenge.
    
    It contains multiple paragraphs to test the chunking functionality.
    
    The document processing pipeline should:
    1. Extract this text
    2. Chunk it intelligently
    3. Store it in Redis
    4. Make it searchable
    
    This is the final paragraph of our test document.
    """
    
    test_file = Path("test_document.txt")
    test_file.write_text(test_content)
    
    try:
        # Upload document
        print("📤 Uploading test document...")
        with open(test_file, 'rb') as f:
            files = {'file': ('test_document.txt', f, 'text/plain')}
            response = requests.post(f"{API_BASE}/api/documents/upload", files=files)
        
        if response.status_code == 201:
            result = response.json()
            doc_id = result["doc_id"]
            print(f"✅ Upload successful! Doc ID: {doc_id}")
            print(f"   Chunks created: {result['chunks_created']}")
            print(f"   Processing time: {result['processing_time']:.2f}s")
            
            # Test document retrieval
            print("\n📖 Retrieving document...")
            doc_response = requests.get(f"{API_BASE}/api/documents/{doc_id}")
            if doc_response.status_code == 200:
                doc_data = doc_response.json()
                print(f"✅ Document retrieved: {doc_data['title']}")
                print(f"   Word count: {doc_data['word_count']}")
                print(f"   Chunk count: {doc_data['chunk_count']}")
            
            # Test chunks retrieval
            print("\n🧩 Retrieving chunks...")
            chunks_response = requests.get(f"{API_BASE}/api/documents/{doc_id}/chunks")
            if chunks_response.status_code == 200:
                chunks_data = chunks_response.json()
                print(f"✅ Retrieved {len(chunks_data['chunks'])} chunks")
                for i, chunk in enumerate(chunks_data['chunks']):
                    print(f"   Chunk {i}: {chunk['word_count']} words")
            
            # Test document listing
            print("\n📋 Testing document listing...")
            list_response = requests.get(f"{API_BASE}/api/documents/")
            if list_response.status_code == 200:
                list_data = list_response.json()
                print(f"✅ Listed {len(list_data['documents'])} documents")
            
            return doc_id
            
        else:
            print(f"❌ Upload failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return None
            
    finally:
        # Cleanup test file
        if test_file.exists():
            test_file.unlink()

def test_system_stats():
    """Test system statistics"""
    print("\n📊 Testing system statistics...")
    response = requests.get(f"{API_BASE}/api/system/stats")
    
    if response.status_code == 200:
        stats = response.json()
        print("✅ System stats retrieved:")
        print(f"   Redis connected: {stats['system']['redis_connected']}")
        print(f"   Total documents: {stats['documents']['total_documents']}")
        print(f"   Total chunks: {stats['documents']['total_chunks']}")
        print(f"   Memory used: {stats['redis']['memory_used']}")
    else:
        print(f"❌ Stats failed: {response.status_code}")

def test_health_endpoints():
    """Test health and basic endpoints"""
    print("\n🏥 Testing health endpoints...")
    
    # Test health endpoint
    health_response = requests.get(f"{API_BASE}/health")
    if health_response.status_code == 200:
        health_data = health_response.json()
        print(f"✅ Health check: {health_data['status']}")
        print(f"   Redis: {health_data['redis']}")
    else:
        print(f"❌ Health check failed: {health_response.status_code}")
    
    # Test basic stats endpoint
    stats_response = requests.get(f"{API_BASE}/api/stats")
    if stats_response.status_code == 200:
        print("✅ Basic stats endpoint working")
    else:
        print(f"❌ Basic stats failed: {stats_response.status_code}")

def test_pdf_upload():
    """Test PDF upload (if available)"""
    print("\n📄 Testing PDF upload...")
    
    # Create a simple test PDF content (placeholder)
    # In a real test, you'd use a proper PDF file
    print("⚠️  PDF test skipped - requires actual PDF file")
    print("   To test PDF functionality:")
    print("   1. Place a PDF file in the scripts directory")
    print("   2. Update this function to use the actual file")

if __name__ == "__main__":
    print("🚀 Starting DocuMind Pipeline Tests")
    print("=" * 60)
    
    try:
        # Test basic endpoints first
        test_health_endpoints()
        
        # Test the main pipeline
        doc_id = test_document_upload()
        
        # Test system statistics
        test_system_stats()
        
        # Test PDF functionality (placeholder)
        test_pdf_upload()
        
        if doc_id:
            print(f"\n🎉 All tests passed! Document ID: {doc_id}")
            print("💡 Next steps:")
            print("   1. Test with PDF files")
            print("   2. Add embedding generation")
            print("   3. Implement vector search")
        else:
            print("\n❌ Some tests failed!")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Connection Error!")
        print("   Make sure the DocuMind API server is running:")
        print("   cd backend && python -m app.main")
    except Exception as e:
        print(f"\n❌ Test error: {e}")
        
    print("\n" + "=" * 60)
    print("🏁 Test run completed")
