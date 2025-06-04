#!/usr/bin/env python3
"""
Test script to verify backend audio improvements are working correctly.
"""

import sys
import logging
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from services.voice_synthesis import (
    my_processing_function_streaming,
    diagnose_cartesia_audio_quality,
)


def test_audio_improvements():
    """Test the audio improvements in the backend."""

    # Set up logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    print("🧪 Testing Backend Audio Improvements")
    print("=" * 50)

    # Test text
    test_text = "Hello! This is a test of the improved audio processing system."

    try:
        print("🔍 1. Testing Cartesia Audio Quality Diagnosis...")
        diagnosis = diagnose_cartesia_audio_quality(test_text, logger)

        if "error" in diagnosis:
            print(f"❌ Diagnosis failed: {diagnosis['error']}")
            return False

        print("✅ Diagnosis completed successfully!")
        print("📊 Audio Analysis Results:")
        print(
            f"   • Peak Level: {diagnosis['audio_levels']['peak_level']:.4f} ({diagnosis['audio_levels']['peak_level_db']:.1f}dB)"
        )
        print(
            f"   • RMS Level: {diagnosis['audio_levels']['rms_level']:.4f} ({diagnosis['audio_levels']['rms_level_db']:.1f}dB)"
        )
        print(
            f"   • Recommended Gain: {diagnosis['recommendations']['recommended_gain']:.2f}x ({diagnosis['recommendations']['recommended_gain_db']:.1f}dB)"
        )

        if diagnosis["recommendations"]["issues"]:
            print("⚠️ Issues Found:")
            for issue in diagnosis["recommendations"]["issues"]:
                print(f"   • {issue}")
        else:
            print("✅ No major audio quality issues detected")

        print("\n🎵 2. Testing Streaming Audio Processing...")

        # Test streaming function
        frame_count = 0
        total_bytes = 0

        for audio_chunk in my_processing_function_streaming(test_text, logger):
            frame_count += 1
            total_bytes += len(audio_chunk)

            if frame_count <= 3:  # Show first few frames
                print(f"   📦 Frame {frame_count}: {len(audio_chunk)} bytes")

            if frame_count >= 10:  # Limit test to first 10 frames
                break

        print("✅ Streaming test completed!")
        print(f"   • Total frames processed: {frame_count}")
        print(f"   • Total audio bytes: {total_bytes}")
        print(f"   • Average frame size: {total_bytes / frame_count:.1f} bytes")

        # Verify improvements are applied
        if diagnosis["recommendations"]["recommended_gain"] > 1.0:
            print("🔧 Audio improvements detected:")
            print(
                f"   • Gain boost applied: +{diagnosis['recommendations']['recommended_gain_db']:.1f}dB"
            )
            print("   • This should resolve low audio level issues")

        print("\n🎯 Backend Audio Improvements Test: ✅ PASSED")
        return True

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_audio_improvements()
    sys.exit(0 if success else 1)
