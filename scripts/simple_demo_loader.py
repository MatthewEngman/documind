import sys
import os
import uuid
from datetime import datetime
import logging

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))
from app.database.redis_client import redis_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SAMPLE_DOCS = [
    {
        "filename": "machine_learning_intro.txt",
        "content": """Machine Learning Introduction

Machine learning is a subset of artificial intelligence (AI) that provides systems the ability to automatically learn and improve from experience without being explicitly programmed. Machine learning focuses on the development of computer programs that can access data and use it to learn for themselves.

The process of learning begins with observations or data, such as examples, direct experience, or instruction, in order to look for patterns in data and make better decisions in the future based on the examples that we provide. The primary aim is to allow the computers to learn automatically without human intervention or assistance and adjust actions accordingly.

Types of Machine Learning:
1. Supervised Learning - Uses labeled training data
2. Unsupervised Learning - Finds patterns in unlabeled data  
3. Reinforcement Learning - Learns through interaction with environment

Applications include image recognition, natural language processing, recommendation systems, and autonomous vehicles."""
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

Python is widely used in web development, data science, artificial intelligence, automation, and scientific computing."""
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

Modern databases support ACID properties (Atomicity, Consistency, Isolation, Durability) to ensure reliable transaction processing."""
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

Applications span healthcare, finance, transportation, entertainment, and many other industries. AI continues to evolve rapidly with advances in computing power and algorithmic improvements."""
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

Tools commonly used include Python, R, SQL, Jupyter notebooks, and various machine learning libraries."""
    }
]

def load_demo_documents():
    """Load demo documents directly into Redis in API-expected format"""
    print("🚀 Simple Demo Data Loader")
    print("=" * 50)
    
    if not redis_client.health_check():
        print("❌ Cannot connect to Redis. Please check your configuration.")
        return False
    
    print("✅ Redis connection successful")
    print(f"\nLoading {len(SAMPLE_DOCS)} sample documents...")
    
    loaded_count = 0
    
    for doc_data in SAMPLE_DOCS:
        try:
            doc_id = str(uuid.uuid4())
            
            doc_format = {
                "id": doc_id,
                "filename": doc_data["filename"],
                "title": doc_data["filename"].replace('.txt', '').replace('_', ' ').title(),
                "file_type": "txt",
                "file_size": len(doc_data["content"].encode('utf-8')),
                "word_count": len(doc_data["content"].split()),
                "language": "en",
                "created_at": datetime.utcnow().isoformat(),
                "processing_status": "completed"
            }
            
            redis_client.set_json(f"doc:{doc_id}", doc_format)
            redis_client.set_json(f"doc:content:{doc_id}", {
                "document_id": doc_id,
                "raw_text": doc_data["content"],
                "processed_timestamp": datetime.utcnow().isoformat()
            })
            
            if hasattr(redis_client.client, 'sadd'):
                redis_client.client.sadd("doc:index", doc_id)
            else:
                if not hasattr(redis_client.client, '_sets'):
                    redis_client.client._sets = {}
                if "doc:index" not in redis_client.client._sets:
                    redis_client.client._sets["doc:index"] = set()
                redis_client.client._sets["doc:index"].add(doc_id)
            
            redis_client.increment_counter("stats:total_documents")
            loaded_count += 1
            
            print(f"✅ Loaded: {doc_data['filename']} (ID: {doc_id})")
            
        except Exception as e:
            print(f"❌ Error loading {doc_data['filename']}: {e}")
            continue
    
    print(f"\n🎉 Successfully loaded {loaded_count} documents!")
    print("\nYou can now:")
    print("1. Start the API server: python -m app.main")
    print("2. Test document access: curl http://localhost:8000/api/documents")
    print("3. View stats: curl http://localhost:8000/api/stats")
    
    return loaded_count > 0

if __name__ == "__main__":
    load_demo_documents()
