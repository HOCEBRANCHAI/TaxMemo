"""
Script to ingest tax and legal documents into Qdrant vector database.
Run this once to populate your knowledge base.

Usage:
    python scripts/ingest_documents.py
"""

import os
import sys
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant
from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    DirectoryLoader,
)
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

# Load environment variables
load_dotenv()

# Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "tax_memo_production"
DOCUMENTS_DIR = "./documents"  # Directory containing your PDFs/text files


def create_collection_if_not_exists():
    """Create Qdrant collection if it doesn't exist."""
    if not QDRANT_HOST or not QDRANT_API_KEY:
        print("❌ Error: QDRANT_HOST and QDRANT_API_KEY must be set in .env file")
        sys.exit(1)
    
    client = QdrantClient(
        url=QDRANT_HOST,
        api_key=QDRANT_API_KEY,
    )
    
    # Check if collection exists
    try:
        collections = client.get_collections().collections
        collection_names = [col.name for col in collections]
        
        if COLLECTION_NAME not in collection_names:
            print(f"Creating collection: {COLLECTION_NAME}")
            client.create_collection(
                collection_name=COLLECTION_NAME,
                vectors_config=VectorParams(
                    size=1536,  # OpenAI text-embedding-3-small dimension
                    distance=Distance.COSINE,
                ),
            )
            print(f"✅ Collection '{COLLECTION_NAME}' created!")
        else:
            print(f"✅ Collection '{COLLECTION_NAME}' already exists!")
    except Exception as e:
        print(f"❌ Error connecting to Qdrant: {e}")
        print("💡 Check your QDRANT_HOST and QDRANT_API_KEY in .env file")
        sys.exit(1)
    
    return client


def load_documents(documents_dir: str):
    """Load all documents from directory."""
    documents = []
    
    if not os.path.exists(documents_dir):
        print(f"❌ Documents directory not found: {documents_dir}")
        print(f"💡 Create this directory and add your PDF/text files")
        return documents
    
    # Load PDFs
    try:
        pdf_loader = DirectoryLoader(
            documents_dir,
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,
            show_progress=True,
        )
        pdf_docs = pdf_loader.load()
        documents.extend(pdf_docs)
        print(f"📄 Loaded {len(pdf_docs)} PDF documents")
    except Exception as e:
        print(f"⚠️ Error loading PDFs: {e}")
    
    # Load text files
    try:
        text_loader = DirectoryLoader(
            documents_dir,
            glob="**/*.txt",
            loader_cls=TextLoader,
            show_progress=True,
        )
        text_docs = text_loader.load()
        documents.extend(text_docs)
        print(f"📝 Loaded {len(text_docs)} text documents")
    except Exception as e:
        print(f"⚠️ Error loading text files: {e}")
    
    return documents


def split_documents(documents, chunk_size=1000, chunk_overlap=200):
    """Split documents into smaller chunks for better retrieval."""
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"✂️ Split documents into {len(chunks)} chunks")
    
    return chunks


def extract_topic_from_source(source_path: str) -> str:
    """Extract topic from file path or name."""
    filename = os.path.basename(source_path).lower()
    path_lower = source_path.lower()
    
    # Topic mapping based on file names
    if "corporate" in filename or "cit" in filename or "income_tax" in filename or "income-tax" in filename:
        return "corporate_income_tax"
    elif "vat" in filename or "gst" in filename or "sales_tax" in filename or "value-added" in filename:
        return "vat"
    elif "withholding" in filename:
        return "withholding_tax"
    elif "transfer_pricing" in filename or "transfer-pricing" in filename:
        return "transfer_pricing"
    elif "permanent_establishment" in filename or "permanent-establishment" in filename or "pe" in filename:
        return "permanent_establishment"
    elif "substance" in filename:
        return "substance_requirements"
    elif "payroll" in filename:
        return "payroll_tax"
    elif "employment" in filename or "labor" in filename or "labour" in filename:
        return "employment_law"
    elif "corporate_law" in filename or "corporate-law" in filename or "entity" in filename or "incorporation" in filename:
        return "corporate_law"
    elif "intellectual_property" in filename or "intellectual-property" in filename or "ip" in filename or "patent" in filename or "trademark" in filename:
        return "intellectual_property"
    elif "data_protection" in filename or "data-protection" in filename or "gdpr" in filename or "privacy" in filename:
        return "data_protection"
    elif "immigration" in filename or "visa" in filename:
        return "immigration"
    elif "banking" in filename or "payment" in filename or "financial" in filename:
        return "banking_payments"
    elif "licensing" in filename or "licence" in filename or "license" in filename or "permits" in filename:
        return "licensing_permits"
    elif "contract" in filename:
        return "contract_law"
    elif "real_estate" in filename or "real-estate" in filename or "property" in filename:
        return "real_estate"
    elif "dispute" in filename or "arbitration" in filename:
        return "dispute_resolution"
    elif "environmental" in filename or "environment" in filename:
        return "environmental_law"
    elif "social_security" in filename or "social-security" in filename or "insurance" in filename:
        return "social_security"
    elif "timeline" in filename or "setup" in filename or "process" in filename:
        return "timeline"
    elif "cost" in filename or "fee" in filename or "pricing" in filename:
        return "costs"
    elif "risk" in filename:
        return "risk"
    else:
        return "general"  # Default topic


def extract_country_from_source(source_path: str) -> str:
    """Extract country from file path or name."""
    filename = os.path.basename(source_path).lower()
    path_lower = source_path.lower()
    
    # Country mapping
    countries = {
        "netherlands": "netherlands",
        "dutch": "netherlands",
        "nl": "netherlands",
        "nederland": "netherlands",
        "germany": "germany",
        "german": "germany",
        "de": "germany",
        "deutschland": "germany",
        "france": "france",
        "french": "france",
        "fr": "france",
        "belgium": "belgium",
        "belgian": "belgium",
        "be": "belgium",
        "uk": "united_kingdom",
        "united_kingdom": "united_kingdom",
        "britain": "united_kingdom",
        "ireland": "ireland",
        "ie": "ireland",
        "spain": "spain",
        "es": "spain",
        "espana": "spain",
        "italy": "italy",
        "it": "italy",
        "italia": "italy",
        "switzerland": "switzerland",
        "ch": "switzerland",
        "swiss": "switzerland",
        "denmark": "denmark",
        "dk": "denmark",
        "sweden": "sweden",
        "se": "sweden",
        "austria": "austria",
        "at": "austria",
        "poland": "poland",
        "pl": "poland",
        "czech": "czech_republic",
        "cz": "czech_republic",
    }
    
    for key, country in countries.items():
        if key in filename or key in path_lower:
            return country
    
    return None  # No country detected


def add_metadata_to_chunks(chunks):
    """Add metadata to chunks for filtering."""
    enhanced_chunks = []
    
    for chunk in chunks:
        # Extract metadata from source file path
        source = chunk.metadata.get("source", "")
        
        # Determine topic based on file name or content
        topic = extract_topic_from_source(source)
        
        # Determine country from file name or content
        country = extract_country_from_source(source)
        
        # Add metadata
        chunk.metadata.update({
            "topic": topic,
            "country": country.lower() if country else None,
            "source_file": os.path.basename(source),
        })
        
        enhanced_chunks.append(chunk)
    
    return enhanced_chunks


def ingest_documents():
    """Main function to ingest documents into Qdrant."""
    print("🚀 Starting document ingestion...")
    print(f"📁 Documents directory: {DOCUMENTS_DIR}")
    print(f"🗄️ Collection name: {COLLECTION_NAME}\n")
    
    # 1. Create collection
    client = create_collection_if_not_exists()
    
    # 2. Initialize embeddings
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY must be set in .env file")
        sys.exit(1)
    
    print("🔑 Initializing embeddings...")
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # 3. Load documents
    documents = load_documents(DOCUMENTS_DIR)
    
    if not documents:
        print(f"\n❌ No documents found in {DOCUMENTS_DIR}")
        print("💡 Create this directory and add your PDF/text files")
        print("   Example structure:")
        print("   documents/")
        print("   ├── netherlands/")
        print("   │   ├── corporate_income_tax_netherlands.pdf")
        print("   │   └── vat_netherlands.pdf")
        print("   └── germany/")
        print("       └── ...")
        return
    
    # 4. Split documents into chunks
    print("\n✂️ Splitting documents into chunks...")
    chunks = split_documents(documents)
    
    # 5. Add metadata
    print("🏷️ Adding metadata to chunks...")
    chunks = add_metadata_to_chunks(chunks)
    
    # 6. Create Qdrant vector store and ingest
    print(f"\n📤 Ingesting {len(chunks)} chunks into Qdrant...")
    print("⏳ This may take a few minutes...")
    
    try:
        qdrant = Qdrant.from_documents(
            documents=chunks,
            embedding=embeddings,
            collection_name=COLLECTION_NAME,
            url=QDRANT_HOST,
            api_key=QDRANT_API_KEY,
            prefer_grpc=True,
        )
        
        print(f"\n✅ Successfully ingested {len(chunks)} document chunks into Qdrant!")
        print(f"📊 Collection: {COLLECTION_NAME}")
        print(f"🌐 Qdrant URL: {QDRANT_HOST}")
        
        # 7. Verify ingestion
        verify_ingestion(client)
        
    except Exception as e:
        print(f"\n❌ Error during ingestion: {e}")
        print("💡 Check your Qdrant connection and API keys")
        sys.exit(1)


def verify_ingestion(client):
    """Verify that documents were ingested correctly."""
    print("\n" + "="*60)
    print("📈 Collection Statistics")
    print("="*60)
    
    try:
        collection_info = client.get_collection(COLLECTION_NAME)
        print(f"   ✅ Total vectors: {collection_info.points_count}")
        print(f"   ✅ Vector size: {collection_info.config.params.vectors.size}")
        print(f"   ✅ Distance metric: {collection_info.config.params.vectors.distance}")
        
        # Sample a few points to verify metadata
        print(f"\n🔍 Sampling documents...")
        points = client.scroll(
            collection_name=COLLECTION_NAME,
            limit=5,
            with_payload=True,
        )[0]
        
        print(f"\n📄 Sample Documents:")
        for i, point in enumerate(points, 1):
            payload = point.payload
            print(f"\n   {i}. Topic: {payload.get('topic', 'N/A')}")
            print(f"      Country: {payload.get('country', 'N/A')}")
            print(f"      Source: {payload.get('source_file', 'N/A')}")
            content = payload.get('page_content', '')
            if content:
                preview = content[:150].replace('\n', ' ')
                print(f"      Preview: {preview}...")
        
        print("\n" + "="*60)
        print("✅ Ingestion complete! Your RAG system is ready to use.")
        print("="*60)
        
    except Exception as e:
        print(f"⚠️ Error verifying ingestion: {e}")


if __name__ == "__main__":
    ingest_documents()

