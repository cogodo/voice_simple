import os
import openai
from openai import OpenAI
import logging
from typing import List, Dict, Generator
from datetime import datetime

class ConversationManager:
    """Handles OpenAI LLM interactions with conversation context."""
    
    def __init__(self, logger=None):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        self.client = OpenAI(api_key=self.api_key)
        self.logger = logger or logging.getLogger(__name__)
        
        # Conversation context - stores message history
        self.conversation_history: List[Dict[str, str]] = [
            {
                "role": "system", 
                "content": "You are a helpful AI assistant having a voice conversation with a human. Keep your responses concise and natural for speech. Aim for responses that are 1-3 sentences unless the user specifically asks for more detail."
            }
        ]
        
        # Default model settings
        self.model = "gpt-4o-mini"  # Fast and cost-effective model
        self.max_tokens = 150  # Keep responses concise for voice
        self.temperature = 0.7  # Balanced creativity
    
    def get_current_timestamp(self) -> str:
        """Get current timestamp as a formatted string."""
        return datetime.now().isoformat()
    
    def add_user_message(self, text: str) -> None:
        """Add a user message to the conversation history."""
        self.conversation_history.append({"role": "user", "content": text})
        self.logger.info(f"User message added: '{text[:50]}...'")
    
    def add_assistant_message(self, text: str) -> None:
        """Add an assistant message to the conversation history."""
        self.conversation_history.append({"role": "assistant", "content": text})
        self.logger.info(f"Assistant message added: '{text[:50]}...'")
    
    def get_conversation_summary(self) -> str:
        """Get a summary of the conversation for logging/debugging."""
        return f"Conversation has {len(self.conversation_history)} messages"
    
    def clear_conversation(self, keep_system_prompt: bool = True) -> None:
        """Clear conversation history, optionally keeping the system prompt."""
        if keep_system_prompt and self.conversation_history:
            system_msg = self.conversation_history[0]
            self.conversation_history = [system_msg]
        else:
            self.conversation_history = []
        self.logger.info("Conversation history cleared")
    
    def get_streaming_response(self, user_text: str) -> Generator[str, None, None]:
        """
        Get a streaming response from OpenAI for the given user text.
        Yields text chunks as they arrive from the API.
        
        Args:
            user_text (str): The user's input text
            
        Yields:
            str: Text chunks from OpenAI's response
        """
        self.add_user_message(user_text)
        
        try:
            self.logger.info(f"Requesting streaming response from OpenAI for: '{user_text[:50]}...'")
            self.logger.debug(f"Conversation context: {len(self.conversation_history)} messages")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True  # Enable streaming
            )
            
            full_response = ""
            chunk_count = 0
            
            for chunk in response:
                chunk_count += 1
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    self.logger.debug(f"OpenAI chunk {chunk_count}: '{content}'")
                    yield content
                
                # Check if the response is finished
                if chunk.choices[0].finish_reason is not None:
                    self.logger.info(f"OpenAI response finished. Reason: {chunk.choices[0].finish_reason}")
                    break
            
            # Add the complete assistant response to conversation history
            if full_response:
                self.add_assistant_message(full_response)
                self.logger.info(f"Complete OpenAI response: '{full_response[:100]}...' ({len(full_response)} chars)")
            
        except Exception as e:
            error_msg = f"Error getting OpenAI response: {e}"
            self.logger.error(error_msg, exc_info=True)
            # Yield an error message that can be spoken
            yield f"I'm sorry, I encountered an error while processing your request. Please try again."
    
    def get_response(self, user_text: str) -> str:
        """
        Get a complete (non-streaming) response from OpenAI.
        Useful for testing or when streaming is not needed.
        
        Args:
            user_text (str): The user's input text
            
        Returns:
            str: Complete response from OpenAI
        """
        self.add_user_message(user_text)
        
        try:
            self.logger.info(f"Requesting response from OpenAI for: '{user_text[:50]}...'")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=self.conversation_history,
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            assistant_response = response.choices[0].message.content
            self.add_assistant_message(assistant_response)
            
            self.logger.info(f"OpenAI response: '{assistant_response[:100]}...' ({len(assistant_response)} chars)")
            return assistant_response
            
        except Exception as e:
            error_msg = f"Error getting OpenAI response: {e}"
            self.logger.error(error_msg, exc_info=True)
            return "I'm sorry, I encountered an error while processing your request. Please try again."

# Factory function for easy instantiation
def create_conversation_manager(logger=None) -> ConversationManager:
    """Create a ConversationManager instance with error handling."""
    try:
        return ConversationManager(logger)
    except ValueError as e:
        if logger:
            logger.error(f"Failed to create ConversationManager: {e}")
        raise

# For standalone testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
    logger = logging.getLogger(__name__)
    
    try:
        # Test the conversation manager
        manager = create_conversation_manager(logger)
        
        # Test non-streaming response
        logger.info("Testing non-streaming response...")
        response = manager.get_response("Hello, how are you?")
        print(f"Non-streaming response: {response}")
        
        # Test streaming response
        logger.info("Testing streaming response...")
        print("Streaming response: ", end="")
        for chunk in manager.get_streaming_response("Tell me a short joke"):
            print(chunk, end="", flush=True)
        print()  # New line after streaming
        
        # Show conversation summary
        print(f"\n{manager.get_conversation_summary()}")
        
    except Exception as e:
        logger.error(f"Error in standalone test: {e}", exc_info=True) 