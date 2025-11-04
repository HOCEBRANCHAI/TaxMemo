# In app/models.py
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


# --- SUB-MODELS for nested data ---


# Business Structure: Company Entity
class Company(BaseModel):
    """Company entity in the business structure"""
    id: str
    name: str
    country: str
    type: str  # "Holding", "Operating", "Service", "IP", "Financing"


# Business Structure: Relationship between companies
class Relationship(BaseModel):
    """Relationship between companies in the business structure"""
    id: str
    source_id: str = Field(..., alias="sourceId")
    target_id: str = Field(..., alias="targetId")
    type: str  # "Ownership", "Service Agreement", "Licensing", "Financing"
    percentage: Optional[str] = None


# Legal Topic Data - nested structure for topic-specific questions
# This is a flexible structure that can hold any topic's questions
LegalTopicData = Dict[str, Dict[str, Any]]


# --- MAIN API "CONTRACT" ---
class MemoRequest(BaseModel):
    """
    Complete API contract matching the frontend input specification.
    All fields use Field(alias=...) for camelCase -> snake_case conversion.
    """
    
    # 1. Business Profile Section
    business_name: Optional[str] = Field(None, alias="businessName")
    industry: Optional[str] = None
    company_size: Optional[str] = Field(None, alias="companySize")
    current_markets: List[str] = Field(default_factory=list, alias="currentMarkets")
    entry_goals: List[str] = Field(default_factory=list, alias="entryGoals")
    timeline: Optional[str] = None
    
    # 2. Jurisdiction Section
    primary_jurisdiction: Optional[str] = Field(None, alias="primaryJurisdiction")
    secondary_jurisdictions: List[str] = Field(default_factory=list, alias="secondaryJurisdictions")
    tax_treaties: List[str] = Field(default_factory=list, alias="taxTreaties")
    
    # 3. Business Structure Section
    business_structure: Optional[str] = Field(None, alias="businessStructure")
    # Options: "simple", "holding", "ip-holding", "regional-hub"
    companies: Optional[List[Company]] = Field(default_factory=list)
    relationships: Optional[List[Relationship]] = Field(default_factory=list)
    
    # 4. Tax Considerations Section
    tax_queries: List[str] = Field(default_factory=list, alias="taxQueries")
    transaction_types: List[str] = Field(default_factory=list, alias="transactionTypes")
    specific_concerns: Optional[str] = Field(None, alias="specificConcerns")
    
    # 5. Legal Topics Section
    selected_legal_topics: Optional[List[str]] = Field(default_factory=list, alias="selectedLegalTopics")
    legal_topic_data: Optional[LegalTopicData] = Field(default_factory=dict, alias="legalTopicData")
    
    # 6. Entry Options Section (PLACEHOLDER - Always empty, but included for completeness)
    target_markets: List[str] = Field(default_factory=list, alias="targetMarkets")
    activities: List[str] = Field(default_factory=list, alias="activities")
    expected_revenue: Optional[str] = Field(None, alias="expectedRevenue")
    entry_option: Optional[str] = Field(None, alias="entryOption")
    compliance_priorities: List[str] = Field(default_factory=list, alias="compliancePriorities")
    
    # 7. Memo Metadata
    memo_name: Optional[str] = Field(None, alias="memoName")
    
    class Config:
        populate_by_name = True  # Allows both camelCase and snake_case
        json_schema_extra = {
            "example": {
                "businessName": "Tech Solutions Inc.",
                "industry": "Software & Technology",
                "companySize": "Medium (51-250 employees)",
                "currentMarkets": ["United States", "Canada"],
                "entryGoals": ["Sell products/services", "Tax optimization"],
                "timeline": "Medium-term (3-6 months)",
                "primaryJurisdiction": "Netherlands",
                "secondaryJurisdictions": ["Germany", "Belgium"],
                "taxTreaties": ["Netherlands-Germany", "Netherlands-Belgium"],
                "businessStructure": "holding",
                "companies": [
                    {
                        "id": "company-1234567890",
                        "name": "Tech Solutions Inc.",
                        "country": "United States",
                        "type": "Holding"
                    },
                    {
                        "id": "company-1234567891",
                        "name": "Tech Solutions B.V.",
                        "country": "Netherlands",
                        "type": "Operating"
                    }
                ],
                "relationships": [
                    {
                        "id": "rel-1234567890",
                        "sourceId": "company-1234567890",
                        "targetId": "company-1234567891",
                        "type": "Ownership",
                        "percentage": "100"
                    }
                ],
                "taxQueries": [
                    "Corporate income tax implications",
                    "VAT registration and compliance",
                    "Substance requirements"
                ],
                "transactionTypes": [
                    "Provision of services",
                    "Software licensing",
                    "E-commerce"
                ],
                "specificConcerns": "We want to minimize tax burden while maintaining full compliance with EU regulations.",
                "selectedLegalTopics": [
                    "corporate-law",
                    "employment-law",
                    "data-protection"
                ],
                "legalTopicData": {
                    "corporate-law": {
                        "entity-type": "Limited Liability Company",
                        "shelf-company": "No",
                        "local-directors": "Yes",
                        "setup-priority": "Both speed and capital"
                    },
                    "employment-law": {
                        "hire-employees": "Yes",
                        "employee-count": "10",
                        "remote-work": "Yes",
                        "employment-concerns": "Need to understand termination requirements"
                    },
                    "data-protection": {
                        "data-types": ["Customer data", "Employee data"],
                        "data-location": "EU servers only",
                        "gdpr-readiness": "Partially",
                        "data-concerns": "Want to ensure full GDPR compliance"
                    }
                },
                "memoName": "Tech Solutions - EU Market Entry Strategy"
            }
        }
