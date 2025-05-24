#!/usr/bin/env python3
import socketio
import time

sio = socketio.SimpleClient()
sio.connect('http://localhost:8000')

print('Testing AI conversation with auto-TTS...')
sio.emit('conversation_text_input', {'text': 'Say hello'})

# Listen for events
for i in range(10):
    try:
        events = sio.receive(timeout=2)
        if events:
            print(f'{events[0]}: {events[1]}')
    except:
        break

sio.disconnect() 