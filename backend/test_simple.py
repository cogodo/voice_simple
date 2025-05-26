#!/usr/bin/env python3
"""
Simple test to verify the conversation manager is working.
"""
import os
import sys
sys.path.append('.')

from services.openai_handler import create_conversation_manager
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def test_conversation_manager():
    """Test the conversation manager directly."""
    try:
        logger.info("Testing conversation manager...")
        
        # Create conversation manager
        manager = create_conversation_manager(logger)
        logger.info("Conversation manager created successfully")
        
        # Test a simple conversation
        test_message = "What is 2 plus 2?"
        logger.info(f"Testing with message: '{test_message}'")
        
        response = manager.get_response(test_message)
        logger.info(f"Response: '{response}'")
        
        if response and "4" in response:
            logger.info("✅ Conversation manager is working correctly!")
            return True
        else:
            logger.error("❌ Unexpected response from conversation manager")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error testing conversation manager: {e}", exc_info=True)
        return False

def test_openai_key():
    """Test if OpenAI API key is configured."""
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        logger.info(f"✅ OPENAI_API_KEY is configured ({len(api_key)} characters)")
        return True
    else:
        logger.error("❌ OPENAI_API_KEY is not configured")
        return False

def main():
    logger.info("=== TESTING CONVERSATION PIPELINE ===")
    
    # Test OpenAI key
    if not test_openai_key():
        return
    
    # Test conversation manager
    if not test_conversation_manager():
        return
    
    logger.info("=== ALL TESTS PASSED ===")

if __name__ == "__main__":
    main() 