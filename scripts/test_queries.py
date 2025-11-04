"""
Test queries to verify document ingestion and RAG functionality.

Usage:
    python scripts/test_queries.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant

load_dotenv()

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "tax_memo_production"


def test_queries():
    """Test various queries to verify document retrieval."""
    
    if not QDRANT_HOST or not QDRANT_API_KEY:
        print("❌ Error: QDRANT_HOST and QDRANT_API_KEY must be set in .env file")
        sys.exit(1)
    
    print("🔍 Testing Qdrant queries...\n")
    
    # Initialize embeddings and Qdrant
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    qdrant = Qdrant.from_existing_collection(
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        url=QDRANT_HOST,
        api_key=QDRANT_API_KEY,
        prefer_grpc=True,
    )
    
    # Test queries
    test_cases = [
        {
            "name": "Corporate Income Tax in Netherlands",
            "query": "Corporate income tax rate in Netherlands",
            "filter": {"country": "netherlands", "topic": "corporate_income_tax"},
        },
        {
            "name": "VAT in Netherlands",
            "query": "VAT registration requirements in Netherlands",
            "filter": {"country": "netherlands", "topic": "vat"},
        },
        {
            "name": "Employment Law in Netherlands",
            "query": "Employment law requirements for hiring employees in Netherlands",
            "filter": {"country": "netherlands", "topic": "employment_law"},
        },
        {
            "name": "Corporate Law in Germany",
            "query": "Corporate law entity setup in Germany",
            "filter": {"country": "germany", "topic": "corporate_law"},
        },
        {
            "name": "General Query (No Filter)",
            "query": "Tax requirements for setting up a business",
            "filter": None,
        },
    ]
    
    for i, test in enumerate(test_cases, 1):
        print("=" * 70)
        print(f"Test {i}: {test['name']}")
        print("=" * 70)
        print(f"Query: {test['query']}")
        if test['filter']:
            print(f"Filter: {test['filter']}")
        print()
        
        try:
            if test['filter']:
                results = qdrant.similarity_search(
                    query=test['query'],
                    filter=test['filter'],
                    k=3,
                )
            else:
                results = qdrant.similarity_search(
                    query=test['query'],
                    k=3,
                )
            
            print(f"✅ Found {len(results)} results\n")
            
            for j, doc in enumerate(results, 1):
                print(f"Result {j}:")
                print(f"  Content: {doc.page_content[:200]}...")
                print(f"  Metadata: {doc.metadata}")
                print()
                
        except Exception as e:
            print(f"❌ Error: {e}\n")
        
        print()
    
    print("=" * 70)
    print("✅ Query testing complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_queries()

