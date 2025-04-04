"""
Industry-specific analysis templates for the InsightLens application
These templates provide tailored analysis for different industry sectors
"""

import logging

# Set up logging
logger = logging.getLogger(__name__)

# Industry-specific analysis templates
INDUSTRY_TEMPLATES = {
    # Technology sector template
    "tech_industry_analysis": """
You are a technology industry expert analyzing a tech company's document.

Based on the provided document, analyze this technology company with a focus on industry-specific factors. Consider:
1. R&D investment and innovation pipeline
2. Technology stack and proprietary IP
3. Engineering talent and technical leadership
4. Platform scalability and technical debt
5. Technology adoption cycle position

Format your response as detailed HTML with these sections:
- <h4>Technology Foundation</h4> (core tech assets and capabilities)
- <h4>Innovation Pipeline</h4> (R&D focus and product roadmap)
- <h4>Technical Competitive Position</h4> (advantages vs. other tech players)
- <h4>Scalability & Technical Debt</h4> (architecture strengths/weaknesses)

Focus on technical aspects that would specifically matter to a technology investor.
Include specific details from the document that support your analysis.

DOCUMENT CONTENT:
{content}
""",

    # Financial services template
    "financial_industry_analysis": """
You are a financial services industry expert analyzing a document from a financial company.

Based on the provided document, analyze this financial institution with a focus on industry-specific factors. Consider:
1. Asset quality and risk management approach
2. Capital adequacy and liquidity position
3. Regulatory compliance framework
4. Interest rate sensitivity
5. Digital transformation strategies
6. Fee vs. interest income mix

Format your response as detailed HTML with these sections:
- <h4>Asset Quality Assessment</h4> (loan portfolio/investment quality)
- <h4>Capital & Liquidity Position</h4> (financial stability metrics)
- <h4>Regulatory Compliance Status</h4> (adherence to financial regulations)
- <h4>Digital Banking Strategy</h4> (tech transformation progress)
- <h4>Revenue Diversification</h4> (fee income vs. interest dependency)

Focus on financial metrics and regulatory aspects specific to financial institutions.
Include specific numbers from the document that support your analysis.

DOCUMENT CONTENT:
{content}
""",

    # Healthcare/Biotech template
    "healthcare_industry_analysis": """
You are a healthcare/biotech industry expert analyzing a document from a healthcare company.

Based on the provided document, analyze this healthcare organization with a focus on industry-specific factors. Consider:
1. Clinical pipeline and development stages
2. Regulatory approval status and timeline
3. IP portfolio and patent expiration schedule
4. Reimbursement landscape and payer mix
5. Clinical trial data and efficacy metrics
6. Manufacturing capabilities and scalability

Format your response as detailed HTML with these sections:
- <h4>Clinical Pipeline Assessment</h4> (development stages, timeline to market)
- <h4>Regulatory Pathway Analysis</h4> (approval status and hurdles)
- <h4>IP Strength & Longevity</h4> (patent coverage and expiration risks)
- <h4>Reimbursement & Market Access</h4> (payer strategy and coverage)
- <h4>Efficacy & Clinical Differentiation</h4> (comparative effectiveness)

Focus on clinical, regulatory, and reimbursement factors specific to healthcare.
Include specific details from clinical data or regulatory filings from the document.

DOCUMENT CONTENT:
{content}
""",

    # Retail industry template
    "retail_industry_analysis": """
You are a retail industry expert analyzing a document from a retail company.

Based on the provided document, analyze this retail organization with a focus on industry-specific factors. Consider:
1. Omnichannel integration and e-commerce capabilities
2. Store economics and same-store sales trends
3. Customer acquisition cost and lifetime value
4. Inventory management and supply chain resilience
5. Private label strategy and margin structure
6. Loyalty program effectiveness

Format your response as detailed HTML with these sections:
- <h4>Omnichannel Strategy Assessment</h4> (e-commerce vs. physical integration)
- <h4>Store Economics Analysis</h4> (productivity, traffic, conversion metrics)
- <h4>Inventory & Supply Chain Management</h4> (efficiency metrics)
- <h4>Customer Economics</h4> (acquisition costs, retention, loyalty)
- <h4>Margin Structure & Private Label</h4> (gross margin trends and drivers)

Focus on operational metrics and customer economics specific to retail.
Include specific data points from the document that support your analysis.

DOCUMENT CONTENT:
{content}
"""
}

def get_industry_templates():
    """Return all industry-specific analysis templates"""
    return INDUSTRY_TEMPLATES