"""
Load demo data for DocuMind testing
"""
import sys
import os
import logging
import asyncio
from typing import List, Dict, Any
import uuid
from datetime import datetime

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.database.redis_client import redis_client
from app.database.models import DocumentMetadata, DocumentContent, DocumentStatus, DocumentType
from app.services.document_processor import DocumentProcessor
from app.services.search_service import SearchService

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Sample document contents
SAMPLE_DOCUMENTS = [
    {
        "filename": "machine_learning_intro.txt",
        "content": """Machine Learning Introduction

Machine learning is a subset of artificial intelligence (AI) that provides systems the ability to automatically learn and improve from experience without being explicitly programmed. Machine learning focuses on the development of computer programs that can access data and use it to learn for themselves.

The process of learning begins with observations or data, such as examples, direct experience, or instruction, in order to look for patterns in data and make better decisions in the future based on the examples that we provide. The primary aim is to allow the computers to learn automatically without human intervention or assistance and adjust actions accordingly.

Types of Machine Learning:
1. Supervised Learning - Uses labeled training data
2. Unsupervised Learning - Finds patterns in unlabeled data  
3. Reinforcement Learning - Learns through interaction with environment

Applications include image recognition, natural language processing, recommendation systems, and autonomous vehicles.""",
        "file_type": "txt"
    },
    {
        "filename": "python_programming_guide.txt", 
        "content": """Python Programming Guide

Python is a high-level, interpreted programming language with dynamic semantics. Its high-level built-in data structures, combined with dynamic typing and dynamic binding, make it very attractive for Rapid Application Development, as well as for use as a scripting or glue language to connect existing components together.

Key Features:
- Easy to learn and use
- Interpreted language
- Object-oriented programming support
- Extensive standard library
- Cross-platform compatibility

Popular Python Libraries:
- NumPy: Numerical computing
- Pandas: Data manipulation and analysis
- Matplotlib: Data visualization
- Scikit-learn: Machine learning
- Django/Flask: Web development
- TensorFlow/PyTorch: Deep learning

Python is widely used in web development, data science, artificial intelligence, automation, and scientific computing.""",
        "file_type": "txt"
    },
    {
        "filename": "database_design_principles.txt",
        "content": """Database Design Principles

Database design is the process of producing a detailed data model of a database. This data model contains all the needed logical and physical design choices and physical storage parameters needed to generate a design in a data definition language.

Key Principles:

1. Normalization
   - Eliminate redundant data
   - Ensure data dependencies make sense
   - Reduce storage space and improve data integrity

2. Entity-Relationship Modeling
   - Identify entities (tables)
   - Define relationships between entities
   - Establish primary and foreign keys

3. Indexing Strategy
   - Create indexes on frequently queried columns
   - Balance query performance with storage overhead
   - Consider composite indexes for multi-column queries

4. Data Types and Constraints
   - Choose appropriate data types
   - Implement referential integrity
   - Use check constraints for data validation

5. Performance Considerations
   - Denormalization when appropriate
   - Partitioning for large datasets
   - Query optimization techniques

Modern databases support ACID properties (Atomicity, Consistency, Isolation, Durability) to ensure reliable transaction processing.""",
        "file_type": "txt"
    },
    {
        "filename": "artificial_intelligence_overview.txt",
        "content": """Artificial Intelligence Overview

Artificial Intelligence (AI) refers to the simulation of human intelligence in machines that are programmed to think and learn like humans. The term may also be applied to any machine that exhibits traits associated with a human mind such as learning and problem-solving.

AI Categories:

1. Narrow AI (Weak AI)
   - Designed for specific tasks
   - Current state of most AI systems
   - Examples: voice assistants, recommendation systems

2. General AI (Strong AI)
   - Human-level intelligence across all domains
   - Theoretical concept, not yet achieved
   - Would match human cognitive abilities

3. Superintelligence
   - Surpasses human intelligence
   - Hypothetical future development
   - Subject of ongoing research and debate

AI Techniques:
- Machine Learning
- Deep Learning
- Natural Language Processing
- Computer Vision
- Robotics
- Expert Systems

Applications span healthcare, finance, transportation, entertainment, and many other industries. AI continues to evolve rapidly with advances in computing power and algorithmic improvements.""",
        "file_type": "txt"
    },
    {
        "filename": "data_science_methodology.txt",
        "content": """Data Science Methodology

Data science is an interdisciplinary field that uses scientific methods, processes, algorithms, and systems to extract knowledge and insights from structured and unstructured data.

The Data Science Process:

1. Problem Definition
   - Understand business objectives
   - Define success metrics
   - Identify data requirements

2. Data Collection
   - Gather relevant datasets
   - Ensure data quality and completeness
   - Consider data privacy and ethics

3. Data Exploration and Cleaning
   - Exploratory data analysis (EDA)
   - Handle missing values
   - Remove outliers and inconsistencies

4. Feature Engineering
   - Select relevant features
   - Create new features from existing data
   - Transform variables as needed

5. Model Development
   - Choose appropriate algorithms
   - Train and validate models
   - Tune hyperparameters

6. Model Evaluation
   - Assess model performance
   - Cross-validation techniques
   - Compare different approaches

7. Deployment and Monitoring
   - Implement models in production
   - Monitor performance over time
   - Update models as needed

Tools commonly used include Python, R, SQL, Jupyter notebooks, and various machine learning libraries.""",
        "file_type": "txt"
    }
]

class DemoDataLoader:
    """Load demo data into DocuMind"""
    
    def __init__(self):
        self.doc_processor = DocumentProcessor()
        self.search_service = SearchService()
        self.loaded_documents = []
    
    async def load_sample_documents(self) -> List[str]:
        """Load sample documents into the system"""
        try:
            logger.info(f"Loading {len(SAMPLE_DOCUMENTS)} sample documents...")
            
            for doc_data in SAMPLE_DOCUMENTS:
                try:
                    document_id = await self._create_document(doc_data)
                    if document_id:
                        self.loaded_documents.append(document_id)
                        logger.info(f"✅ Loaded: {doc_data['filename']} (ID: {document_id})")
                    else:
                        logger.error(f"❌ Failed to load: {doc_data['filename']}")
                        
                except Exception as e:
                    logger.error(f"❌ Error loading {doc_data['filename']}: {e}")
                    continue
            
            logger.info(f"Successfully loaded {len(self.loaded_documents)} documents")
            return self.loaded_documents
            
        except Exception as e:
            logger.error(f"Demo data loading failed: {e}")
            return []
    
    async def _create_document(self, doc_data: Dict[str, Any]) -> str:
        """Create a single document"""
        try:
            # Generate document ID
            document_id = str(uuid.uuid4())
            
            # Create metadata
            content_bytes = doc_data["content"].encode('utf-8')
            metadata = DocumentMetadata(
                id=document_id,
                filename=doc_data["filename"],
                file_type=DocumentType(doc_data["file_type"]),
                file_size=len(content_bytes),
                processing_status=DocumentStatus.COMPLETED,
                word_count=len(doc_data["content"].split()),
                language="en"
            )
            
            # Store metadata
            redis_client.set_json(f"doc:meta:{document_id}", metadata.model_dump(mode='json'))
            
            # Create and store content
            doc_content = DocumentContent(
                document_id=document_id,
                raw_text=doc_data["content"],
                processed_timestamp=datetime.utcnow()
            )
            
            redis_client.set_json(f"doc:content:{document_id}", doc_content.model_dump(mode='json'))
            
            # Chunk and index the document
            from app.services.text_chunker import text_chunker
            chunks = await text_chunker.chunk_text(doc_data["content"], document_id, {"filename": doc_data["filename"]})
            await self.search_service.index_document_chunks(document_id, chunks)
            
            # Update counters
            redis_client.increment_counter("stats:total_documents")
            
            return document_id
            
        except Exception as e:
            logger.error(f"Document creation failed: {e}")
            return None
    
    def create_sample_searches(self) -> bool:
        """Create sample search history and popular queries"""
        try:
            # Sample search queries
            sample_queries = [
                "machine learning algorithms",
                "python data science",
                "database normalization",
                "artificial intelligence applications",
                "supervised learning examples",
                "data visualization techniques",
                "neural networks",
                "big data processing",
                "statistical analysis",
                "programming best practices"
            ]
            
            # Add to popular queries with scores
            for i, query in enumerate(sample_queries):
                score = len(sample_queries) - i  # Higher score for earlier queries
                redis_client.client.zadd("stats:popular_queries", {query: score})
            
            # Add to recent searches
            for query in sample_queries[:5]:  # Add first 5 to recent searches
                redis_client.client.lpush("stats:recent_searches", query)
            
            # Trim recent searches to reasonable size
            redis_client.client.ltrim("stats:recent_searches", 0, 19)  # Keep last 20
            
            logger.info("✅ Sample search data created")
            return True
            
        except Exception as e:
            logger.error(f"Sample search creation failed: {e}")
            return False
    
    def create_sample_analytics(self) -> bool:
        """Create sample analytics data"""
        try:
            # Set some sample counters
            redis_client.client.set("stats:total_searches", 150)
            redis_client.client.set("stats:cache_hits", 45)
            
            # Add sample response times
            sample_times = [0.123, 0.089, 0.156, 0.098, 0.134, 0.087, 0.145, 0.092, 0.167, 0.103]
            for time_val in sample_times:
                redis_client.client.lpush("stats:response_times", time_val)
            
            logger.info("✅ Sample analytics data created")
            return True
            
        except Exception as e:
            logger.error(f"Sample analytics creation failed: {e}")
            return False
    
    def get_load_summary(self) -> Dict[str, Any]:
        """Get summary of loaded demo data"""
        try:
            return {
                "documents_loaded": len(self.loaded_documents),
                "document_ids": self.loaded_documents,
                "total_documents_in_system": int(redis_client.client.get("stats:total_documents") or 0),
                "popular_queries_count": redis_client.client.zcard("stats:popular_queries"),
                "recent_searches_count": redis_client.client.llen("stats:recent_searches"),
                "index_stats": self.search_service.get_index_stats(),
                "timestamp": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return {"error": str(e)}

async def main():
    """Main demo data loading function"""
    print("🚀 DocuMind Demo Data Loader")
    print("=" * 50)
    
    # Test Redis connection
    print("\n1. Testing Redis connection...")
    if not redis_client.health_check():
        print("❌ Cannot connect to Redis. Please check your configuration.")
        sys.exit(1)
    print("✅ Redis connection successful")
    
    # Initialize loader
    loader = DemoDataLoader()
    
    # Load sample documents
    print("\n2. Loading sample documents...")
    document_ids = await loader.load_sample_documents()
    
    if not document_ids:
        print("❌ No documents were loaded successfully")
        sys.exit(1)
    
    # Create sample search data
    print("\n3. Creating sample search data...")
    if loader.create_sample_searches():
        print("✅ Sample search data created")
    else:
        print("⚠️  Warning: Sample search data creation failed")
    
    # Create sample analytics
    print("\n4. Creating sample analytics data...")
    if loader.create_sample_analytics():
        print("✅ Sample analytics data created")
    else:
        print("⚠️  Warning: Sample analytics creation failed")
    
    # Show summary
    print("\n📊 Demo Data Load Summary:")
    print("-" * 30)
    summary = loader.get_load_summary()
    
    for key, value in summary.items():
        if key == "document_ids":
            print(f"Document IDs:")
            for doc_id in value:
                print(f"  - {doc_id}")
        elif key == "index_stats":
            print(f"Search Index Stats:")
            for stat_key, stat_value in value.items():
                print(f"  {stat_key}: {stat_value}")
        else:
            print(f"{key}: {value}")
    
    print("\n🎉 Demo data loading completed!")
    print("\nYou can now:")
    print("1. Start the API server: python -m app.main")
    print("2. Test search functionality with the loaded documents")
    print("3. View analytics at: http://localhost:8000/api/analytics")
    print("4. Try searching for terms like 'machine learning', 'python', or 'database'")

if __name__ == "__main__":
    asyncio.run(main())
