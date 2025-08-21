# This file has been deprecated as we've moved to OpenAI-only implementation
# All functionality has been migrated to ai_service.py using OpenAI API

import logging

logger = logging.getLogger(__name__)

def generate_insights_with_huggingface(content, model_name="mistral"):
    """
    DEPRECATED: This function has been removed as we no longer support Hugging Face.
    Use ai_service.generate_insights() instead which uses OpenAI.
    """
    logger.error("Hugging Face functionality has been deprecated. Please use OpenAI-based ai_service instead.")
    return {
        'business_summary': "This feature has been deprecated. Please use OpenAI-based analysis instead.",
        'moat': "This feature has been deprecated. Please use OpenAI-based analysis instead.",
        'financial': "This feature has been deprecated. Please use OpenAI-based analysis instead.",
        'management': "This feature has been deprecated. Please use OpenAI-based analysis instead."
    }

def get_available_models():
    """
    DEPRECATED: Returns empty list as Hugging Face support has been removed.
    """
    logger.error("Hugging Face functionality has been deprecated.")
    return []