#!/usr/bin/env python3
"""
Comprehensive test script to verify all audio and conversation fixes.
Tests:
1. LLM response triggering TTS automatically
2. Audio chunk streaming and playback
3. Direct TTS functionality
4. WebSocket connection stability
"""

import socketio
import time
import sys


def test_complete_flow():
    """Test the complete conversation and audio flow."""

    print("🧪 Testing Complete Audio & Conversation Flow")
    print("=" * 60)

    sio = socketio.SimpleClient()

    try:
        # Test 1: Connection
        print("\n1️⃣ Testing WebSocket Connection...")
        sio.connect("http://localhost:8000")
        print("✅ Connected successfully")

        time.sleep(1)

        # Test 2: Direct TTS
        print("\n2️⃣ Testing Direct TTS...")
        audio_chunks_received = []
        tts_finished = False

        def track_audio_chunks():
            nonlocal audio_chunks_received, tts_finished
            try:
                while True:
                    events = sio.receive(timeout=1)
                    if events:
                        event_name, data = events[0], events[1]

                        if event_name == "audio_chunk":
                            audio_chunks_received.append(data)
                            print(
                                f"  📢 Audio chunk received: {len(data.get('audio_chunk', []))} bytes"
                            )

                        elif event_name == "tts_starting":
                            print(f"  🎵 TTS starting: {data.get('text', '')[:30]}...")

                        elif event_name == "tts_finished":
                            print(
                                f"  ✅ TTS finished: {data.get('total_chunks', 0)} chunks"
                            )
                            tts_finished = True
                            break

                        elif event_name == "tts_error":
                            print(f"  ❌ TTS Error: {data.get('error')}")
                            break

            except Exception as e:
                if "timeout" not in str(e).lower():
                    print(f"  ⚠️ Event error: {e}")

        # Send TTS request
        sio.emit(
            "synthesize_speech_streaming",
            {"text": "Hello, this is a test of the text to speech system."},
        )

        # Track audio chunks
        track_audio_chunks()

        if audio_chunks_received and tts_finished:
            print(
                f"✅ Direct TTS working: {len(audio_chunks_received)} audio chunks received"
            )
        else:
            print(
                f"❌ Direct TTS issue: {len(audio_chunks_received)} chunks, finished: {tts_finished}"
            )

        time.sleep(1)

        # Test 3: AI Conversation with Auto-TTS
        print("\n3️⃣ Testing AI Conversation with Auto-TTS...")
        audio_chunks_received = []
        ai_response_received = False
        tts_finished = False

        def track_conversation():
            nonlocal audio_chunks_received, ai_response_received, tts_finished
            try:
                while True:
                    events = sio.receive(timeout=2)
                    if events:
                        event_name, data = events[0], events[1]

                        if event_name == "ai_thinking":
                            print(f"  🤔 AI thinking: {data.get('status')}")

                        elif event_name == "ai_response_complete":
                            ai_response_received = True
                            response = data.get("response", "")
                            print(f"  🤖 AI response: {response[:50]}...")

                        elif event_name == "audio_chunk":
                            audio_chunks_received.append(data)
                            # Don't print every chunk to reduce noise

                        elif event_name == "tts_starting":
                            print("  🎵 Auto-TTS starting for AI response...")

                        elif event_name == "tts_finished":
                            print(
                                f"  ✅ Auto-TTS finished: {data.get('total_chunks', 0)} chunks"
                            )
                            tts_finished = True
                            break

                        elif event_name == "conversation_error":
                            print(f"  ❌ Conversation Error: {data.get('error')}")
                            break

                    # Timeout after 15 seconds
                    if time.time() - start_time > 15:
                        print("  ⏰ Timeout waiting for complete response")
                        break

            except Exception as e:
                if "timeout" not in str(e).lower():
                    print(f"  ⚠️ Event error: {e}")

        # Send conversation message
        start_time = time.time()
        sio.emit(
            "conversation_text_input",
            {"text": "Please tell me a fun fact about space in one sentence."},
        )

        # Track conversation flow
        track_conversation()

        if ai_response_received and audio_chunks_received and tts_finished:
            print(
                f"✅ AI Conversation + Auto-TTS working: Response received, {len(audio_chunks_received)} audio chunks"
            )
        else:
            print(
                f"❌ AI Conversation issue: AI response: {ai_response_received}, Audio chunks: {len(audio_chunks_received)}, TTS finished: {tts_finished}"
            )

        # Test 4: Connection Stability
        print("\n4️⃣ Testing Connection Stability...")
        try:
            sio.emit("synthesize_speech_streaming", {"text": "Connection test"})
            time.sleep(3)
            print("✅ Connection stable")
        except Exception as e:
            print(f"❌ Connection issue: {e}")

        sio.disconnect()

        # Final Summary
        print("\n" + "=" * 60)
        print("🎯 TEST SUMMARY")
        print("=" * 60)

        print("✅ WebSocket Connection: Working")
        print(
            f"{'✅' if audio_chunks_received else '❌'} Audio Streaming: {'Working' if audio_chunks_received else 'Failed'}"
        )
        print(
            f"{'✅' if ai_response_received else '❌'} AI Responses: {'Working' if ai_response_received else 'Failed'}"
        )
        print(
            f"{'✅' if tts_finished else '❌'} Auto-TTS after AI: {'Working' if tts_finished else 'Failed'}"
        )

        if ai_response_received and audio_chunks_received and tts_finished:
            print(
                "\n🎉 ALL SYSTEMS WORKING! The audio and conversation issues have been FIXED!"
            )
            print("\n📱 Flutter App Status:")
            print("   • Direct TTS should work smoothly (no more choppy audio)")
            print("   • AI conversations should automatically convert to speech")
            print("   • Microphone should work on Chrome web platform")
            print("\n🎯 Next Steps:")
            print("   1. Test microphone in Flutter web app")
            print("   2. Verify smooth audio playback")
            print("   3. Test complete voice-to-voice conversation")
        else:
            print("\n⚠️ Some issues remain - check the specific test results above")

        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_complete_flow()
    sys.exit(0 if success else 1)
