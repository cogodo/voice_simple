#!/usr/bin/env python3
"""
Test script to verify ChatGPT integration via WebSocket.
"""

import socketio
import time
import sys
import os
import unittest

# Add the backend directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestChatIntegration(unittest.TestCase):
    """Test cases for ChatGPT integration via WebSocket."""

    def setUp(self):
        """Set up test client."""
        self.sio = socketio.SimpleClient()
        self.backend_url = "http://localhost:8000"
        self.timeout = 15

    def tearDown(self):
        """Clean up after tests."""
        try:
            if self.sio.connected:
                self.sio.disconnect()
        except:
            pass

    def test_chat_integration(self):
        """Test the chat integration with the backend."""

        print(f"Connecting to backend at {self.backend_url}...")
        self.sio.connect(self.backend_url)
        self.assertTrue(self.sio.connected, "Failed to connect to backend")
        print("✓ Connected successfully!")

        # Send a test message
        test_message = "Hello! Can you tell me a short joke?"
        print(f'\n📤 Sending message: "{test_message}"')
        self.sio.emit("user_message", {"message": test_message})

        # Wait for response
        print("⏳ Waiting for AI response...")
        response = self._wait_for_ai_response()

        self.assertIsNotNone(response, "No AI response received")
        self.assertIsInstance(response, str, "AI response should be a string")
        self.assertGreater(len(response), 0, "AI response should not be empty")
        print(f"✓ AI Response: {response}")

    def test_multiple_messages(self):
        """Test multiple conversation turns."""

        self.sio.connect(self.backend_url)
        self.assertTrue(self.sio.connected)

        # First message
        self.sio.emit("user_message", {"message": "What is 2+2?"})
        response1 = self._wait_for_ai_response()
        self.assertIsNotNone(response1)
        print(f"✓ First response: {response1}")

        # Second message
        self.sio.emit("user_message", {"message": "What about 3+3?"})
        response2 = self._wait_for_ai_response()
        self.assertIsNotNone(response2)
        print(f"✓ Second response: {response2}")

        # Responses should be different
        self.assertNotEqual(response1, response2, "Responses should be different")

    def test_empty_message_handling(self):
        """Test handling of empty messages."""

        self.sio.connect(self.backend_url)
        self.assertTrue(self.sio.connected)

        # Send empty message
        self.sio.emit("user_message", {"message": ""})

        # Should receive an error
        error = self._wait_for_error()
        self.assertIsNotNone(error, "Should receive error for empty message")
        print(f"✓ Error handling: {error}")

    def _wait_for_ai_response(self):
        """Wait for AI response and return the message."""
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            try:
                event_data = self.sio.receive(timeout=1)
                if event_data:
                    event_name, data = event_data

                    if event_name == "ai_response":
                        return data.get("message", data.get("response", ""))
                    elif event_name == "conversation_error":
                        error = data.get("error", "Unknown error")
                        self.fail(f"Conversation error: {error}")
                    elif event_name == "ai_thinking":
                        print(f"⏳ {data.get('status', 'AI is thinking...')}")

            except socketio.exceptions.TimeoutError:
                continue
            except Exception as e:
                self.fail(f"Error during wait: {e}")

        return None

    def _wait_for_error(self):
        """Wait for conversation error and return the error message."""
        start_time = time.time()

        while time.time() - start_time < self.timeout:
            try:
                event_data = self.sio.receive(timeout=1)
                if event_data:
                    event_name, data = event_data

                    if event_name == "conversation_error":
                        return data.get("error", "Unknown error")
                    elif event_name == "ai_response":
                        # Unexpected response instead of error
                        return None

            except socketio.exceptions.TimeoutError:
                continue
            except Exception as e:
                self.fail(f"Error during wait: {e}")

        return None


def run_standalone_test():
    """Run a standalone test for manual verification."""

    print("🧪 Testing ChatGPT Integration via WebSocket")
    print("=" * 50)

    sio = socketio.SimpleClient()

    try:
        print("Connecting to backend at http://localhost:8000...")
        sio.connect("http://localhost:8000")
        print("✓ Connected successfully!")

        # Send a test message
        test_message = "Hello! Can you tell me a short joke?"
        print(f'\n📤 Sending message: "{test_message}"')
        sio.emit("user_message", {"message": test_message})

        # Wait for response
        print("⏳ Waiting for AI response...")
        timeout = 15
        responses_received = []

        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                event_data = sio.receive(timeout=1)
                if event_data:
                    event_name, data = event_data
                    print(f"📨 Received event: {event_name}")

                    if event_name == "ai_response":
                        message = data.get("message", data.get("response", ""))
                        responses_received.append(message)
                        print(f"✓ AI Response: {message}")
                        break
                    elif event_name == "conversation_error":
                        error = data.get("error", "Unknown error")
                        print(f"✗ Conversation Error: {error}")
                        return False
                    elif event_name == "ai_thinking":
                        status = data.get("status", "AI is thinking...")
                        print(f"⏳ {status}")
                    else:
                        print(f"📋 Other event: {event_name} - {data}")

            except socketio.exceptions.TimeoutError:
                continue
            except Exception as e:
                print(f"Error during wait: {e}")
                break

        if responses_received:
            print(f"\n✅ SUCCESS! Received response: {responses_received[0]}")
            return True
        else:
            print(f"\n❌ TIMEOUT: No response received within {timeout} seconds")
            return False

    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

    finally:
        try:
            sio.disconnect()
            print("\n🔌 Disconnected from backend")
        except:
            pass


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--standalone":
        # Run standalone test
        success = run_standalone_test()
        print("\n" + "=" * 50)
        if success:
            print("🎉 ChatGPT integration test PASSED!")
            sys.exit(0)
        else:
            print("💥 ChatGPT integration test FAILED!")
            sys.exit(1)
    else:
        # Run unittest
        unittest.main()
