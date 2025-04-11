#!/usr/bin/env python3
"""
Environment Variables Check Script for InsightLens

This script checks if required environment variables are set and attempts to 
validate API keys when possible. Use this script to verify your environment 
setup before running the application.

Usage:
    python check_env.py
"""

import os
import sys
import logging
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Required environment variables
REQUIRED_VARS = [
    'DATABASE_URL',  # Required for database connection
    'SESSION_SECRET'  # Required for Flask session security
]

# At least one of these API keys is required
ONE_REQUIRED_API_KEYS = [
    'HUGGINGFACE_API_KEY',
    'OPENAI_API_KEY'
]

# Optional environment variables with their default values
OPTIONAL_VARS = {
    'AI_MODEL_TYPE': 'huggingface',  # Default AI model type
    'HUGGINGFACE_MODEL': 'mistral',  # Default Hugging Face model
    'MONTHLY_API_BUDGET': '20.0'     # Default monthly budget (USD)
}

def check_required_vars() -> List[str]:
    """Check if required environment variables are set."""
    missing_vars = []
    for var in REQUIRED_VARS:
        if not os.environ.get(var):
            missing_vars.append(var)
    return missing_vars

def check_api_keys() -> Tuple[bool, List[str]]:
    """Check if at least one API key is set."""
    available_keys = []
    for key in ONE_REQUIRED_API_KEYS:
        if os.environ.get(key):
            available_keys.append(key)
    
    return len(available_keys) > 0, available_keys

def validate_huggingface_key() -> bool:
    """Attempt to validate Hugging Face API key."""
    api_key = os.environ.get('HUGGINGFACE_API_KEY')
    if not api_key:
        return False
    
    try:
        import requests
        # Make a simple API call to validate the key
        headers = {"Authorization": f"Bearer {api_key}"}
        response = requests.get(
            "https://api-inference.huggingface.co/models", 
            headers=headers
        )
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Error validating Hugging Face API key: {str(e)}")
        return False

def validate_openai_key() -> bool:
    """Attempt to validate OpenAI API key."""
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        return False
    
    try:
        # Only import if needed
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        # Make a lightweight request
        models = client.models.list(limit=1)
        return True
    except Exception as e:
        logger.error(f"Error validating OpenAI API key: {str(e)}")
        return False

def check_optional_vars() -> Dict[str, str]:
    """Check optional environment variables and their values."""
    var_status = {}
    for var, default_value in OPTIONAL_VARS.items():
        current_value = os.environ.get(var, default_value)
        var_status[var] = current_value
    return var_status

def check_database_url() -> bool:
    """Validate DATABASE_URL format."""
    db_url = os.environ.get('DATABASE_URL')
    if not db_url:
        return False
    
    # Check if it's a valid PostgreSQL URL
    if not db_url.startswith('postgresql://'):
        logger.warning("DATABASE_URL does not appear to be a PostgreSQL connection string")
        return False
    
    # Basic format check
    parts = db_url.split('://')
    if len(parts) != 2:
        return False
    
    try:
        # Attempt to connect (optional)
        import psycopg2
        conn = psycopg2.connect(db_url)
        conn.close()
        return True
    except ImportError:
        logger.warning("psycopg2 not available, skipping database connection test")
        return True
    except Exception as e:
        logger.error(f"Error connecting to database: {str(e)}")
        return False

def main():
    """Main function to check environment variables."""
    print("\n===== InsightLens Environment Check =====\n")
    
    # Check required variables
    missing_vars = check_required_vars()
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
    else:
        logger.info("✓ All required environment variables are set")
    
    # Check database URL
    if 'DATABASE_URL' not in missing_vars and check_database_url():
        logger.info("✓ DATABASE_URL is valid")
    elif 'DATABASE_URL' not in missing_vars:
        logger.warning("⚠ DATABASE_URL is set but may not be valid")
    
    # Check API keys
    has_api_key, available_keys = check_api_keys()
    if has_api_key:
        logger.info(f"✓ At least one API key is set: {', '.join(available_keys)}")
        
        # Validate Hugging Face API key if available
        if 'HUGGINGFACE_API_KEY' in available_keys:
            if validate_huggingface_key():
                logger.info("✓ Hugging Face API key is valid")
            else:
                logger.warning("⚠ Hugging Face API key is set but may not be valid")
        
        # Validate OpenAI API key if available
        if 'OPENAI_API_KEY' in available_keys:
            if validate_openai_key():
                logger.info("✓ OpenAI API key is valid")
            else:
                logger.warning("⚠ OpenAI API key is set but may not be valid")
    else:
        logger.error("✗ No API keys are set. At least one of the following is required: "
                   f"{', '.join(ONE_REQUIRED_API_KEYS)}")
    
    # Check optional variables
    print("\nOptional environment variables:")
    optional_vars = check_optional_vars()
    for var, value in optional_vars.items():
        # Don't print actual values, just indicate if they're set
        if os.environ.get(var):
            print(f"  ✓ {var}: Custom value set")
        else:
            print(f"  ℹ {var}: Using default ({value})")
    
    # Summarize
    print("\n===== Environment Check Summary =====")
    if missing_vars or not has_api_key:
        print("❌ Some required environment variables are missing.")
        print("   Please set them before running the application.")
        return 1
    else:
        print("✅ Environment appears to be configured correctly.")
        print("   The application should be able to start without environment issues.")
        return 0

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)