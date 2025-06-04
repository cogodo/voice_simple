#!/usr/bin/env python3
"""
Direct test of Cartesia API to understand response structure
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from cartesia import Cartesia
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def test_cartesia_direct():
    """Test Cartesia SSE API directly"""
    try:
        api_key = os.getenv("CARTESIA_API_KEY")
        if not api_key:
            print("❌ CARTESIA_API_KEY not set")
            return False

        print(f"✅ API Key found: {api_key[:10]}...")

        client = Cartesia(api_key=api_key)
        text = "Hello, this is a test"

        print(f"🎯 Testing with text: '{text}'")

        # Test SSE response
        print("📡 Making SSE request...")
        response = client.tts.sse(
            model_id="sonic-english",
            transcript=text,
            voice={"mode": "id", "id": "b7d50908-b17c-442d-ad8d-810c63997ed9"},
            output_format={
                "container": "raw",
                "encoding": "pcm_f32le",
                "sample_rate": 22050,
            },
        )

        print(f"📋 Response type: {type(response)}")
        print(f"📋 Response dir: {dir(response)}")

        chunk_count = 0
        total_bytes = 0

        print("🔄 Processing response...")
        for item in response:
            chunk_count += 1
            print(f"📦 Item {chunk_count}: {type(item)}")
            print(f"📦 Item dir: {dir(item)}")

            if hasattr(item, "data"):
                print(f"📦 Item.data type: {type(item.data)}")
                if isinstance(item.data, bytes):
                    total_bytes += len(item.data)
                    print(f"📦 Audio chunk: {len(item.data)} bytes")
                else:
                    print(f"📦 Data content: {item.data}")

            if hasattr(item, "type"):
                print(f"📦 Item.type: {item.type}")

            if chunk_count > 10:  # Limit output
                print("📦 ... (limiting output)")
                break

        print(f"✅ Total: {chunk_count} items, {total_bytes} audio bytes")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_cartesia_direct()
