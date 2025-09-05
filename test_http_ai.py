#!/usr/bin/env python3
"""
Test script for the HTTP-based AI implementation.
"""

import os
from pycaps.ai.gpt import Gpt

def test_http_ai():
    """Test the HTTP-based AI implementation."""
    
    # Check if API key is set
    if not os.getenv("OPENAI_API_KEY"):
        print("ERROR: OPENAI_API_KEY environment variable not set!")
        print("Please set your OpenAI API key:")
        print("export OPENAI_API_KEY='your-key-here'")
        return False
    
    try:
        # Create GPT instance
        gpt = Gpt()
        
        # Test basic functionality
        if not gpt.is_enabled():
            print("ERROR: AI is not enabled!")
            return False
        
        print("Testing HTTP-based AI implementation...")
        
        # Test simple message
        test_prompt = "List 3 important words from this text: 'You need to understand that your life has tremendous value.'"
        
        print(f"Sending test prompt: {test_prompt}")
        
        response = gpt.send_message(test_prompt)
        
        print(f"Response received: {response}")
        
        if response and len(response.strip()) > 0:
            print("✅ HTTP-based AI implementation working correctly!")
            return True
        else:
            print("❌ Empty or invalid response from API")
            return False
            
    except Exception as e:
        print(f"❌ Error testing HTTP AI implementation: {e}")
        return False

if __name__ == "__main__":
    success = test_http_ai()
    if success:
        print("\n🎉 HTTP-based OpenAI API implementation is working!")
        print("You can now use pycaps with AI features without the openai package dependency.")
    else:
        print("\n❌ HTTP-based implementation test failed.")
        print("Please check your API key and network connection.")