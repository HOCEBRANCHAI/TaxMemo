# In app/rag_logic.py
import os
import json
from typing import List, Optional
from .models import MemoRequest
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_qdrant import Qdrant
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field  # Use regular pydantic, not pydantic_v1


# --- 1. DEFINE LLM OUTPUT STRUCTURES (FOR STRUCTURED JSON) ---
# This is the key to production-ready JSON.
# We define *exactly* what we want the LLM to return.


class CITOpportunity(BaseModel):
    """A tax credit or optimization strategy."""
    name: str = Field(..., description="The name of the tax credit or optimization strategy (e.g., 'R&D Tax Credits (WBSO)')")
    description: str = Field(..., description="A brief, 1-2 sentence description of the opportunity")


class CITSection(BaseModel):
    """Structured data for the Corporate Income Tax section."""
    standard_rate: str = Field(..., description="The standard corporate income tax rate (e.g., '25.8%')")
    description: str = Field(..., description="A 2-3 sentence overview of the CIT system based on the context.")
    optimization_strategies: Optional[List[CITOpportunity]] = Field(
        default=None,
        description="A list of relevant tax optimization strategies or credits."
    )


class VATRate(BaseModel):
    """A VAT rate with its application."""
    rate: str = Field(..., description="The VAT rate (e.g., '21%', '9%', '0%')")
    applies_to: str = Field(..., description="A brief description of what this rate applies to (e.g., 'Most goods & services', 'Food, books, medicine')")


class VATSection(BaseModel):
    """Structured data for the Value-Added Tax (VAT) section."""
    rates: List[VATRate] = Field(..., description="A list of the applicable VAT rates.")
    registration_requirements: str = Field(..., description="A 2-3 sentence summary of when a company must register for VAT.")
    oss_details: Optional[str] = Field(
        default=None,
        description="Details about the One-Stop-Shop (OSS) system, if relevant for the user's transaction types."
    )


# --- 2. INITIALIZE CLIENTS (Global Scope with Lazy Initialization) ---
# This is a production best practice. These clients are created once when the
# API server starts, not on every request.
_llm = None
_embeddings = None
_qdrant_client = None


def _get_clients():
    """Lazy initialization of clients to ensure env vars are loaded."""
    global _llm, _embeddings, _qdrant_client
    if _llm is None:
        _llm = ChatOpenAI(model="gpt-4o", temperature=0)
        _embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
        _qdrant_client = Qdrant.from_existing_collection(
            embedding=_embeddings,
            collection_name="tax_memo_production",
            url=os.getenv("QDRANT_HOST"),
            api_key=os.getenv("QDRANT_API_KEY"),
            prefer_grpc=True,
        )
    return _llm, _embeddings, _qdrant_client


def _format_context(docs):
    """Helper function to format RAG context from documents."""
    # Qdrant returns documents with page_content attribute
    return "\n\n---\n\n".join([doc.page_content for doc in docs])


# --- 3. THE MAIN ORCHESTRATOR FUNCTION ---
def run_memo_orchestrator(request: MemoRequest):
    """
    Accepts the validated user profile, creates a memo plan,
    runs RAG workers for each section, and assembles the final JSON response.
    """
    memo_plan = create_memo_plan(request)
    final_memo = {}
    
    print(f"Running orchestrator for plan: {memo_plan}")
    
    section_generators = {
        "Executive Summary": generate_executive_summary,
        "Market Entry Options Analysis": generate_market_entry_options,
        "Tax & Regulatory Compliance": generate_tax_section,
        "Legal & Business Topics": generate_legal_section,
        "Implementation Timeline": generate_timeline_section,
        "Resource Requirements & Costs": generate_costs_section,
        "Risk Assessment": generate_risk_section,
        "Next Steps & Action Plan": generate_next_steps_section,
    }
    
    for section in memo_plan:
        if section in section_generators:
            final_memo[section] = section_generators[section](request)
    
    print("Orchestration complete.")
    return final_memo


# --- 4. THE "WORKER" FUNCTIONS ---

def create_memo_plan(request: MemoRequest):
    """Creates the memo's table of contents based on user input."""
    plan = ["Executive Summary"]
    
    # Always include market entry options if we have jurisdiction info
    if request.primary_jurisdiction:
        plan.append("Market Entry Options Analysis")
    
    # Add tax section if tax queries are provided
    if request.tax_queries:
        plan.append("Tax & Regulatory Compliance")
    
    # Add legal section if legal topics are selected
    if request.selected_legal_topics:
        plan.append("Legal & Business Topics")
    
    # Always include implementation and planning sections
    plan.extend([
        "Implementation Timeline",
        "Resource Requirements & Costs",
        "Risk Assessment",
        "Next Steps & Action Plan"
    ])
    
    return plan


def generate_executive_summary(request: MemoRequest):
    """Placeholder for the summary worker."""
    print(f"Generating summary for {request.business_name}...")
    # In a real scenario, this would also run RAG queries
    # to find the best entity type, timeline, etc.
    return {
        "primary_recommendation": f"Based on your profile as a '{request.industry or 'company'}' company, we recommend establishing a legal entity for your entry into {request.primary_jurisdiction or 'the target market'}.",
        "timeline": "3-4 weeks",
        "initial_investment": "To be determined based on structure",
        "liability_protection": "Full legal protection with proper entity setup",
        "key_strategic_benefits": [
            {"name": "Tax Optimization", "description": "Access to tax treaties and optimization strategies."},
            {"name": "Market Credibility", "description": "A full legal entity in the target market."}
        ]
    }


def generate_tax_section(request: MemoRequest):
    """
    Generates the full JSON for the Tax & Compliance section.
    This is the production-ready RAG worker using structured output.
    """
    print("Generating tax section...")
    tax_json = {}
    
    if not request.tax_queries or not request.primary_jurisdiction:
        return tax_json  # Return empty if no topics or country selected
    
    # Get clients (lazy initialization)
    llm, embeddings, qdrant_client = _get_clients()
    
    # This is the base filter for ALL queries in this section
    base_filter = {"country": request.primary_jurisdiction.lower()}  # e.g., "netherlands"
    
    # --- Worker 1: Corporate Income Tax ---
    if "Corporate income tax implications" in request.tax_queries:
        print("-> Running CIT worker...")
        try:
            # 1. Create Filter: Find "cit" documents for the country
            cit_filter = {**base_filter, "topic": "corporate_income_tax"}
            
            # 2. Create Search Query: Make it specific to the user
            cit_query = f"Corporate income tax rules for a {request.industry or 'company'} company in {request.primary_jurisdiction}."
            if request.specific_concerns:
                cit_query += f" Specific concerns: {request.specific_concerns}"
            
            # 3. Run RAG: Get context from Vector DB
            cit_docs = qdrant_client.similarity_search(
                query=cit_query,
                filter=cit_filter,
                k=3
            )
            cit_context = _format_context(cit_docs)
            
            # 4. Create Prompt: Instruct the LLM to generate structured JSON
            cit_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert tax advisor. Based *only* on the provided context, generate a structured JSON response. Do not invent information."),
                ("human", f"""
Context:
{cit_context}

User Profile:
- Industry: {request.industry or 'Not specified'}
- Business Size: {request.company_size or 'Not specified'}

Please generate the JSON for the Corporate Income Tax section.
""")
            ])
            
            # 5. Call LLM & Force JSON Output
            # This chain binds our Pydantic model (CITSection) to the LLM
            cit_chain = cit_prompt | llm.with_structured_output(CITSection)
            cit_json_response = cit_chain.invoke({})
            
            # Convert Pydantic model to dict for JSON serialization
            tax_json["corporate_income_tax"] = cit_json_response.model_dump()
            
        except Exception as e:
            print(f"ERROR in CIT worker: {e}")
            tax_json["corporate_income_tax"] = {"error": "Failed to generate CIT data.", "details": str(e)}
    
    # --- Worker 2: Value-Added Tax (VAT) ---
    if "Value-added tax (VAT) registration and compliance" in request.tax_queries:
        print("-> Running VAT worker...")
        try:
            # 1. Create Filter: Find "vat" documents
            vat_filter = {**base_filter, "topic": "vat_digital_services"}  # Adjust topic as needed
            
            # 2. Create Search Query: Use the user's specific activity
            transaction_types_str = ', '.join(request.transaction_types) if request.transaction_types else 'general business activities'
            vat_query = f"VAT rules in {request.primary_jurisdiction} for the following transaction types: {transaction_types_str}. Are OSS rules applicable?"
            
            # 3. Run RAG:
            vat_docs = qdrant_client.similarity_search(
                query=vat_query,
                filter=vat_filter,
                k=3
            )
            vat_context = _format_context(vat_docs)
            
            # 4. Create Prompt:
            vat_prompt = ChatPromptTemplate.from_messages([
                ("system", "You are an expert tax advisor. Based *only* on the provided context, generate a structured JSON response. Focus on the user's transaction types."),
                ("human", f"""
Context:
{vat_context}

User Profile:
- Transaction Types: {transaction_types_str}
- Industry: {request.industry or 'Not specified'}

Please generate the JSON for the VAT section.
""")
            ])
            
            # 5. Call LLM & Force JSON Output
            vat_chain = vat_prompt | llm.with_structured_output(VATSection)
            vat_json_response = vat_chain.invoke({})
            
            tax_json["vat_compliance"] = vat_json_response.model_dump()
            
        except Exception as e:
            print(f"ERROR in VAT worker: {e}")
            tax_json["vat_compliance"] = {"error": "Failed to generate VAT data.", "details": str(e)}
    
    # Additional tax query workers can be added here following the same pattern
    # For example: Transfer pricing, Withholding tax, Permanent establishment, etc.
    
    print("Tax section generation complete.")
    return tax_json


def generate_market_entry_options(request: MemoRequest):
    """Generates the Market Entry Options table JSON."""
    if not request.primary_jurisdiction:
        return {"status": "No primary jurisdiction provided"}
    
    return {"status": "Pending implementation for Market Entry Options..."}


def generate_legal_section(request: MemoRequest):
    """Generates the Legal & Business Topics JSON."""
    if not request.primary_jurisdiction or not request.selected_legal_topics:
        return {"status": "No legal topics or jurisdiction provided"}
    
    legal_json = {}
    base_filter = {"country": request.primary_jurisdiction.lower()}
    
    # Process each selected legal topic
    for topic_id in request.selected_legal_topics:
        topic_data = request.legal_topic_data.get(topic_id, {}) if request.legal_topic_data else {}
        
        # Build topic-specific query based on the topic and its data
        query = f"Legal requirements for {topic_id.replace('-', ' ').title()} in {request.primary_jurisdiction}"
        
        # Enhance query with topic-specific data
        if topic_id == "employment-law" and topic_data.get("hire-employees") == "Yes":
            employee_count = topic_data.get("employee-count", "")
            query += f" for hiring {employee_count} employees" if employee_count else " for hiring employees"
        
        # Run RAG query for this topic
        try:
            llm, embeddings, qdrant_client = _get_clients()
            topic_filter = {**base_filter, "topic": topic_id.replace("-", "_")}
            docs = qdrant_client.similarity_search(query=query, filter=topic_filter, k=3)
            context = _format_context(docs)
            
            # For now, return placeholder - you can add structured output models for legal topics too
            legal_json[topic_id] = {
                "status": "Implementation pending",
                "context_summary": context[:200] + "..." if len(context) > 200 else context
            }
        except Exception as e:
            print(f"ERROR in legal topic {topic_id}: {e}")
            legal_json[topic_id] = {"error": f"Failed to generate data for {topic_id}"}
    
    return legal_json


def generate_timeline_section(request: MemoRequest):
    """Generates the Implementation Timeline JSON."""
    if not request.primary_jurisdiction:
        return {"status": "No primary jurisdiction provided"}
    
    return {"status": "Pending implementation..."}


def generate_costs_section(request: MemoRequest):
    """Generates the Resource Requirements & Costs JSON."""
    if not request.primary_jurisdiction:
        return {"status": "No primary jurisdiction provided"}
    
    return {"status": "Pending implementation..."}


def generate_risk_section(request: MemoRequest):
    """Generates the Risk Assessment JSON."""
    if not request.primary_jurisdiction:
        return {"status": "No primary jurisdiction provided"}
    
    return {"status": "Pending implementation..."}


def generate_next_steps_section(request: MemoRequest):
    """Generates the Next Steps & Action Plan JSON."""
    if not request.primary_jurisdiction:
        return {"status": "No primary jurisdiction provided"}
    
    return {"status": "Pending implementation..."}
