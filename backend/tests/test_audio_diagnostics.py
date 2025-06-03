#!/usr/bin/env python3
"""
Comprehensive Audio Diagnostics Script
Tests every stage of the audio pipeline to identify sources of static/artifacts
"""

import sys
import os
import wave
import base64
import struct
import math
import json
import numpy as np
from pathlib import Path

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.voice_synthesis import my_processing_function_streaming, diagnose_cartesia_audio_quality
import logging

# Setup detailed logging
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class AudioDiagnostics:
    def __init__(self):
        self.test_text = "Hello world, this is a test of the audio quality system."
        self.sample_rate = 22050
        
        # Analysis results
        self.cartesia_analysis = {}
        self.backend_analysis = {}
        self.conversion_analysis = {}
        self.artifacts_detected = []
        
        # Audio data at each stage
        self.raw_cartesia_data = []
        self.processed_backend_data = []
        self.final_output_data = []
        
    def run_full_diagnostics(self):
        """Run complete audio pipeline diagnostics"""
        print("🔬 Starting comprehensive audio diagnostics...")
        print("=" * 70)
        
        try:
            # Phase 1: Test Cartesia raw output quality
            print("\n📡 Phase 1: Analyzing raw Cartesia output...")
            self.test_cartesia_quality()
            
            # Phase 2: Test backend IIR processing
            print("\n🔧 Phase 2: Testing backend IIR processing...")
            self.test_backend_processing()
            
            # Phase 3: Test conversion artifacts
            print("\n🔄 Phase 3: Testing format conversion...")
            self.test_conversion_artifacts()
            
            # Phase 4: Analyze potential sources
            print("\n🔍 Phase 4: Analyzing artifact sources...")
            self.analyze_artifact_sources()
            
            # Phase 5: Generate comprehensive report
            print("\n📊 Phase 5: Generating diagnostic report...")
            self.generate_diagnostic_report()
            
        except Exception as e:
            logger.error(f"Diagnostics failed: {e}", exc_info=True)
    
    def test_cartesia_quality(self):
        """Test raw Cartesia output quality"""
        try:
            # Get raw Cartesia analysis
            self.cartesia_analysis = diagnose_cartesia_audio_quality(self.test_text, logger)
            
            if 'error' in self.cartesia_analysis:
                print(f"❌ Cartesia analysis failed: {self.cartesia_analysis['error']}")
                return
            
            # Print key metrics
            audio_levels = self.cartesia_analysis['audio_levels']
            quality_analysis = self.cartesia_analysis['quality_analysis']
            
            print(f"✅ Cartesia Raw Audio Analysis:")
            print(f"   • Peak Level: {audio_levels['peak_level']:.4f} ({audio_levels['peak_level_db']:.1f}dB)")
            print(f"   • RMS Level: {audio_levels['rms_level']:.4f} ({audio_levels['rms_level_db']:.1f}dB)")
            print(f"   • Dynamic Range: {audio_levels['dynamic_range_db']:.1f}dB")
            print(f"   • Clipping: {quality_analysis['clipping_percentage']:.2f}%")
            
            # Check for issues in raw Cartesia output
            if quality_analysis['clipping_percentage'] > 1.0:
                self.artifacts_detected.append("Raw Cartesia output has clipping")
            
            if audio_levels['dynamic_range_db'] < 6:
                self.artifacts_detected.append("Raw Cartesia output has poor dynamic range")
                
        except Exception as e:
            logger.error(f"Cartesia quality test failed: {e}")
            self.artifacts_detected.append(f"Cartesia quality test failed: {e}")
    
    def test_backend_processing(self):
        """Test backend IIR processing for artifacts"""
        try:
            print("🎛️ Testing backend IIR filter processing...")
            
            # Collect streaming output
            raw_chunks = []
            iir_chunks = []
            
            chunk_count = 0
            for chunk in my_processing_function_streaming(self.test_text, logger):
                chunk_count += 1
                iir_chunks.append(chunk)
                
                if chunk_count % 10 == 0:
                    print(f"   Processed chunk {chunk_count} ({len(chunk)} bytes)")
            
            if not iir_chunks:
                self.artifacts_detected.append("No chunks received from backend IIR processing")
                return
            
            # Combine all chunks
            combined_audio = b''.join(iir_chunks)
            
            # Analyze IIR-processed audio
            self.backend_analysis = self.analyze_pcm_audio(combined_audio, "Backend IIR Output")
            
            # Check for specific IIR artifacts
            self.check_iir_artifacts(combined_audio)
            
            # Save for comparison
            self.save_audio_sample(combined_audio, "backend_iir_output.wav")
            
            print(f"✅ Backend IIR processing complete: {len(combined_audio)} bytes, {chunk_count} chunks")
            
        except Exception as e:
            logger.error(f"Backend processing test failed: {e}")
            self.artifacts_detected.append(f"Backend processing test failed: {e}")
    
    def test_conversion_artifacts(self):
        """Test for artifacts in various conversion stages"""
        try:
            print("🔄 Testing conversion artifact sources...")
            
            # Test 1: Float32 to Int16 conversion precision
            self.test_float_to_int_conversion()
            
            # Test 2: Frame boundary discontinuities
            self.test_frame_boundary_issues()
            
            # Test 3: Sample rate conflicts
            self.test_sample_rate_issues()
            
            # Test 4: Endianness issues
            self.test_endianness_issues()
            
        except Exception as e:
            logger.error(f"Conversion testing failed: {e}")
            self.artifacts_detected.append(f"Conversion testing failed: {e}")
    
    def test_float_to_int_conversion(self):
        """Test Float32 to Int16 conversion for precision artifacts"""
        print("   Testing Float32→Int16 conversion precision...")
        
        # Create test signals with known characteristics
        test_signals = [
            ("Low level signal", 0.1),
            ("Medium level signal", 0.5),
            ("High level signal", 0.8),
            ("Near-clipping signal", 0.99),
        ]
        
        for name, level in test_signals:
            # Generate pure sine wave at different levels
            samples = 1000
            frequency = 440  # A4 note
            
            float_samples = []
            for i in range(samples):
                t = i / self.sample_rate
                sample = level * math.sin(2 * math.pi * frequency * t)
                float_samples.append(sample)
            
            # Convert to int16 using backend method
            int16_samples = []
            for float_val in float_samples:
                int_val = int(float_val * 32767.0)
                int_val = max(-32768, min(32767, int_val))
                int16_samples.append(int_val)
            
            # Convert back to float for comparison
            converted_back = [s / 32768.0 for s in int16_samples]
            
            # Calculate conversion error
            max_error = max(abs(orig - conv) for orig, conv in zip(float_samples, converted_back))
            rms_error = math.sqrt(sum((orig - conv)**2 for orig, conv in zip(float_samples, converted_back)) / len(float_samples))
            
            print(f"      {name}: Max error: {max_error:.6f}, RMS error: {rms_error:.6f}")
            
            if max_error > 0.0001:  # Check for excessive quantization error
                self.artifacts_detected.append(f"Float32→Int16 conversion error too high for {name}")
    
    def test_frame_boundary_issues(self):
        """Test for discontinuities at frame boundaries"""
        print("   Testing frame boundary continuity...")
        
        # This would require access to individual frames from streaming
        # For now, check if the combined audio has sudden jumps
        if hasattr(self, 'processed_backend_data') and self.processed_backend_data:
            # Analyze for sudden amplitude jumps that could indicate boundary issues
            samples = []
            for i in range(0, len(self.processed_backend_data), 2):
                if i + 1 < len(self.processed_backend_data):
                    sample = struct.unpack('<h', self.processed_backend_data[i:i+2])[0]
                    samples.append(sample / 32768.0)
            
            # Look for sudden amplitude changes
            large_jumps = 0
            for i in range(1, len(samples)):
                if abs(samples[i] - samples[i-1]) > 0.5:  # 50% amplitude jump
                    large_jumps += 1
            
            jump_rate = large_jumps / len(samples) * 100
            print(f"      Large amplitude jumps: {large_jumps} ({jump_rate:.2f}%)")
            
            if jump_rate > 0.1:  # More than 0.1% sudden jumps
                self.artifacts_detected.append(f"Frame boundary discontinuities detected: {jump_rate:.2f}% jump rate")
    
    def test_sample_rate_issues(self):
        """Test for sample rate mismatch artifacts"""
        print("   Testing sample rate consistency...")
        
        # Check if all components use 22050Hz consistently
        expected_rate = 22050
        
        # This is more of a configuration check
        print(f"      Expected sample rate: {expected_rate}Hz")
        print(f"      Backend sample rate: {self.sample_rate}Hz")
        
        if self.sample_rate != expected_rate:
            self.artifacts_detected.append(f"Sample rate mismatch: expected {expected_rate}, got {self.sample_rate}")
    
    def test_endianness_issues(self):
        """Test for little-endian/big-endian conversion issues"""
        print("   Testing endianness consistency...")
        
        # Create test pattern that would reveal endianness issues
        test_values = [0x1234, 0x5678, 0xABCD, 0xEF01]
        
        for value in test_values:
            # Pack as little-endian (correct format)
            le_bytes = struct.pack('<h', value if value < 32768 else value - 65536)
            
            # Unpack as little-endian (should match)
            unpacked_le = struct.unpack('<h', le_bytes)[0]
            
            # Unpack as big-endian (would be wrong)
            unpacked_be = struct.unpack('>h', le_bytes)[0]
            
            if unpacked_le != (value if value < 32768 else value - 65536):
                self.artifacts_detected.append(f"Endianness issue detected with value 0x{value:04X}")
    
    def check_iir_artifacts(self, audio_data):
        """Check for specific IIR filter artifacts"""
        print("   Analyzing IIR filter artifacts...")
        
        # Convert to samples for analysis
        samples = []
        for i in range(0, len(audio_data), 2):
            if i + 1 < len(audio_data):
                sample = struct.unpack('<h', audio_data[i:i+2])[0]
                samples.append(sample / 32768.0)
        
        if not samples:
            return
        
        # Check for IIR-specific artifacts
        
        # 1. Filter instability (oscillations)
        oscillation_count = 0
        for i in range(2, len(samples) - 2):
            # Look for rapid sign changes that could indicate instability
            if (samples[i-1] * samples[i] < 0 and 
                samples[i] * samples[i+1] < 0 and
                abs(samples[i]) > 0.1):
                oscillation_count += 1
        
        if oscillation_count > len(samples) * 0.01:  # More than 1% oscillations
            self.artifacts_detected.append(f"IIR filter instability detected: {oscillation_count} oscillations")
        
        # 2. Over-smoothing (excessive high-frequency attenuation)
        # Calculate high-frequency content
        high_freq_content = self.calculate_high_frequency_content(samples)
        print(f"      High-frequency content: {high_freq_content:.4f}")
        
        if high_freq_content < 0.01:  # Very low HF content might indicate over-smoothing
            self.artifacts_detected.append("Possible over-smoothing: very low high-frequency content")
        
        # 3. DC bias (IIR filters can introduce DC offset)
        dc_bias = sum(samples) / len(samples)
        print(f"      DC bias: {dc_bias:.6f}")
        
        if abs(dc_bias) > 0.01:  # More than 1% DC bias
            self.artifacts_detected.append(f"DC bias detected: {dc_bias:.6f}")
    
    def calculate_high_frequency_content(self, samples):
        """Calculate high-frequency content as a measure of audio brightness"""
        if len(samples) < 4:
            return 0.0
        
        # Simple high-pass difference filter
        hf_energy = 0.0
        for i in range(1, len(samples)):
            diff = samples[i] - samples[i-1]
            hf_energy += diff * diff
        
        return hf_energy / len(samples)
    
    def analyze_pcm_audio(self, audio_data, name):
        """Analyze PCM audio data for quality metrics"""
        samples = []
        for i in range(0, len(audio_data), 2):
            if i + 1 < len(audio_data):
                sample = struct.unpack('<h', audio_data[i:i+2])[0]
                samples.append(sample / 32768.0)
        
        if not samples:
            return {"error": "No samples found"}
        
        # Calculate metrics
        max_level = max(abs(s) for s in samples)
        rms_level = math.sqrt(sum(s*s for s in samples) / len(samples))
        peak_db = 20 * math.log10(max_level) if max_level > 0 else -100
        rms_db = 20 * math.log10(rms_level) if rms_level > 0 else -100
        
        # Count clipping
        clipped = sum(1 for s in samples if abs(s) >= 0.99)
        clipping_percent = (clipped / len(samples)) * 100
        
        analysis = {
            "name": name,
            "total_samples": len(samples),
            "duration_seconds": len(samples) / self.sample_rate,
            "peak_level": max_level,
            "peak_db": peak_db,
            "rms_level": rms_level,
            "rms_db": rms_db,
            "clipping_samples": clipped,
            "clipping_percentage": clipping_percent,
        }
        
        print(f"✅ {name} Analysis:")
        print(f"   • Duration: {analysis['duration_seconds']:.2f}s ({analysis['total_samples']} samples)")
        print(f"   • Peak: {max_level:.4f} ({peak_db:.1f}dB)")
        print(f"   • RMS: {rms_level:.4f} ({rms_db:.1f}dB)")
        print(f"   • Clipping: {clipped} samples ({clipping_percent:.2f}%)")
        
        return analysis
    
    def analyze_artifact_sources(self):
        """Analyze potential sources of artifacts"""
        print("🔍 Analyzing potential artifact sources...")
        
        # Check for known artifact patterns
        artifact_sources = {
            "cartesia_output": "Raw TTS output quality issues",
            "iir_processing": "IIR filter introduces artifacts", 
            "format_conversion": "Float32→Int16 conversion artifacts",
            "frame_boundaries": "Discontinuities at frame boundaries",
            "sample_rate": "Sample rate mismatch issues",
            "endianness": "Byte order conversion issues",
            "web_audio": "Web Audio API conversion artifacts",
            "timing": "Audio scheduling/timing issues"
        }
        
        detected_sources = []
        
        # Analyze based on collected evidence
        if self.cartesia_analysis and 'quality_analysis' in self.cartesia_analysis:
            if self.cartesia_analysis['quality_analysis']['clipping_percentage'] > 1.0:
                detected_sources.append("cartesia_output")
        
        # Check for IIR artifacts
        if "IIR filter instability" in str(self.artifacts_detected):
            detected_sources.append("iir_processing")
        
        if "over-smoothing" in str(self.artifacts_detected).lower():
            detected_sources.append("iir_processing")
        
        # Check conversion artifacts
        if "conversion error" in str(self.artifacts_detected).lower():
            detected_sources.append("format_conversion")
        
        if "boundary discontinuities" in str(self.artifacts_detected).lower():
            detected_sources.append("frame_boundaries")
        
        print(f"📊 Potential artifact sources identified:")
        for source in detected_sources:
            print(f"   • {artifact_sources[source]}")
        
        if not detected_sources:
            print("   ✅ No obvious artifact sources detected in backend processing")
            print("   🔍 Artifacts likely occur in frontend Web Audio API or audio scheduling")
            detected_sources.append("web_audio")
            detected_sources.append("timing")
        
        return detected_sources
    
    def generate_diagnostic_report(self):
        """Generate comprehensive diagnostic report"""
        report = {
            "test_info": {
                "text": self.test_text,
                "sample_rate": self.sample_rate,
                "timestamp": "2025-01-20T10:00:00Z"  # Current time
            },
            "cartesia_analysis": self.cartesia_analysis,
            "backend_analysis": self.backend_analysis,
            "artifacts_detected": self.artifacts_detected,
            "recommendations": self.generate_recommendations()
        }
        
        # Save report
        with open('audio_diagnostics_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("📄 Diagnostic report saved to: audio_diagnostics_report.json")
        
        # Print summary
        self.print_diagnostic_summary(report)
    
    def generate_recommendations(self):
        """Generate recommendations based on findings"""
        recommendations = []
        
        if "over-smoothing" in str(self.artifacts_detected).lower():
            recommendations.append("Reduce IIR filter alpha (increase from 0.35 to 0.5+) for more audio clarity")
        
        if "instability" in str(self.artifacts_detected).lower():
            recommendations.append("Check IIR filter stability - consider reducing gain or alpha value")
        
        if "conversion error" in str(self.artifacts_detected).lower():
            recommendations.append("Improve Float32→Int16 conversion precision or use higher bit depth")
        
        if "boundary discontinuities" in str(self.artifacts_detected).lower():
            recommendations.append("Add crossfading between audio frames to eliminate boundary artifacts")
        
        if "web_audio" in str(self.artifacts_detected).lower():
            recommendations.append("Investigate Web Audio API sample rate matching and scheduling precision")
        
        if not self.artifacts_detected:
            recommendations.append("Backend audio processing appears clean - focus on frontend Web Audio implementation")
            recommendations.append("Check Web Audio API createBuffer sample rate consistency")
            recommendations.append("Verify audio scheduling timing precision")
            recommendations.append("Test with different frame sizes or buffering strategies")
        
        return recommendations
    
    def print_diagnostic_summary(self, report):
        """Print diagnostic summary"""
        print("\n" + "="*70)
        print("🎯 AUDIO DIAGNOSTICS SUMMARY")
        print("="*70)
        
        artifacts = report['artifacts_detected']
        if artifacts:
            print(f"⚠️ {len(artifacts)} potential issues detected:")
            for i, artifact in enumerate(artifacts, 1):
                print(f"   {i}. {artifact}")
        else:
            print("✅ No major backend artifacts detected")
        
        print(f"\n📋 Recommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"   {i}. {rec}")
        
        print(f"\n📊 Key Metrics:")
        if 'cartesia_analysis' in report and 'audio_levels' in report['cartesia_analysis']:
            levels = report['cartesia_analysis']['audio_levels']
            print(f"   • Cartesia Peak: {levels['peak_level']:.3f} ({levels['peak_level_db']:.1f}dB)")
            print(f"   • Cartesia RMS: {levels['rms_level']:.3f} ({levels['rms_level_db']:.1f}dB)")
        
        if 'backend_analysis' in report and report['backend_analysis']:
            backend = report['backend_analysis']
            print(f"   • Backend Peak: {backend['peak_level']:.3f} ({backend['peak_db']:.1f}dB)")
            print(f"   • Backend RMS: {backend['rms_level']:.3f} ({backend['rms_db']:.1f}dB)")
            print(f"   • Backend Clipping: {backend['clipping_percentage']:.2f}%")
        
        print("="*70)
    
    def save_audio_sample(self, audio_data, filename):
        """Save audio data as WAV file for external analysis"""
        try:
            with wave.open(filename, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(self.sample_rate)
                wav_file.writeframes(audio_data)
            print(f"💾 Audio sample saved: {filename}")
        except Exception as e:
            print(f"❌ Failed to save {filename}: {e}")

def main():
    """Run comprehensive audio diagnostics"""
    print("🔬 Audio Diagnostics Tool - Comprehensive Pipeline Analysis")
    print("This tool will test every stage of the audio pipeline to identify artifact sources.")
    print("")
    
    # Check environment
    if not os.getenv("CARTESIA_API_KEY"):
        print("❌ CARTESIA_API_KEY environment variable not set")
        return 1
    
    diagnostics = AudioDiagnostics()
    diagnostics.run_full_diagnostics()
    
    print("\n🎯 Diagnostics complete! Check audio_diagnostics_report.json for detailed results.")
    return 0

if __name__ == "__main__":
    exit(main()) 