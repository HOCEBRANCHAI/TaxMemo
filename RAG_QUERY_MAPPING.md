# 🔍 RAG Query Mapping: User Input → Document Retrieval

## Overview

Your RAG system uses **user inputs** to build **intelligent queries** that retrieve relevant documents from Qdrant. This document shows exactly how each user input field maps to RAG queries and filters.

---

## 🎯 How RAG Works with User Inputs

```
User Input (JSON)
    ↓
Extract Key Information
    ↓
Build RAG Query + Filter
    ↓
Query Qdrant Vector DB
    ↓
Retrieve Relevant Documents
    ↓
Use as Context for LLM
    ↓
Generate Structured JSON Response
```

---

## 📊 Input Field → RAG Query Mapping

### 1. **Primary Jurisdiction** → Base Filter

**User Input:**
```json
{
  "primaryJurisdiction": "Netherlands"
}
```

**Used In RAG:**
```python
# In rag_logic.py - generate_tax_section()
base_filter = {"country": request.primary_jurisdiction.lower()}  
# Result: {"country": "netherlands"}
```

**Purpose**: Filters all Qdrant queries to only retrieve documents about that specific country.

**Example Usage**:
- Tax queries: `{"country": "netherlands", "topic": "corporate_income_tax"}`
- Legal queries: `{"country": "netherlands", "topic": "employment_law"}`

---

### 2. **Tax Queries** → Topic Filter + Query Text

**User Input:**
```json
{
  "taxQueries": [
    "Corporate income tax implications",
    "VAT registration and compliance",
    "Substance requirements"
  ]
}
```

**Used In RAG:**

For each tax query, the system:

1. **Maps to Topic**: Converts UI text to metadata topic
   ```python
   "Corporate income tax implications" → topic: "corporate_income_tax"
   "VAT registration and compliance" → topic: "vat"
   "Substance requirements" → topic: "substance_requirements"
   ```

2. **Creates Filter**: Combines country + topic
   ```python
   filter = {
       "country": "netherlands",
       "topic": "corporate_income_tax"
   }
   ```

3. **Builds Query**: Adds user context
   ```python
   query = f"Corporate income tax rules for a {request.industry} company in Netherlands"
   # Example: "Corporate income tax rules for a Software & Technology company in Netherlands"
   ```

4. **Runs RAG Query**:
   ```python
   docs = qdrant_client.similarity_search(
       query=query,
       filter=filter,
       k=3
   )
   ```

**Current Implementation**: ✅ CIT and VAT workers implemented
**Missing**: ⚠️ Transfer Pricing, Withholding Tax, Substance Requirements, etc.

---

### 3. **Industry** → Query Enhancement

**User Input:**
```json
{
  "industry": "Software & Technology"
}
```

**Used In RAG:**
```python
# Enhances query specificity
cit_query = f"Corporate income tax rules for a {request.industry} company in {request.primary_jurisdiction}"
# Result: "Corporate income tax rules for a Software & Technology company in Netherlands"
```

**Purpose**: Makes queries more specific, retrieves industry-relevant documents.

---

### 4. **Transaction Types** → Query Enhancement

**User Input:**
```json
{
  "transactionTypes": [
    "Provision of services",
    "Software licensing",
    "E-commerce"
  ]
}
```

**Used In RAG:**
```python
# In VAT worker
transaction_types_str = ', '.join(request.transaction_types)
vat_query = f"VAT rules in {request.primary_jurisdiction} for the following transaction types: {transaction_types_str}"
# Result: "VAT rules in Netherlands for the following transaction types: Provision of services, Software licensing, E-commerce"
```

**Purpose**: Retrieves documents specific to user's actual business activities.

---

### 5. **Specific Concerns** → Query Enhancement

**User Input:**
```json
{
  "specificConcerns": "We want to minimize tax burden while maintaining full compliance with EU regulations"
}
```

**Used In RAG:**
```python
cit_query = f"Corporate income tax rules for a {request.industry} company in {request.primary_jurisdiction}"
if request.specific_concerns:
    cit_query += f" Specific concerns: {request.specific_concerns}"
# Result includes user's specific concerns in the query
```

**Purpose**: Adds user's specific questions/concerns to the query for more targeted retrieval.

---

### 6. **Selected Legal Topics** → Topic Filter

**User Input:**
```json
{
  "selectedLegalTopics": [
    "corporate-law",
    "employment-law",
    "data-protection"
  ]
}
```

**Used In RAG:**
```python
# In generate_legal_section()
for topic_id in request.selected_legal_topics:
    topic_filter = {
        "country": request.primary_jurisdiction.lower(),
        "topic": topic_id.replace("-", "_")  # "employment-law" → "employment_law"
    }
    
    query = f"Legal requirements for {topic_id.replace('-', ' ').title()} in {request.primary_jurisdiction}"
    # Example: "Legal requirements for Employment Law in Netherlands"
    
    docs = qdrant_client.similarity_search(
        query=query,
        filter=topic_filter,
        k=3
    )
```

**Purpose**: Retrieves documents for each selected legal topic.

**Current Status**: ⚠️ RAG queries work, but returns placeholder JSON (needs structured output models)

---

### 7. **Legal Topic Data** → Query Enhancement

**User Input:**
```json
{
  "legalTopicData": {
    "employment-law": {
      "hire-employees": "Yes",
      "employee-count": "10",
      "remote-work": "Yes",
      "employment-concerns": "Need to understand termination requirements"
    }
  }
}
```

**Used In RAG:**
```python
# In generate_legal_section()
topic_data = request.legal_topic_data.get("employment-law", {})

# Build more specific query
query = f"Employment law for {request.primary_jurisdiction}"
if topic_data.get("hire-employees") == "Yes":
    employee_count = topic_data.get("employee-count", "")
    query += f" for hiring {employee_count} employees"
if topic_data.get("remote-work") == "Yes":
    query += " including remote work regulations"
if topic_data.get("employment-concerns"):
    query += f". Concerns: {topic_data['employment-concerns']}"

# Final query might be:
# "Employment law for Netherlands for hiring 10 employees including remote work regulations. 
#  Concerns: Need to understand termination requirements"
```

**Purpose**: Creates highly specific queries based on user's detailed answers to topic-specific questions.

---

### 8. **Business Structure** → Query Enhancement

**User Input:**
```json
{
  "businessStructure": "holding"
}
```

**Used In RAG:**
```python
# Can be used in Executive Summary or Market Entry Options
query = f"Recommendation for {request.business_structure} structure for a {request.industry} company"
# Example: "Recommendation for holding structure for a Software & Technology company"
```

**Purpose**: Helps retrieve documents relevant to the user's chosen structure template.

---

### 9. **Entry Goals** → Query Enhancement

**User Input:**
```json
{
  "entryGoals": [
    "Sell products/services",
    "Tax optimization",
    "Establish physical presence"
  ]
}
```

**Used In RAG:**
```python
# Can be used in Executive Summary
goals_summary = ", ".join(request.entry_goals)
query = f"Market entry strategy for {goals_summary} in {request.primary_jurisdiction}"
# Example: "Market entry strategy for Sell products/services, Tax optimization, Establish physical presence in Netherlands"
```

**Purpose**: Retrieves documents relevant to user's specific goals.

---

### 10. **Timeline** → Query Enhancement

**User Input:**
```json
{
  "timeline": "Medium-term (3-6 months)"
}
```

**Used In RAG:**
```python
# Can be used in Timeline section
query = f"Implementation timeline for {request.business_structure} in {request.primary_jurisdiction}. User timeline: {request.timeline}"
```

**Purpose**: Retrieves timeline information matching user's urgency.

---

## 🔄 Complete RAG Flow Example

### Example: User wants Corporate Income Tax info

**User Input:**
```json
{
  "primaryJurisdiction": "Netherlands",
  "industry": "Software & Technology",
  "companySize": "Medium (51-250 employees)",
  "taxQueries": ["Corporate income tax implications"],
  "specificConcerns": "Minimize tax burden while maintaining compliance"
}
```

**Step 1: Extract Key Info**
```python
country = "netherlands"
topic = "corporate_income_tax"
industry = "Software & Technology"
concerns = "Minimize tax burden while maintaining compliance"
```

**Step 2: Build Filter**
```python
filter = {
    "country": "netherlands",
    "topic": "corporate_income_tax"
}
```

**Step 3: Build Query**
```python
query = "Corporate income tax rules for a Software & Technology company in Netherlands. Specific concerns: Minimize tax burden while maintaining compliance"
```

**Step 4: Query Qdrant**
```python
docs = qdrant_client.similarity_search(
    query=query,
    filter=filter,
    k=3
)
# Returns top 3 most relevant documents about Dutch CIT for tech companies
```

**Step 5: Format Context**
```python
context = "\n\n---\n\n".join([doc.page_content for doc in docs])
# Combines document contents into context string
```

**Step 6: Send to LLM**
```python
prompt = f"""
Context:
{context}

User Profile:
- Industry: Software & Technology
- Business Size: Medium (51-250 employees)

Generate CIT section...
"""

result = llm.with_structured_output(CITSection).invoke(prompt)
# LLM generates structured JSON using the retrieved context
```

---

## 📋 Input Fields Used for RAG

### ✅ Fields Currently Used in RAG Queries

| Input Field | Used In | Purpose |
|------------|---------|---------|
| `primaryJurisdiction` | All sections | Base country filter |
| `taxQueries[]` | Tax section | Determines which tax topics to query |
| `industry` | Tax, Executive Summary | Query enhancement |
| `transactionTypes[]` | Tax section (VAT) | Query specificity |
| `specificConcerns` | Tax section | Query enhancement |
| `selectedLegalTopics[]` | Legal section | Determines which legal topics to query |
| `legalTopicData{}` | Legal section | Query enhancement per topic |

### ⚠️ Fields Not Yet Used (But Could Be)

| Input Field | Potential Use | Priority |
|------------|--------------|----------|
| `businessStructure` | Executive Summary, Market Entry | MEDIUM |
| `entryGoals[]` | Executive Summary | MEDIUM |
| `timeline` | Timeline section | MEDIUM |
| `companySize` | All sections | LOW |
| `currentMarkets` | Market Entry | LOW |
| `taxTreaties[]` | Tax section | MEDIUM |
| `companies[]` | Corporate structure analysis | LOW |
| `relationships[]` | Corporate structure analysis | LOW |

---

## 🎯 RAG Query Patterns by Section

### Tax Section

**Pattern:**
```python
for tax_query in request.tax_queries:
    # 1. Map to topic
    topic = map_tax_query_to_topic(tax_query)
    
    # 2. Create filter
    filter = {
        "country": request.primary_jurisdiction.lower(),
        "topic": topic
    }
    
    # 3. Build query
    query = f"{tax_query} for {request.industry} in {request.primary_jurisdiction}"
    if request.specific_concerns:
        query += f". {request.specific_concerns}"
    
    # 4. Run RAG
    docs = qdrant.similarity_search(query=query, filter=filter, k=3)
    
    # 5. Generate structured output
    result = llm.with_structured_output(TaxSectionModel).invoke(context)
```

### Legal Section

**Pattern:**
```python
for topic_id in request.selected_legal_topics:
    topic_data = request.legal_topic_data.get(topic_id, {})
    
    # 1. Create filter
    filter = {
        "country": request.primary_jurisdiction.lower(),
        "topic": topic_id.replace("-", "_")
    }
    
    # 2. Build query with topic-specific data
    query = build_legal_query(topic_id, topic_data, request)
    
    # 3. Run RAG
    docs = qdrant.similarity_search(query=query, filter=filter, k=3)
    
    # 4. Generate structured output
    result = llm.with_structured_output(LegalTopicModel).invoke(context)
```

### Executive Summary

**Pattern:**
```python
# Multiple RAG queries for different aspects

# Structure query
structure_query = f"{request.business_structure} structure for {request.industry}"
structure_docs = qdrant.similarity_search(
    query=structure_query,
    filter={"country": request.primary_jurisdiction.lower(), "topic": "entity_setup"},
    k=2
)

# Timeline query
timeline_query = f"Setup timeline for {request.business_structure} in {request.primary_jurisdiction}"
timeline_docs = qdrant.similarity_search(
    query=timeline_query,
    filter={"country": request.primary_jurisdiction.lower(), "topic": "timeline"},
    k=2
)

# Tax overview query
tax_query = f"Tax benefits for {request.industry} in {request.primary_jurisdiction}"
tax_docs = qdrant.similarity_search(
    query=tax_query,
    filter={"country": request.primary_jurisdiction.lower(), "topic": "corporate_income_tax"},
    k=2
)

# Combine all contexts
context = combine_contexts(structure_docs, timeline_docs, tax_docs)

# Generate summary
result = llm.with_structured_output(ExecutiveSummaryModel).invoke(context)
```

---

## 🔑 Key Points

1. **Primary Jurisdiction** = Base filter for ALL queries
2. **Tax Queries** = Determines which tax topics to retrieve
3. **Legal Topics** = Determines which legal topics to retrieve
4. **Industry/Transaction Types/Concerns** = Enhance query specificity
5. **Legal Topic Data** = Makes legal queries highly specific

---

## 📊 Current RAG Implementation Status

### ✅ Fully Implemented
- Tax Section: CIT worker (uses RAG)
- Tax Section: VAT worker (uses RAG)

### ⚠️ Partially Implemented
- Legal Section: RAG queries work, but needs structured output models

### ❌ Not Yet Implemented
- Tax Section: Transfer Pricing, Withholding Tax, Substance Requirements, etc.
- Executive Summary: Has placeholder, needs RAG queries
- Market Entry Options: Needs RAG queries
- Timeline, Costs, Risk, Next Steps: Need RAG queries

---

## 💡 Summary

**YES, you ARE using RAG retrieval!**

Your system:
1. ✅ Takes user inputs (jurisdiction, tax queries, legal topics, etc.)
2. ✅ Builds intelligent queries based on those inputs
3. ✅ Filters Qdrant by country and topic
4. ✅ Retrieves relevant documents
5. ✅ Uses documents as context for LLM
6. ✅ Generates structured JSON responses

The user inputs **directly drive** the RAG retrieval process. Each field is used to either:
- Create filters (country, topic)
- Build query text (industry, concerns, transaction types)
- Determine which sections to generate (tax queries, legal topics)

Your RAG system is **user-input-driven** - the more specific the user's inputs, the better the retrieved documents and final output! 🎯

