import socketio
import time

sio = socketio.SimpleClient()

try:
    print("Connecting to backend...")
    sio.connect("http://localhost:8000")

    print("Connected! Waiting for ready signal...")
    time.sleep(1)

    print("Sending test message...")
    sio.emit("conversation_text_input", {"text": "Hello AI, can you hear me?"})

    print("Waiting for response...")
    start_time = time.time()
    response_received = False

    while time.time() - start_time < 10:  # Wait up to 10 seconds
        try:
            events = sio.receive(timeout=1)
            if events:
                print(f"Received event: {events[0]} with data: {events[1]}")
                if events[0] == "ai_response_complete":
                    print(
                        f"✅ AI Response: {events[1].get('response', events[1].get('content', 'No content'))}"
                    )
                    response_received = True
                    break
        except Exception as e:
            print(f"Timeout or error receiving: {e}")
            break

    if not response_received:
        print("❌ No AI response received")

    sio.disconnect()
    print("Test complete")

except Exception as e:
    print(f"❌ Error: {e}")
    import traceback

    traceback.print_exc()
