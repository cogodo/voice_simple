#!/usr/bin/env python3
"""
Simple server status checker for the voice agent backend.
"""
import requests
import time
import sys

def check_http_server():
    """Check if HTTP server is responding."""
    try:
        print("🔌 Checking HTTP server...")
        response = requests.get('http://localhost:8000', timeout=5)
        print(f"✅ HTTP server responding: {response.status_code}")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ HTTP server not responding (Connection refused)")
        return False
    except requests.exceptions.Timeout:
        print("❌ HTTP server timeout")
        return False
    except Exception as e:
        print(f"❌ HTTP server error: {e}")
        return False

def check_socketio_server():
    """Check if SocketIO server is responding via HTTP polling."""
    try:
        print("🔌 Checking SocketIO server...")
        # Try to access the SocketIO endpoint directly
        response = requests.get('http://localhost:8000/socket.io/?transport=polling&EIO=4', timeout=5)
        if response.status_code == 200:
            print("✅ SocketIO server responding")
            return True
        else:
            print(f"❌ SocketIO server returned status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ SocketIO server not responding (Connection refused)")
        return False
    except requests.exceptions.Timeout:
        print("❌ SocketIO server timeout")
        return False
    except Exception as e:
        print(f"❌ SocketIO server error: {e}")
        return False

def main():
    print("🧪 VOICE AGENT SERVER STATUS CHECK")
    print("=" * 50)
    
    http_ok = check_http_server()
    socketio_ok = check_socketio_server()
    
    print("\n" + "=" * 50)
    print("📊 SERVER STATUS SUMMARY:")
    print("=" * 50)
    
    if http_ok and socketio_ok:
        print("🎉 ALL SYSTEMS GO!")
        print("✅ HTTP server: OK")
        print("✅ SocketIO server: OK")
        print("🚀 Ready for full pipeline testing")
        return True
    else:
        print("⚠️ SERVER ISSUES DETECTED:")
        print(f"{'✅' if http_ok else '❌'} HTTP server: {'OK' if http_ok else 'FAILED'}")
        print(f"{'✅' if socketio_ok else '❌'} SocketIO server: {'OK' if socketio_ok else 'FAILED'}")
        print("🔧 Start the backend server before running tests")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 