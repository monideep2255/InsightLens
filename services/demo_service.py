import json
import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Define sample insights for different company types
DEMO_INSIGHTS = {
    # Technology company insights
    "tech": {
        "business_summary": """
        <h3>Business Summary</h3>
        <p>This technology company specializes in developing and selling innovative hardware, software, and online services. Their main product categories include consumer electronics (smartphones, computers, wearables), cloud services, and digital content distribution platforms. They primarily target individual consumers and businesses across global markets.</p>
        <p>The company operates in the technology sector with a focus on premium product offerings and a vertically integrated ecosystem that combines hardware, software, and services.</p>
        """,
        
        "moat": """
        <h3>Competitive Advantages</h3>
        <h4>Type of Moat: Brand Value + Ecosystem Lock-in</h4>
        <p>The company has established two primary moats:</p>
        <ul>
            <li><strong>Powerful Brand Recognition:</strong> Their brand commands premium pricing and strong customer loyalty, allowing them to maintain higher margins than competitors.</li>
            <li><strong>Ecosystem Lock-in:</strong> Their integrated ecosystem of hardware, software, and services creates high switching costs for users who have invested in multiple products within their ecosystem.</li>
        </ul>
        <h4>Supporting Evidence:</h4>
        <blockquote>"Our customer satisfaction and loyalty rates remain exceptionally high, with customer retention above 90% in our core markets. This brand loyalty continues to drive repeat purchases across our expanding product lineup."</blockquote>
        """,
        
        "financial": """
        <h3>Financial Health</h3>
        <ul>
            <li><strong>Revenue Growth:</strong> Annual revenue of $365 billion, representing 8% year-over-year growth</li>
            <li><strong>Profitability:</strong> Operating margin of 30%, among the highest in the industry</li>
            <li><strong>Cash Position:</strong> $195 billion in cash and marketable securities</li>
            <li><strong>Debt Level:</strong> Long-term debt of $110 billion, well-covered by cash reserves</li>
            <li><strong>Capital Allocation:</strong> Aggressive share repurchase program and growing dividend payments</li>
        </ul>
        """,
        
        "management": """
        <h3>Management Assessment</h3>
        <p>The management team demonstrates a disciplined, long-term focused approach to business growth. Key observations:</p>
        <ul>
            <li>Strong emphasis on innovation with substantial R&D investments (8% of revenue)</li>
            <li>Disciplined capital allocation with balanced approach to reinvestment, acquisitions, and shareholder returns</li>
            <li>Clear succession planning with smooth executive transitions</li>
            <li>Compensation structure aligned with long-term performance metrics and shareholder returns</li>
        </ul>
        <p>Management communications are transparent about business challenges while maintaining optimistic but realistic growth projections.</p>
        """
    },
    
    # Financial company insights
    "financial": {
        "business_summary": """
        <h3>Business Summary</h3>
        <p>This financial institution operates a diversified banking business with four main segments: Consumer Banking, Commercial Banking, Investment Banking, and Wealth Management. The company provides a comprehensive range of financial services including deposit accounts, loans, credit cards, mortgages, investment products, and advisory services.</p>
        <p>Their customer base spans individuals, small businesses, corporations, institutions, and governments across multiple countries, with primary operations concentrated in North America and Europe.</p>
        """,
        
        "moat": """
        <h3>Competitive Advantages</h3>
        <h4>Type of Moat: Regulatory + Scale</h4>
        <p>The company has established two primary moats:</p>
        <ul>
            <li><strong>Regulatory Barrier:</strong> Banking licenses and regulatory compliance create high barriers to entry, particularly for their investment banking operations.</li>
            <li><strong>Scale Advantages:</strong> Their large customer base and asset size create cost advantages in operations, technology infrastructure, and funding costs.</li>
        </ul>
        <h4>Supporting Evidence:</h4>
        <blockquote>"Our deposit base of over $1.2 trillion provides stable, low-cost funding that significantly improves our net interest margin compared to smaller competitors. Additionally, our regulatory technology investments have created compliance capabilities that smaller institutions struggle to match."</blockquote>
        """,
        
        "financial": """
        <h3>Financial Health</h3>
        <ul>
            <li><strong>Revenue:</strong> $128 billion annual revenue with 6% growth year-over-year</li>
            <li><strong>Net Interest Margin:</strong> 2.8%, improving by 0.2% from previous year</li>
            <li><strong>Efficiency Ratio:</strong> 58%, indicating good cost control</li>
            <li><strong>Capital Ratio:</strong> 13.2% CET1 ratio, well above regulatory requirements</li>
            <li><strong>Return on Assets:</strong> 1.3%, consistent with industry leaders</li>
            <li><strong>Loan Loss Reserves:</strong> Increased to 2.1% of total loan portfolio</li>
        </ul>
        """,
        
        "management": """
        <h3>Management Assessment</h3>
        <p>The management team demonstrates a conservative approach to risk balanced with growth initiatives. Key observations:</p>
        <ul>
            <li>Disciplined risk management with clear credit underwriting standards</li>
            <li>Proactive investment in digital transformation to reduce branch costs while improving customer experience</li>
            <li>Focus on fee-based income streams to reduce reliance on interest rate spreads</li>
            <li>Compensation tied to risk-adjusted performance metrics and regulatory compliance</li>
        </ul>
        <p>Leadership communications emphasize stability and prudent growth rather than aggressive expansion, appropriate for a financial institution of this size.</p>
        """
    },
    
    # Retail company insights
    "retail": {
        "business_summary": """
        <h3>Business Summary</h3>
        <p>This retail company operates a multi-channel business selling consumer products through physical stores, e-commerce platforms, and marketplace partnerships. Their product categories include groceries, general merchandise, electronics, apparel, and home goods with both private label and national brands.</p>
        <p>The company primarily targets middle-income consumers across North America, with an expanding international presence. They operate approximately 4,800 stores alongside a rapidly growing e-commerce business that now represents 24% of total sales.</p>
        """,
        
        "moat": """
        <h3>Competitive Advantages</h3>
        <h4>Type of Moat: Scale + Distribution Network</h4>
        <p>The company has established two primary moats:</p>
        <ul>
            <li><strong>Massive Scale:</strong> Their purchasing power and logistics volume create significant cost advantages that enable everyday low pricing while maintaining margins.</li>
            <li><strong>Distribution Network:</strong> Their integrated network of stores, distribution centers, and last-mile delivery infrastructure creates a fulfillment advantage that's difficult to replicate.</li>
        </ul>
        <h4>Supporting Evidence:</h4>
        <blockquote>"Our ability to place merchandise within 10 miles of 90% of the U.S. population creates a fulfillment advantage that enables same-day delivery options that few competitors can match at our scale and cost structure."</blockquote>
        """,
        
        "financial": """
        <h3>Financial Health</h3>
        <ul>
            <li><strong>Revenue:</strong> $615 billion annual revenue with 4.2% growth year-over-year</li>
            <li><strong>Comparable Store Sales:</strong> Increased 3.7% year-over-year</li>
            <li><strong>E-commerce Growth:</strong> 18% year-over-year increase</li>
            <li><strong>Operating Margin:</strong> 4.3%, reflecting the traditionally thin margins of retail</li>
            <li><strong>Inventory Turnover:</strong> 8.5 times annually, improving efficiency</li>
            <li><strong>Free Cash Flow:</strong> $18.5 billion, enabling significant shareholder returns</li>
        </ul>
        """,
        
        "management": """
        <h3>Management Assessment</h3>
        <p>The management team demonstrates a balanced approach to maintaining core retail strength while investing in digital transformation. Key observations:</p>
        <ul>
            <li>Clear focus on omnichannel integration rather than treating stores and e-commerce as separate businesses</li>
            <li>Disciplined capital allocation with emphasis on supply chain modernization</li>
            <li>Increased investment in employee wages and training to reduce turnover</li>
            <li>Data-driven decision making with advanced analytics capabilities</li>
        </ul>
        <p>Management communications are straightforward about competitive challenges from both discount and premium retailers, with specific strategies to address each segment.</p>
        """
    },
    
    # Manufacturing company insights
    "manufacturing": {
        "business_summary": """
        <h3>Business Summary</h3>
        <p>This manufacturing company designs, produces, and distributes industrial equipment and components for multiple sectors including aerospace, automotive, energy, and construction. Their product portfolio includes specialized machinery, precision components, control systems, and aftermarket parts and services.</p>
        <p>The company primarily serves industrial customers, OEMs, and distributors across global markets, with manufacturing facilities in 12 countries and sales in over 100 markets worldwide.</p>
        """,
        
        "moat": """
        <h3>Competitive Advantages</h3>
        <h4>Type of Moat: Intellectual Property + Switching Costs</h4>
        <p>The company has established two primary moats:</p>
        <ul>
            <li><strong>Patent Portfolio:</strong> Their extensive patent portfolio (over 3,200 active patents) protects proprietary technology and manufacturing processes that enable superior product performance.</li>
            <li><strong>Switching Costs:</strong> Their components are designed into customer products and production systems, creating high switching costs once integrated into manufacturing processes or product designs.</li>
        </ul>
        <h4>Supporting Evidence:</h4>
        <blockquote>"Our customer retention rate exceeds 95% in our core markets, with an average relationship duration of 14 years among our top 100 customers. This stability reflects the mission-critical nature of our components and the significant requalification costs involved in switching suppliers."</blockquote>
        """,
        
        "financial": """
        <h3>Financial Health</h3>
        <ul>
            <li><strong>Revenue:</strong> $38.5 billion annual revenue with 3.1% growth year-over-year</li>
            <li><strong>Gross Margin:</strong> 34.8%, reflecting premium positioning within industrial segments</li>
            <li><strong>Recurring Revenue:</strong> 42% of sales from aftermarket parts and services</li>
            <li><strong>EBITDA Margin:</strong> 18.5%, consistent with industry leaders</li>
            <li><strong>Return on Invested Capital:</strong> 16.3%, significantly above cost of capital</li>
            <li><strong>Debt-to-EBITDA Ratio:</strong> 1.8x, indicating conservative leverage</li>
        </ul>
        """,
        
        "management": """
        <h3>Management Assessment</h3>
        <p>The management team demonstrates a long-term orientation with focus on sustainable competitive advantages. Key observations:</p>
        <ul>
            <li>Experienced leadership with deep industry expertise and engineering backgrounds</li>
            <li>Significant R&D investment at 6.5% of sales, well above industry average</li>
            <li>Disciplined acquisition strategy focusing on technology capabilities and adjacent markets</li>
            <li>Emphasis on operational excellence with continuous improvement methodologies</li>
        </ul>
        <p>Leadership communications highlight both cyclical industry challenges and structural growth drivers, with clear strategies to manage both aspects of their business environment.</p>
        """
    }
}

def generate_demo_insights(document_id, company_type="tech"):
    """
    Generate demo insights without making API calls
    
    Args:
        document_id: The ID of the document
        company_type: The type of company to generate insights for (tech, financial, retail, manufacturing)
    
    Returns:
        dict: A dictionary of insights by category
    """
    # Log that we're using demo mode
    logger.info(f"Generating demo insights for document {document_id} using {company_type} template")
    
    # Get the appropriate template
    template = DEMO_INSIGHTS.get(company_type.lower(), DEMO_INSIGHTS["tech"])
    
    # Return all the insights
    return template


def perform_local_analysis(content):
    """
    Perform rule-based local analysis without using AI APIs
    
    This uses simple text pattern matching to extract insights from the document
    
    Args:
        content: The document content to analyze
        
    Returns:
        dict: A dictionary of insights by category
    """
    logger.info("Performing local rule-based analysis without AI APIs")
    
    # Convert to lowercase for easier pattern matching
    content_lower = content.lower()
    
    # Initialize insights dictionary
    insights = {
        "business_summary": "<h3>Business Summary</h3>",
        "moat": "<h3>Competitive Advantages</h3>",
        "financial": "<h3>Financial Health</h3>",
        "management": "<h3>Management Assessment</h3>"
    }
    
    # --- Business Summary Analysis ---
    business_desc = "<p>Based on document analysis, this company "
    
    # Check for business type indicators
    if any(word in content_lower for word in ["software", "hardware", "technology", "digital", "app", "platform"]):
        business_desc += "appears to operate in the technology sector, "
        if "software" in content_lower:
            business_desc += "developing software products"
        elif "hardware" in content_lower:
            business_desc += "producing hardware devices"
        else:
            business_desc += "providing technology solutions"
    elif any(word in content_lower for word in ["bank", "loan", "deposit", "financial", "investment", "insurance"]):
        business_desc += "operates in the financial services industry, "
        if "bank" in content_lower:
            business_desc += "offering banking services"
        elif "insurance" in content_lower:
            business_desc += "providing insurance products"
        else:
            business_desc += "delivering financial services"
    elif any(word in content_lower for word in ["retail", "store", "shop", "merchandise", "consumer", "product"]):
        business_desc += "is in the retail sector, "
        business_desc += "selling consumer products"
    elif any(word in content_lower for word in ["manufacture", "production", "factory", "industrial", "equipment"]):
        business_desc += "is involved in manufacturing, "
        business_desc += "producing industrial goods"
    else:
        business_desc += "operates across multiple sectors"
    
    business_desc += ".</p>"
    
    # Add customer information if found
    if "customer" in content_lower or "client" in content_lower:
        business_desc += "<p>The company serves "
        if any(word in content_lower for word in ["consumer", "individual", "retail customer"]):
            business_desc += "individual consumers"
        elif any(word in content_lower for word in ["business", "enterprise", "corporate", "company"]):
            business_desc += "business clients"
        elif any(word in content_lower for word in ["government", "public sector"]):
            business_desc += "government entities"
        else:
            business_desc += "various customer segments"
        business_desc += ".</p>"
    
    insights["business_summary"] += business_desc
    
    # --- Moat Analysis ---
    moat_desc = "<p>Potential competitive advantages identified in the document:</p><ul>"
    
    # Check for different types of moats
    moats_found = False
    
    # Brand
    if any(word in content_lower for word in ["brand", "reputation", "recognition", "loyalty"]):
        moat_desc += "<li><strong>Brand Advantage:</strong> The company appears to have brand recognition or customer loyalty.</li>"
        moats_found = True
    
    # Network Effects
    if any(phrase in content_lower for phrase in ["network effect", "platform advantage", "user base", "marketplace"]):
        moat_desc += "<li><strong>Network Effects:</strong> The company may benefit from network effects through its platform or user base.</li>"
        moats_found = True
    
    # IP
    if any(word in content_lower for word in ["patent", "intellectual property", "trademark", "proprietary", "copyright"]):
        moat_desc += "<li><strong>Intellectual Property:</strong> The company has patents or other intellectual property protections.</li>"
        moats_found = True
    
    # Scale
    if any(phrase in content_lower for phrase in ["economies of scale", "scale advantage", "market share", "largest", "leading"]):
        moat_desc += "<li><strong>Scale Advantage:</strong> The company benefits from economies of scale or market leadership.</li>"
        moats_found = True
    
    # Switching Costs
    if any(phrase in content_lower for phrase in ["switching cost", "lock-in", "retention", "recurring", "subscription"]):
        moat_desc += "<li><strong>Switching Costs:</strong> Customers face costs or difficulties in switching to competitors.</li>"
        moats_found = True
    
    # Regulatory
    if any(word in content_lower for word in ["regulation", "compliance", "license", "permit", "regulatory"]):
        moat_desc += "<li><strong>Regulatory Advantages:</strong> The company benefits from regulatory barriers to entry.</li>"
        moats_found = True
    
    if not moats_found:
        moat_desc += "<li>No clear competitive advantages were identified in the document.</li>"
    
    moat_desc += "</ul>"
    insights["moat"] += moat_desc
    
    # --- Financial Analysis ---
    financial_desc = "<p>Financial indicators extracted from the document:</p><ul>"
    
    # Look for revenue information
    revenue_found = False
    for financial_term in ["revenue", "sales", "turnover"]:
        if financial_term in content_lower:
            # Look for nearby numbers
            start_pos = content_lower.find(financial_term)
            context = content[max(0, start_pos-50):min(len(content), start_pos+100)]
            financial_desc += f"<li><strong>Revenue:</strong> Mentioned in the document. Full context: \"{context}\"</li>"
            revenue_found = True
            break
    
    if not revenue_found:
        financial_desc += "<li><strong>Revenue:</strong> No specific information found.</li>"
    
    # Look for profit information
    profit_found = False
    for profit_term in ["profit", "earnings", "net income", "ebitda", "margin"]:
        if profit_term in content_lower:
            start_pos = content_lower.find(profit_term)
            context = content[max(0, start_pos-50):min(len(content), start_pos+100)]
            financial_desc += f"<li><strong>Profitability:</strong> Mentioned in the document. Full context: \"{context}\"</li>"
            profit_found = True
            break
    
    if not profit_found:
        financial_desc += "<li><strong>Profitability:</strong> No specific information found.</li>"
    
    # Look for debt information
    debt_found = False
    for debt_term in ["debt", "leverage", "loan", "borrowing", "liability"]:
        if debt_term in content_lower:
            start_pos = content_lower.find(debt_term)
            context = content[max(0, start_pos-50):min(len(content), start_pos+100)]
            financial_desc += f"<li><strong>Debt:</strong> Mentioned in the document. Full context: \"{context}\"</li>"
            debt_found = True
            break
    
    if not debt_found:
        financial_desc += "<li><strong>Debt:</strong> No specific information found.</li>"
    
    financial_desc += "</ul>"
    insights["financial"] += financial_desc
    
    # --- Management Analysis ---
    management_desc = "<p>Management information extracted from the document:</p><ul>"
    
    # Look for management mentions
    management_found = False
    for mgmt_term in ["ceo", "chief executive", "president", "chairman", "director", "leadership", "management team"]:
        if mgmt_term in content_lower:
            start_pos = content_lower.find(mgmt_term)
            context = content[max(0, start_pos-50):min(len(content), start_pos+150)]
            management_desc += f"<li><strong>Leadership:</strong> Management mentioned in the document. Full context: \"{context}\"</li>"
            management_found = True
            break
    
    if not management_found:
        management_desc += "<li><strong>Leadership:</strong> No specific information found about management team.</li>"
    
    # Look for strategy mentions
    strategy_found = False
    for strategy_term in ["strategy", "vision", "mission", "goal", "plan", "objective"]:
        if strategy_term in content_lower:
            start_pos = content_lower.find(strategy_term)
            context = content[max(0, start_pos-50):min(len(content), start_pos+150)]
            management_desc += f"<li><strong>Strategy:</strong> Business strategy mentioned in the document. Full context: \"{context}\"</li>"
            strategy_found = True
            break
    
    if not strategy_found:
        management_desc += "<li><strong>Strategy:</strong> No specific information found about business strategy.</li>"
    
    management_desc += "</ul>"
    insights["management"] += management_desc
    
    return insights


# List of SEC CIK and ticker symbols for quick access
SEC_QUICK_ACCESS = [
    {"name": "Apple Inc.", "cik": "0000320193", "ticker": "AAPL"},
    {"name": "Microsoft Corporation", "cik": "0000789019", "ticker": "MSFT"},
    {"name": "Amazon.com, Inc.", "cik": "0001018724", "ticker": "AMZN"},
    {"name": "Alphabet Inc. (Google)", "cik": "0001652044", "ticker": "GOOGL"},
    {"name": "Meta Platforms, Inc. (Facebook)", "cik": "0001326801", "ticker": "META"},
    {"name": "Tesla, Inc.", "cik": "0001318605", "ticker": "TSLA"},
    {"name": "Berkshire Hathaway Inc.", "cik": "0001067983", "ticker": "BRK.A"},
    {"name": "JPMorgan Chase & Co.", "cik": "0000019617", "ticker": "JPM"},
    {"name": "Johnson & Johnson", "cik": "0000200406", "ticker": "JNJ"},
    {"name": "Walmart Inc.", "cik": "0000104169", "ticker": "WMT"}
]

def get_latest_10k_url(cik):
    """
    Get the URL for the latest 10-K filing for a company by CIK
    """
    # Strip leading zeros from CIK
    cik = cik.lstrip('0')
    
    # Format the URL to the latest 10-K
    form_type = "10-K"
    url = f"https://www.sec.gov/Archives/edgar/data/{cik}/index.json"
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/", cik