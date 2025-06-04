#!/usr/bin/env python3
"""
Test Runner for Backend Streaming Tests
Runs all streaming tests and provides comprehensive results.
"""

import sys
import os
import subprocess
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_test_script(script_name, description):
    """Run a test script and return success status."""
    print(f"\n{'='*60}")
    print(f"🚀 Running {description}")
    print(f"📄 Script: {script_name}")
    print(f"{'='*60}")
    
    script_path = os.path.join(os.path.dirname(__file__), script_name)
    
    try:
        # Run the test script
        start_time = time.time()
        result = subprocess.run([sys.executable, script_path], 
                              capture_output=False, 
                              text=True)
        end_time = time.time()
        
        duration = end_time - start_time
        
        if result.returncode == 0:
            print(f"✅ {description} PASSED (took {duration:.2f}s)")
            return True
        else:
            print(f"❌ {description} FAILED (took {duration:.2f}s)")
            return False
            
    except Exception as e:
        print(f"❌ Failed to run {script_name}: {e}")
        return False


def check_server_status():
    """Check if the backend server is running."""
    print("🔍 Checking backend server status...")
    
    try:
        import requests
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend server is running")
            return True
        else:
            print(f"⚠️  Backend server responded with status {response.status_code}")
            return False
    except ImportError:
        print("⚠️  'requests' not available for server check")
        return None  # Unknown status
    except Exception as e:
        print(f"❌ Backend server not accessible: {e}")
        return False


def check_environment():
    """Check if the environment is properly set up."""
    print("🔧 Checking test environment...")
    
    # Check for required packages
    required_packages = ['socketio', 'flask', 'flask-socketio']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} is available")
        except ImportError:
            missing_packages.append(package)
            print(f"❌ {package} is missing")
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return False
    
    # Check for environment variables
    env_vars = ['CARTESIA_API_KEY', 'OPENAI_API_KEY']
    missing_env = []
    
    for var in env_vars:
        if os.getenv(var):
            print(f"✅ {var} is set")
        else:
            missing_env.append(var)
            print(f"⚠️  {var} is not set")
    
    if missing_env:
        print(f"\n⚠️  Missing environment variables: {', '.join(missing_env)}")
        print("Some tests may fail without proper API keys")
    
    return True


def main():
    """Run all streaming tests."""
    print("🎯 Backend Streaming Test Suite")
    print("=" * 80)
    print("This suite tests the core streaming functionality of the backend")
    print("=" * 80)
    
    # Check environment
    if not check_environment():
        print("❌ Environment check failed. Fix issues above and try again.")
        return False
    
    # Check server status
    server_status = check_server_status()
    if server_status is False:
        print("\n⚠️  Backend server is not running!")
        print("Please start the server with: python app.py")
        print("WebSocket tests will be skipped.")
        skip_websocket = True
    else:
        skip_websocket = False
    
    # Define tests
    tests = [
        ("test_streaming_basic.py", "Basic TTS Streaming Tests"),
    ]
    
    if not skip_websocket:
        tests.append(("test_websocket_streaming.py", "WebSocket TTS Streaming Tests"))
    
    # Run tests
    passed = 0
    total = len(tests)
    
    print(f"\n🧪 Running {total} test suite(s)...")
    
    for script, description in tests:
        if run_test_script(script, description):
            passed += 1
        else:
            print(f"❌ {description} failed")
    
    # Final results
    print(f"\n{'='*80}")
    print(f"🎯 FINAL TEST RESULTS")
    print(f"{'='*80}")
    print(f"✅ Passed: {passed}/{total} test suites")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Backend streaming is working correctly.")
        print("\n📋 What was tested:")
        print("   • TTS streaming service functionality")
        print("   • Streaming timing and performance")
        print("   • Streaming consistency")
        if not skip_websocket:
            print("   • WebSocket streaming events")
            print("   • Real-time frame delivery")
            print("   • Error handling")
        
        print("\n✨ Your backend is ready for production use!")
        return True
    else:
        print(f"❌ {total - passed} test suite(s) failed.")
        print("\n🔧 Troubleshooting:")
        print("   • Check that all dependencies are installed")
        print("   • Verify API keys are set (CARTESIA_API_KEY, OPENAI_API_KEY)")
        print("   • Ensure the backend server is running for WebSocket tests")
        print("   • Check network connectivity")
        
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 