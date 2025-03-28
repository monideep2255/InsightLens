import os
import json
import logging
from openai import OpenAI

logger = logging.getLogger(__name__)

# Initialize OpenAI client
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
openai = OpenAI(api_key=OPENAI_API_KEY)

# Prompt templates
PROMPT_TEMPLATES = {
    'business_summary': """
You are an expert business analyst reviewing a company document.

Based on the provided content, explain this company's business model in plain language.
- What do they sell or build?
- Who are their customers?
- What industry are they in?
- What problem do they solve?

Format your response as a concise, well-structured HTML that clearly explains what the company does.
Focus on objective facts from the document, not speculation.

DOCUMENT CONTENT:
{content}
""",

    'moat': """
You are a value investor assessing competitive advantages.

Based on the provided content, analyze whether the company has a durable competitive advantage (moat).
Consider these types of moats:
- Brand (consumer recognition and loyalty)
- Network Effects (service value increases with more users)
- Intellectual Property (patents, trademarks, trade secrets)
- Cost Advantage (economies of scale, proprietary technology)
- Switching Costs (difficult/expensive for customers to switch)
- Regulatory advantages

Format your response as HTML with these sections:
1. Type of Moat (or None Detected)
2. Justification (2-3 sentences)
3. Supporting Evidence (quote from document, if available)

Be honest if no clear moat is detected from the available information.

DOCUMENT CONTENT:
{content}
""",

    'financial': """
You are a financial analyst reviewing company documents.

Extract 3-5 key financial signals or ratios from the document. Focus specifically on:
- Revenue trend
- Debt levels
- Profitability or free cash flow
- Return on equity or assets (if mentioned)
- Gross margins or operating margins

Format your response as HTML with a concise bullet-point list of the financial metrics you found.
Include specific numbers when available, and note trends (increasing/decreasing).
If certain key financial information seems to be missing, note this as well.

DOCUMENT CONTENT:
{content}
""",

    'management': """
You are a governance expert evaluating company management.

Based on tone, quotes, and information in the document, what can you infer about the management team?
Consider:
- Leadership experience and track record
- Transparency in communication
- Alignment with shareholders
- Focus on long-term vs. short-term results
- Compensation structure (if mentioned)

Format your response as HTML with a concise assessment of management quality based only on what's in the document.
If there's insufficient information to make a judgment, clearly state that.

DOCUMENT CONTENT:
{content}
"""
}

def generate_insights(content):
    """
    Generate structured insights from document content using OpenAI GPT
    Returns a dictionary mapping insight categories to their content
    """
    insights = {}
    
    # Process each insight category with its own prompt
    for category, prompt_template in PROMPT_TEMPLATES.items():
        try:
            # Fill the prompt template with document content
            prompt = prompt_template.format(content=content[:15000])  # Limit content length
            
            # Make OpenAI API call
            # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
            # do not change this unless explicitly requested by the user
            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that helps analyze company documents using value investing principles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5,
                max_tokens=1000
            )
            
            # Extract the insight content from response
            insight_content = response.choices[0].message.content
            insights[category] = insight_content
            
            logger.info(f"Successfully generated {category} insight")
            
        except Exception as e:
            logger.error(f"Error generating {category} insight: {str(e)}")
            # Provide a fallback message for failed insights
            insights[category] = f"<p>Unable to generate {category} insight. Error: {str(e)}</p>"
    
    return insights
