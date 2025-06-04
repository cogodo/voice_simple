#!/usr/bin/env python3
"""
Test script to verify frame size calculations for audio streaming.
"""

# Backend frame size calculation
SAMPLE_RATE = 22050
FRAME_SIZE_MS = 20
SAMPLES_PER_FRAME = int(FRAME_SIZE_MS * SAMPLE_RATE / 1000)  # 441 samples
BYTES_PER_FRAME = SAMPLES_PER_FRAME * 2  # 882 bytes (16-bit samples)

print("=== Audio Frame Size Verification ===")
print(f"Sample Rate: {SAMPLE_RATE} Hz")
print(f"Frame Duration: {FRAME_SIZE_MS} ms")
print(f"Samples per Frame: {SAMPLES_PER_FRAME}")
print(f"Bytes per Frame: {BYTES_PER_FRAME}")
print()

# Verify calculations
expected_samples = 441  # 22050 * 0.02 = 441
expected_bytes = 882  # 441 * 2 = 882

print("=== Verification ===")
print(
    f"Expected samples: {expected_samples}, Calculated: {SAMPLES_PER_FRAME}, Match: {SAMPLES_PER_FRAME == expected_samples}"
)
print(
    f"Expected bytes: {expected_bytes}, Calculated: {BYTES_PER_FRAME}, Match: {BYTES_PER_FRAME == expected_bytes}"
)
print()

# Test with different frame durations
print("=== Frame Size for Different Durations ===")
for duration_ms in [10, 20, 30, 40, 50]:
    samples = int(duration_ms * SAMPLE_RATE / 1000)
    bytes_needed = samples * 2
    print(f"{duration_ms}ms: {samples} samples, {bytes_needed} bytes")

print()
print("=== Buffer Calculations ===")
buffer_frames = 10  # 200ms buffer
buffer_duration_ms = buffer_frames * FRAME_SIZE_MS
buffer_bytes = buffer_frames * BYTES_PER_FRAME
print(
    f"Ring Buffer: {buffer_frames} frames = {buffer_duration_ms}ms = {buffer_bytes} bytes"
)
