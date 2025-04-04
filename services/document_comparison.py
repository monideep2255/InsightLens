"""
Document comparison service for InsightLens

This module provides functionality to compare multiple documents (e.g., annual reports 
from different years) and generate insights about changes over time.
"""

import os
import logging
import time
from datetime import datetime
from models import Document, Insight, db

# Set up logging
logger = logging.getLogger(__name__)

def compare_documents(doc_ids):
    """
    Compare multiple documents and generate insights about changes over time
    
    Args:
        doc_ids (list): List of document IDs to compare
        
    Returns:
        dict: Comparison insights by category
    """
    if not doc_ids or len(doc_ids) < 2:
        logger.error("Cannot compare fewer than 2 documents")
        return {"error": "Please select at least 2 documents to compare"}
    
    # Retrieve the documents and verify they exist
    documents = Document.query.filter(Document.id.in_(doc_ids)).all()
    if len(documents) != len(doc_ids):
        logger.error(f"Not all document IDs were found: requested {len(doc_ids)}, found {len(documents)}")
        return {"error": "One or more selected documents were not found"}
    
    # Extract contents and metadata for each document
    doc_data = []
    for doc in documents:
        # Get the existing insights for this document
        insights = Insight.query.filter_by(document_id=doc.id).all()
        
        # Check if we have the necessary insights for comparison
        if not insights:
            logger.error(f"Document {doc.id} has no insights to compare")
            return {"error": f"Document '{doc.filename or doc.title or f'ID: {doc.id}'}' has no insights to compare"}
        
        # Group insights by category
        insights_by_category = {}
        for insight in insights:
            insights_by_category[insight.category] = insight.content
        
        # Add to document data collection
        doc_data.append({
            "id": doc.id,
            "title": doc.title or doc.filename or f"Document {doc.id}",
            "date": doc.created_at,
            "insights": insights_by_category
        })
    
    # Sort documents by date
    doc_data.sort(key=lambda x: x["date"])
    
    # Perform comparison using specialized AI templates
    comparison_results = generate_comparison_insights(doc_data)
    
    return comparison_results

def generate_comparison_insights(doc_data):
    """
    Generate comparison insights using AI analysis
    
    Args:
        doc_data (list): List of document data including their insights
        
    Returns:
        dict: Comparison insights by category
    """
    try:
        # Check for either OpenAI or Hugging Face API
        if not (os.environ.get("OPENAI_API_KEY") or os.environ.get("HUGGINGFACE_API_KEY")):
            logger.error("No API keys available for comparison analysis")
            return {"error": "No AI API keys configured for comparison analysis"}
        
        # Prepare prompts for different comparison categories
        comparison_results = {}
        
        # Create a structured representation of the document data for the AI prompt
        docs_representation = format_documents_for_comparison(doc_data)
        
        # Define the categories to compare
        categories_to_compare = [
            "financial_comparison",
            "business_evolution",
            "management_changes",
            "strategic_shifts"
        ]
        
        # Import AI service
        from services.ai_service import get_openai_client, PROMPT_TEMPLATES
        
        # Process each comparison category
        for category in categories_to_compare:
            prompt_template = get_comparison_prompt(category)
            
            if not prompt_template:
                logger.warning(f"No template found for comparison category: {category}")
                comparison_results[category] = f"<p>No template configured for {category}</p>"
                continue
            
            # Format the prompt with the document data
            prompt = prompt_template.format(documents=docs_representation)
            
            # Try with OpenAI first
            if os.environ.get("OPENAI_API_KEY"):
                try:
                    # the newest OpenAI model is "gpt-4o" which was released May 13, 2024.
                    # do not change this unless explicitly requested by the user
                    client = get_openai_client()
                    if client:
                        response = client.chat.completions.create(
                            model="gpt-4o",
                            messages=[
                                {"role": "system", "content": "You are a financial analyst comparing company documents across different time periods."},
                                {"role": "user", "content": prompt}
                            ],
                            temperature=0.3,
                            max_tokens=1000
                        )
                        
                        comparison_results[category] = response.choices[0].message.content
                        logger.info(f"Generated {category} comparison with OpenAI")
                        continue
                except Exception as e:
                    logger.error(f"OpenAI comparison failed for {category}: {str(e)}")
                    # Fall through to Hugging Face
            
            # Try with Hugging Face if OpenAI failed or isn't available
            if os.environ.get("HUGGINGFACE_API_KEY"):
                try:
                    from services.open_source_ai import analyze_with_prompt
                    result = analyze_with_prompt(docs_representation, prompt)
                    comparison_results[category] = result
                    logger.info(f"Generated {category} comparison with Hugging Face")
                    continue
                except Exception as e:
                    logger.error(f"Hugging Face comparison failed for {category}: {str(e)}")
            
            # If we get here, both methods failed
            comparison_results[category] = f"<p>Unable to generate {category} comparison. Please try again later.</p>"
        
        return comparison_results
        
    except Exception as e:
        logger.error(f"Error generating comparison insights: {str(e)}")
        return {"error": f"Failed to generate comparison: {str(e)}"}

def format_documents_for_comparison(doc_data):
    """
    Format document data for inclusion in an AI prompt
    
    Args:
        doc_data (list): List of document data including their insights
        
    Returns:
        str: Formatted document data for comparison
    """
    formatted_text = "DOCUMENTS TO COMPARE:\n\n"
    
    for i, doc in enumerate(doc_data):
        # Format date for display
        date_str = doc["date"].strftime("%Y-%m-%d") if isinstance(doc["date"], datetime) else str(doc["date"])
        
        formatted_text += f"DOCUMENT {i+1}: {doc['title']} (Date: {date_str})\n"
        formatted_text += "=" * 50 + "\n"
        
        # Add insights from each category
        formatted_text += "BUSINESS SUMMARY:\n"
        formatted_text += doc["insights"].get("business_summary", "Not available") + "\n\n"
        
        formatted_text += "FINANCIAL METRICS:\n"
        formatted_text += doc["insights"].get("financial", "Not available") + "\n\n"
        
        formatted_text += "MANAGEMENT:\n"
        formatted_text += doc["insights"].get("management", "Not available") + "\n\n"
        
        formatted_text += "COMPETITIVE POSITION:\n"
        formatted_text += doc["insights"].get("moat", "Not available") + "\n\n"
        
        # Add optional insights if available
        for category, content in doc["insights"].items():
            if category not in ["business_summary", "financial", "management", "moat"]:
                formatted_text += f"{category.upper()}:\n"
                formatted_text += content + "\n\n"
        
        formatted_text += "\n" + "=" * 50 + "\n\n"
    
    return formatted_text

def get_comparison_prompt(category):
    """
    Get the prompt template for a specific comparison category
    
    Args:
        category (str): The comparison category
        
    Returns:
        str: The prompt template
    """
    # Comparison prompt templates
    COMPARISON_PROMPTS = {
        "financial_comparison": """
You are a financial analyst comparing a company's financial performance across different time periods.

Based on the information in these documents, analyze how the company's financial metrics have changed over time.
Focus on:
1. Revenue and profit trends
2. Margin evolution (gross, operating, net)
3. Debt and leverage changes
4. Return on capital trends
5. Cash flow patterns

Format your response in well-structured HTML with these sections:
- <h4>Financial Trend Summary</h4> (Overall trajectory of financial health)
- <h4>Key Metrics Comparison</h4> (Table or bullet points showing important metrics across periods)
- <h4>Notable Financial Changes</h4> (Significant shifts in financial performance)
- <h4>Red Flags or Improvements</h4> (Concerning or positive financial developments)

Whenever possible, use specific numbers and percentages from the documents to support your analysis.
Explain what the changes may indicate about the company's financial trajectory.

{documents}
""",

        "business_evolution": """
You are a business strategist comparing how a company's business model and operations have evolved over time.

Based on the information in these documents, analyze how the company's business has changed across periods.
Focus on:
1. Core business model evolution
2. Product/service offering changes
3. Market positioning shifts
4. Customer base or target market changes
5. Geographic expansion or contraction

Format your response in well-structured HTML with these sections:
- <h4>Business Evolution Summary</h4> (Overall trajectory of business changes)
- <h4>Product/Service Portfolio Changes</h4> (How offerings have evolved)
- <h4>Market Position Shifts</h4> (Changes in competitive positioning)
- <h4>Strategic Pivots</h4> (Major strategic changes, if any)

Provide specific examples from the documents whenever possible to illustrate the evolution.
Analyze whether these changes appear to strengthen or weaken the company's position.

{documents}
""",

        "management_changes": """
You are a corporate governance expert comparing changes in a company's management approach over time.

Based on the information in these documents, analyze how the company's leadership and governance have evolved.
Focus on:
1. Leadership personnel changes
2. Management tone and communication style shifts
3. Capital allocation priority changes
4. Compensation structure evolution
5. Corporate governance modifications

Format your response in well-structured HTML with these sections:
- <h4>Management Evolution Summary</h4> (Overall changes in leadership approach)
- <h4>Leadership Transitions</h4> (Key personnel changes and their potential impact)
- <h4>Shareholder Alignment Trends</h4> (How management's alignment with shareholders has changed)
- <h4>Communication Style Shifts</h4> (Changes in transparency and messaging)

Quote specific statements from management across the different periods when relevant.
Assess whether changes appear positive or concerning from a shareholder perspective.

{documents}
""",

        "strategic_shifts": """
You are a strategic analyst comparing a company's strategic direction across different time periods.

Based on the information in these documents, analyze how the company's strategy has evolved.
Focus on:
1. Long-term vision changes
2. Strategic priorities shifts
3. Competitive positioning changes
4. Investment focus modifications
5. Risk appetite evolution

Format your response in well-structured HTML with these sections:
- <h4>Strategic Evolution Summary</h4> (Overall trajectory of strategy changes)
- <h4>Core Focus Shifts</h4> (How strategic emphasis has changed)
- <h4>Competitive Strategy Changes</h4> (Evolution in how the company competes)
- <h4>Investment Priority Changes</h4> (Shifts in where capital is being deployed)
- <h4>Strategic Consistency Assessment</h4> (How consistent the company has been with its strategy)

Provide specific examples from the documents to illustrate strategic evolutions.
Assess whether strategic changes appear coherent and value-creating.

{documents}
"""
    }
    
    return COMPARISON_PROMPTS.get(category)