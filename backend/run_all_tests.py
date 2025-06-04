#!/usr/bin/env python3
"""
Comprehensive test runner for the unified TTS pipeline.
Runs logic tests always, integration tests only if server is available.
"""
import subprocess
import sys
import os

def run_test_script(script_name, description):
    """Run a test script and return success status."""
    print(f"\n🧪 Running {description}...")
    print("=" * 60)
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=False, text=True, cwd=os.getcwd())
        success = result.returncode == 0
        
        if success:
            print(f"✅ {description} PASSED")
        else:
            print(f"❌ {description} FAILED")
        
        return success
    except Exception as e:
        print(f"❌ Error running {description}: {e}")
        return False

def main():
    print("🎯 UNIFIED TTS PIPELINE - COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print("🔧 Testing unified pipeline implementation")
    print("📋 Ensuring test button and LLM responses use identical audio flow")
    
    results = {}
    
    # 1. Always run logic tests (no server needed)
    print("\n" + "🔵" * 20 + " LOGIC TESTS " + "🔵" * 20)
    results['logic'] = run_test_script('test_pipeline_logic.py', 'Pipeline Logic Tests')
    
    # 2. Check server status
    print("\n" + "🔵" * 20 + " SERVER STATUS " + "🔵" * 20)
    results['server'] = run_test_script('check_server.py', 'Server Status Check')
    
    # 3. Run integration tests if server is available
    if results['server']:
        print("\n" + "🔵" * 20 + " INTEGRATION TESTS " + "🔵" * 20)
        results['integration'] = run_test_script('test_unified_pipeline.py', 'Full Integration Tests')
    else:
        print("\n" + "🔵" * 20 + " INTEGRATION TESTS " + "🔵" * 20)
        print("⏭️ Skipping integration tests - server not available")
        print("💡 Start the backend server with: python app.py")
        results['integration'] = None
    
    # Summary
    print("\n" + "=" * 80)
    print("🎯 COMPREHENSIVE TEST RESULTS:")
    print("=" * 80)
    
    logic_status = "✅ PASS" if results['logic'] else "❌ FAIL"
    server_status = "✅ RUNNING" if results['server'] else "❌ NOT RUNNING"
    
    print(f"🧠 Logic Tests:      {logic_status}")
    print(f"🖥️  Server Status:    {server_status}")
    
    if results['integration'] is not None:
        integration_status = "✅ PASS" if results['integration'] else "❌ FAIL"
        print(f"🔗 Integration Tests: {integration_status}")
    else:
        print(f"🔗 Integration Tests: ⏭️ SKIPPED (server not available)")
    
    # Overall assessment
    print("\n" + "🎉" * 30)
    
    if results['logic']:
        print("✅ UNIFIED PIPELINE LOGIC: VERIFIED")
        print("🎊 Test button and LLM responses use IDENTICAL pipeline")
        print("🔊 Crackling issue should be RESOLVED")
        
        if results['integration']:
            print("🚀 FULL INTEGRATION: VERIFIED")
            print("🎯 All systems working perfectly!")
        elif results['server']:
            print("⚠️ INTEGRATION: Needs investigation (server running but tests failed)")
        else:
            print("📋 INTEGRATION: Pending server startup")
            print("💡 Next: Start server and run integration tests")
    else:
        print("❌ PIPELINE LOGIC: Issues detected")
        print("🔧 Fix logic issues before proceeding")
    
    print("🎉" * 30)
    
    # Return overall success
    critical_tests_passed = results['logic']
    if results['integration'] is not None:
        critical_tests_passed = critical_tests_passed and results['integration']
    
    return critical_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 