#!/usr/bin/env python3
"""
Test script to verify the conversation pipeline is working.
"""
import socketio
import time
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Create a Socket.IO client
sio = socketio.Client()

@sio.event
def connect():
    logger.info("Connected to server")

@sio.event
def disconnect():
    logger.info("Disconnected from server")

@sio.event
def conversation_ready(data):
    logger.info(f"Conversation ready: {data}")

@sio.event
def conversation_error(data):
    logger.error(f"Conversation error: {data}")

@sio.event
def ai_thinking(data):
    logger.info(f"AI thinking: {data}")

@sio.event
def ai_response_complete(data):
    logger.info(f"AI response complete: {data}")

@sio.event
def tts_started(data):
    logger.info(f"TTS started: {data}")

@sio.event
def pcm_frame(data):
    logger.info(f"PCM frame received: {len(data)} bytes")

@sio.event
def tts_completed(data):
    logger.info(f"TTS completed: {data}")

@sio.event
def tts_error(data):
    logger.error(f"TTS error: {data}")

def main():
    try:
        # Connect to the server
        logger.info("Connecting to http://localhost:8000...")
        sio.connect('http://localhost:8000')
        
        # Wait for connection to be established
        time.sleep(2)
        
        # Test the conversation pipeline
        test_message = "What is 2 plus 2?"
        logger.info(f"Sending test message: '{test_message}'")
        sio.emit('conversation_text_input', {'text': test_message})
        
        # Wait for response
        logger.info("Waiting for response...")
        time.sleep(10)
        
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        sio.disconnect()

if __name__ == "__main__":
    main() 