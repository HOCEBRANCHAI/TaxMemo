# 📚 Vector Database Setup - Document Ingestion Guide

## 🎯 Overview

Before your RAG system can work, you need to **populate Qdrant with tax and legal documents**. This guide shows you how to:

1. Set up Qdrant (cloud or local)
2. Create a collection
3. Ingest documents (PDFs, text files, etc.)
4. Add metadata for filtering
5. Verify the data is accessible

---

## 📋 Prerequisites

### 1. Qdrant Setup Options

**Option A: Qdrant Cloud** (Recommended for production)
- Sign up at https://cloud.qdrant.io/
- Create a cluster
- Get your URL and API key

**Option B: Qdrant Local** (For development)
- Run Qdrant in Docker:
```bash
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant
```

### 2. Required Python Packages

Add to `requirements.txt`:
```txt
qdrant-client
langchain-qdrant
langchain-openai
langchain-community
pypdf  # For PDF processing
python-docx  # For Word docs (optional)
```

### 3. Environment Variables

Add to your `.env`:
```env
QDRANT_HOST=https://your-cluster.qdrant.io
QDRANT_API_KEY=your-api-key-here
OPENAI_API_KEY=sk-your-openai-key
```

---

## 🚀 Step-by-Step: Document Ingestion

### Step 1: Create Document Ingestion Script

Create `scripts/ingest_documents.py`:

```python
"""
Script to ingest tax and legal documents into Qdrant vector database.
Run this once to populate your knowledge base.
"""

import os
from pathlib import Path
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
    client = QdrantClient(
        url=QDRANT_HOST,
        api_key=QDRANT_API_KEY,
    )
    
    # Check if collection exists
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
    
    return client


def load_documents(documents_dir: str):
    """Load all documents from directory."""
    documents = []
    
    # Load PDFs
    pdf_loader = DirectoryLoader(
        documents_dir,
        glob="**/*.pdf",
        loader_cls=PyPDFLoader,
    )
    pdf_docs = pdf_loader.load()
    documents.extend(pdf_docs)
    print(f"📄 Loaded {len(pdf_docs)} PDF documents")
    
    # Load text files
    text_loader = DirectoryLoader(
        documents_dir,
        glob="**/*.txt",
        loader_cls=TextLoader,
    )
    text_docs = text_loader.load()
    documents.extend(text_docs)
    print(f"📝 Loaded {len(text_docs)} text documents")
    
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


def extract_topic_from_source(source_path: str) -> str:
    """Extract topic from file path or name."""
    filename = os.path.basename(source_path).lower()
    
    # Topic mapping based on file names
    if "corporate" in filename or "cit" in filename or "income_tax" in filename:
        return "corporate_income_tax"
    elif "vat" in filename or "gst" in filename or "sales_tax" in filename:
        return "vat"
    elif "withholding" in filename:
        return "withholding_tax"
    elif "transfer_pricing" in filename:
        return "transfer_pricing"
    elif "permanent_establishment" in filename or "pe" in filename:
        return "permanent_establishment"
    elif "substance" in filename:
        return "substance_requirements"
    elif "payroll" in filename:
        return "payroll_tax"
    elif "employment" in filename or "labor" in filename:
        return "employment_law"
    elif "corporate_law" in filename or "entity" in filename:
        return "corporate_law"
    elif "intellectual_property" in filename or "ip" in filename:
        return "intellectual_property"
    elif "data_protection" in filename or "gdpr" in filename:
        return "data_protection"
    elif "immigration" in filename:
        return "immigration"
    elif "banking" in filename:
        return "banking_payments"
    elif "licensing" in filename:
        return "licensing_permits"
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
        "germany": "germany",
        "german": "germany",
        "de": "germany",
        "france": "france",
        "french": "france",
        "fr": "france",
        "belgium": "belgium",
        "belgian": "belgium",
        "be": "belgium",
        "uk": "united_kingdom",
        "united_kingdom": "united_kingdom",
        "ireland": "ireland",
        "ie": "ireland",
        "spain": "spain",
        "es": "spain",
        "italy": "italy",
        "it": "italy",
        "switzerland": "switzerland",
        "ch": "switzerland",
    }
    
    for key, country in countries.items():
        if key in filename or key in path_lower:
            return country
    
    return None  # No country detected


def ingest_documents():
    """Main function to ingest documents into Qdrant."""
    print("🚀 Starting document ingestion...")
    
    # 1. Create collection
    client = create_collection_if_not_exists()
    
    # 2. Initialize embeddings
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    # 3. Load documents
    if not os.path.exists(DOCUMENTS_DIR):
        print(f"❌ Documents directory not found: {DOCUMENTS_DIR}")
        print("💡 Create this directory and add your PDF/text files")
        return
    
    documents = load_documents(DOCUMENTS_DIR)
    
    if not documents:
        print(f"❌ No documents found in {DOCUMENTS_DIR}")
        return
    
    # 4. Split documents into chunks
    chunks = split_documents(documents)
    
    # 5. Add metadata
    chunks = add_metadata_to_chunks(chunks)
    
    # 6. Create Qdrant vector store
    qdrant = Qdrant.from_documents(
        documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        url=QDRANT_HOST,
        api_key=QDRANT_API_KEY,
        prefer_grpc=True,
    )
    
    print(f"✅ Successfully ingested {len(chunks)} document chunks into Qdrant!")
    print(f"📊 Collection: {COLLECTION_NAME}")
    print(f"🌐 Qdrant URL: {QDRANT_HOST}")
    
    # 7. Verify ingestion
    verify_ingestion(client)


def verify_ingestion(client):
    """Verify that documents were ingested correctly."""
    collection_info = client.get_collection(COLLECTION_NAME)
    print(f"\n📈 Collection Stats:")
    print(f"   - Total vectors: {collection_info.points_count}")
    print(f"   - Vector size: {collection_info.config.params.vectors.size}")
    print(f"   - Distance metric: {collection_info.config.params.vectors.distance}")
    
    # Sample a few points to verify metadata
    print(f"\n🔍 Sampling documents...")
    points = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=3,
        with_payload=True,
    )[0]
    
    for point in points:
        print(f"\n   Document:")
        print(f"   - Topic: {point.payload.get('topic', 'N/A')}")
        print(f"   - Country: {point.payload.get('country', 'N/A')}")
        print(f"   - Source: {point.payload.get('source_file', 'N/A')}")
        print(f"   - Content preview: {point.payload.get('page_content', '')[:100]}...")


if __name__ == "__main__":
    ingest_documents()
```

---

## 📁 Directory Structure

Create this structure in your project:

```
/tax-memo-api/
|-- documents/
|   |-- netherlands/
|   |   |-- corporate_income_tax_netherlands.pdf
|   |   |-- vat_netherlands.pdf
|   |   |-- employment_law_netherlands.pdf
|   |   |-- corporate_law_netherlands.pdf
|   |-- germany/
|   |   |-- corporate_income_tax_germany.pdf
|   |   |-- vat_germany.pdf
|   |   |-- ...
|   |-- general/
|   |   |-- transfer_pricing_guide.pdf
|   |   |-- substance_requirements.pdf
|   |   |-- ...
|-- scripts/
|   |-- ingest_documents.py
|-- app/
|   |-- ...
```

---

## 🔧 Step 2: Prepare Your Documents

### Document Sources

You'll need documents about:
- **Tax Topics**: CIT, VAT, Withholding Tax, Transfer Pricing, Substance Requirements, etc.
- **Legal Topics**: Corporate Law, Employment Law, IP, GDPR, Immigration, etc.
- **Jurisdictions**: Netherlands, Germany, France, Belgium, etc.

### Document Types

1. **Official Sources**:
   - Government tax guides
   - Chamber of Commerce documentation
   - Legal framework documents

2. **Professional Sources**:
   - Law firm articles
   - Tax advisor guides
   - Industry publications

3. **Internal Knowledge**:
   - Your company's tax memos
   - Previous client analyses
   - Internal guides

### Document Format

- **PDFs**: Best for structured documents
- **Text files**: Good for plain text content
- **Word docs**: Can be converted to PDF or text

---

## 🚀 Step 3: Run the Ingestion Script

```bash
# Install additional dependencies
pip install pypdf langchain-community

# Run the ingestion script
python scripts/ingest_documents.py
```

**Expected Output**:
```
🚀 Starting document ingestion...
✅ Collection 'tax_memo_production' already exists!
📄 Loaded 15 PDF documents
📝 Loaded 3 text documents
✂️ Split documents into 245 chunks
✅ Successfully ingested 245 document chunks into Qdrant!
📊 Collection: tax_memo_production
🌐 Qdrant URL: https://your-cluster.qdrant.io

📈 Collection Stats:
   - Total vectors: 245
   - Vector size: 1536
   - Distance metric: Distance.COSINE
```

---

## 🔍 Step 4: Verify Your Data

### Test Query Script

Create `scripts/test_queries.py`:

```python
"""Test queries to verify document ingestion."""

import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import Qdrant

load_dotenv()

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
qdrant = Qdrant.from_existing_collection(
    embedding=embeddings,
    collection_name="tax_memo_production",
    url=os.getenv("QDRANT_HOST"),
    api_key=os.getenv("QDRANT_API_KEY"),
    prefer_grpc=True,
)

# Test query 1: Corporate Income Tax in Netherlands
print("🔍 Test Query 1: CIT in Netherlands")
results = qdrant.similarity_search(
    query="Corporate income tax rate in Netherlands",
    filter={"country": "netherlands", "topic": "corporate_income_tax"},
    k=3,
)
print(f"Found {len(results)} results")
for i, doc in enumerate(results, 1):
    print(f"\n{i}. {doc.page_content[:200]}...")
    print(f"   Metadata: {doc.metadata}")

# Test query 2: VAT in Netherlands
print("\n🔍 Test Query 2: VAT in Netherlands")
results = qdrant.similarity_search(
    query="VAT registration requirements in Netherlands",
    filter={"country": "netherlands", "topic": "vat"},
    k=3,
)
print(f"Found {len(results)} results")
for i, doc in enumerate(results, 1):
    print(f"\n{i}. {doc.page_content[:200]}...")
```

Run it:
```bash
python scripts/test_queries.py
```

---

## 📝 Metadata Best Practices

### Required Metadata Fields

Every document chunk should have:
- `topic`: The tax/legal topic (e.g., "corporate_income_tax", "vat", "employment_law")
- `country`: The jurisdiction (e.g., "netherlands", "germany")
- `source_file`: Original file name

### Topic Values (Match Your RAG Queries)

Use these exact topic values to match your `rag_logic.py` filters:

**Tax Topics**:
- `corporate_income_tax`
- `vat` or `vat_digital_services`
- `withholding_tax`
- `transfer_pricing`
- `permanent_establishment`
- `substance_requirements`
- `payroll_tax`

**Legal Topics**:
- `corporate_law`
- `employment_law`
- `intellectual_property`
- `data_protection`
- `immigration`
- `banking_payments`
- `licensing_permits`
- `contract_law`
- `real_estate`
- `dispute_resolution`
- `environmental_law`
- `social_security`

### Country Values

Use lowercase country names:
- `netherlands`, `germany`, `france`, `belgium`, etc.

---

## 🔄 Updating Documents

### Re-run Ingestion

If you add new documents:
1. Add PDFs to `documents/` directory
2. Run `python scripts/ingest_documents.py` again
3. Script will add new documents (won't duplicate existing ones)

### Delete and Recreate (if needed)

```python
from qdrant_client import QdrantClient

client = QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY)
client.delete_collection(COLLECTION_NAME)
# Then run ingest_documents.py again
```

---

## 🎯 Quick Start Checklist

- [ ] Set up Qdrant (cloud or local)
- [ ] Add `QDRANT_HOST` and `QDRANT_API_KEY` to `.env`
- [ ] Create `documents/` directory
- [ ] Add PDF/text files to `documents/`
- [ ] Create `scripts/ingest_documents.py`
- [ ] Install dependencies: `pip install pypdf langchain-community`
- [ ] Run ingestion: `python scripts/ingest_documents.py`
- [ ] Verify with test queries: `python scripts/test_queries.py`
- [ ] Test your API endpoint to ensure RAG works

---

## 💡 Tips

1. **Document Quality**: Better documents = better RAG results. Use authoritative sources.

2. **Chunk Size**: 1000 characters is good for most cases. Adjust if needed:
   - Smaller chunks (500): More precise, but might miss context
   - Larger chunks (2000): More context, but less precise

3. **Metadata**: Accurate metadata is crucial for filtering. Double-check your topic/country extraction.

4. **Incremental Updates**: Add new documents regularly. The script handles new additions well.

5. **Testing**: Always test queries after ingestion to verify documents are findable.

---

## 🚨 Common Issues

### Issue: "Collection not found"
**Solution**: Run `ingest_documents.py` first to create the collection.

### Issue: "No documents found"
**Solution**: Check that `documents/` directory exists and contains PDF/text files.

### Issue: "Embedding dimension mismatch"
**Solution**: Make sure you're using `text-embedding-3-small` (1536 dimensions) consistently.

### Issue: "Documents not being retrieved"
**Solution**: 
- Check metadata matches your filter queries
- Verify topic and country values are correct
- Test with a simple query first

---

## 📚 Next Steps After Ingestion

1. ✅ Documents are in Qdrant
2. ✅ Test your API endpoint
3. ✅ Verify RAG queries return relevant context
4. ✅ Monitor and improve document quality over time

Once documents are ingested, your RAG system will be able to find relevant information and generate accurate memos! 🎉

