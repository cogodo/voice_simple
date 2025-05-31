#!/usr/bin/env python3
"""
Crackling/Popping Audio Diagnostics Script
Specifically tests for high-frequency artifacts that cause crackling noise
"""

import sys
import os
import wave
import struct
import math
import json
import numpy as np
from pathlib import Path

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.voice_synthesis import my_processing_function_streaming
import logging

logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class CracklingDiagnostics:
    def __init__(self):
        self.test_text = "This is a test for crackling and popping sounds in audio."
        self.sample_rate = 22050
        
        # Crackling detection parameters
        self.pop_threshold = 0.2  # 20% sudden amplitude change
        self.click_duration_samples = 10  # Clicks shorter than this
        self.high_freq_threshold = 0.005  # High frequency energy threshold
        
        # Results
        self.frame_data = []
        self.crackling_issues = []
        self.frame_boundary_issues = []
        
    def run_crackling_diagnostics(self):
        """Run comprehensive crackling detection"""
        print("🔍 CRACKLING DIAGNOSTICS - Detecting Audio Pops & Clicks")
        print("=" * 70)
        
        try:
            # Phase 1: Collect frame-by-frame data
            print("\n📊 Phase 1: Collecting frame-by-frame audio data...")
            self.collect_frame_data()
            
            # Phase 2: Analyze frame boundaries for discontinuities
            print("\n🎯 Phase 2: Analyzing frame boundary discontinuities...")
            self.analyze_frame_boundaries()
            
            # Phase 3: Detect pops and clicks
            print("\n⚡ Phase 3: Detecting pops, clicks, and crackling...")
            self.detect_pops_and_clicks()
            
            # Phase 4: Analyze high-frequency artifacts
            print("\n🔊 Phase 4: Analyzing high-frequency artifacts...")
            self.analyze_high_frequency_artifacts()
            
            # Phase 5: Generate crackling report
            print("\n📋 Phase 5: Generating crackling diagnostics report...")
            self.generate_crackling_report()
            
        except Exception as e:
            logger.error(f"Crackling diagnostics failed: {e}", exc_info=True)
    
    def collect_frame_data(self):
        """Collect individual frame data for boundary analysis"""
        try:
            frame_count = 0
            
            for frame_bytes in my_processing_function_streaming(self.test_text, logger):
                frame_count += 1
                
                # Convert frame to samples
                samples = []
                for i in range(0, len(frame_bytes), 2):
                    if i + 1 < len(frame_bytes):
                        sample = struct.unpack('<h', frame_bytes[i:i+2])[0]
                        samples.append(sample / 32768.0)
                
                # Store frame data
                frame_info = {
                    'frame_number': frame_count,
                    'byte_length': len(frame_bytes),
                    'sample_count': len(samples),
                    'samples': samples,
                    'first_sample': samples[0] if samples else 0.0,
                    'last_sample': samples[-1] if samples else 0.0,
                    'max_amplitude': max(abs(s) for s in samples) if samples else 0.0,
                    'rms': math.sqrt(sum(s*s for s in samples) / len(samples)) if samples else 0.0
                }
                
                self.frame_data.append(frame_info)
                
                if frame_count % 20 == 0:
                    print(f"   Collected frame {frame_count} ({len(frame_bytes)} bytes, {len(samples)} samples)")
            
            print(f"✅ Collected {len(self.frame_data)} frames for analysis")
            
        except Exception as e:
            logger.error(f"Frame data collection failed: {e}")
            raise
    
    def analyze_frame_boundaries(self):
        """Analyze discontinuities at frame boundaries"""
        print("   Checking for discontinuities between frames...")
        
        boundary_issues = 0
        large_jumps = 0
        total_boundaries = len(self.frame_data) - 1
        
        for i in range(1, len(self.frame_data)):
            prev_frame = self.frame_data[i-1]
            curr_frame = self.frame_data[i]
            
            # Check continuity between last sample of prev frame and first sample of current frame
            if prev_frame['samples'] and curr_frame['samples']:
                last_sample = prev_frame['last_sample']
                first_sample = curr_frame['first_sample']
                
                # Calculate discontinuity
                discontinuity = abs(first_sample - last_sample)
                
                # Check for problematic discontinuities
                if discontinuity > self.pop_threshold:
                    boundary_issues += 1
                    issue = {
                        'boundary': f"Frame {i-1} -> {i}",
                        'discontinuity': discontinuity,
                        'last_sample': last_sample,
                        'first_sample': first_sample,
                        'severity': 'HIGH' if discontinuity > 0.5 else 'MEDIUM'
                    }
                    self.frame_boundary_issues.append(issue)
                    
                    if discontinuity > 0.5:
                        large_jumps += 1
        
        boundary_rate = (boundary_issues / total_boundaries) * 100 if total_boundaries > 0 else 0
        
        print(f"   • Total frame boundaries: {total_boundaries}")
        print(f"   • Discontinuities detected: {boundary_issues} ({boundary_rate:.1f}%)")
        print(f"   • Large jumps (>50%): {large_jumps}")
        
        if boundary_issues > 0:
            self.crackling_issues.append(f"Frame boundary discontinuities: {boundary_issues} detected")
            
            # Show worst offenders
            worst_issues = sorted(self.frame_boundary_issues, key=lambda x: x['discontinuity'], reverse=True)[:3]
            print(f"   🚨 Worst discontinuities:")
            for issue in worst_issues:
                print(f"      {issue['boundary']}: {issue['discontinuity']:.3f} jump ({issue['severity']})")
    
    def detect_pops_and_clicks(self):
        """Detect audio pops and clicks within frames"""
        print("   Scanning for pops and clicks within audio frames...")
        
        total_pops = 0
        total_clicks = 0
        
        for frame_info in self.frame_data:
            samples = frame_info['samples']
            frame_num = frame_info['frame_number']
            
            if len(samples) < 3:
                continue
            
            frame_pops = 0
            frame_clicks = 0
            
            # Detect sudden amplitude changes (pops)
            for i in range(1, len(samples) - 1):
                # Calculate local derivative (rate of change)
                prev_diff = abs(samples[i] - samples[i-1])
                next_diff = abs(samples[i+1] - samples[i])
                
                # Pop detection: sudden spike in amplitude change
                if prev_diff > self.pop_threshold or next_diff > self.pop_threshold:
                    frame_pops += 1
                
                # Click detection: rapid oscillation (sign changes)
                if i > 1 and i < len(samples) - 2:
                    # Look for rapid sign changes indicating clicks
                    signs = [math.copysign(1, samples[j]) for j in range(i-1, i+3)]
                    sign_changes = sum(1 for k in range(len(signs)-1) if signs[k] != signs[k+1])
                    
                    if sign_changes >= 3 and abs(samples[i]) > 0.1:  # Rapid oscillation with significant amplitude
                        frame_clicks += 1
            
            total_pops += frame_pops
            total_clicks += frame_clicks
            
            # Report problematic frames
            if frame_pops > 5 or frame_clicks > 3:
                print(f"      Frame {frame_num}: {frame_pops} pops, {frame_clicks} clicks")
        
        print(f"   • Total pops detected: {total_pops}")
        print(f"   • Total clicks detected: {total_clicks}")
        
        if total_pops > 0:
            self.crackling_issues.append(f"Audio pops detected: {total_pops} instances")
        
        if total_clicks > 0:
            self.crackling_issues.append(f"Audio clicks detected: {total_clicks} instances")
    
    def analyze_high_frequency_artifacts(self):
        """Analyze high-frequency content that could cause crackling"""
        print("   Analyzing high-frequency artifacts...")
        
        # Combine all samples for frequency analysis
        all_samples = []
        for frame_info in self.frame_data:
            all_samples.extend(frame_info['samples'])
        
        if len(all_samples) < 100:
            print("   ⚠️ Not enough samples for frequency analysis")
            return
        
        # Calculate high-frequency energy using simple differencing
        hf_energy = 0.0
        max_hf_spike = 0.0
        hf_spikes = 0
        
        for i in range(1, len(all_samples)):
            diff = abs(all_samples[i] - all_samples[i-1])
            hf_energy += diff * diff
            
            if diff > max_hf_spike:
                max_hf_spike = diff
            
            if diff > self.high_freq_threshold:
                hf_spikes += 1
        
        hf_energy_normalized = hf_energy / len(all_samples)
        hf_spike_rate = (hf_spikes / len(all_samples)) * 100
        
        print(f"   • High-frequency energy: {hf_energy_normalized:.6f}")
        print(f"   • Max HF spike: {max_hf_spike:.4f}")
        print(f"   • HF spike rate: {hf_spike_rate:.2f}%")
        
        # Assess crackling risk
        if hf_energy_normalized > 0.001:
            self.crackling_issues.append(f"High HF energy: {hf_energy_normalized:.6f} (may cause crackling)")
        
        if hf_spike_rate > 1.0:
            self.crackling_issues.append(f"High HF spike rate: {hf_spike_rate:.2f}% (crackling risk)")
        
        if max_hf_spike > 0.1:
            self.crackling_issues.append(f"Large HF spike detected: {max_hf_spike:.4f} (audible artifact)")
    
    def generate_crackling_report(self):
        """Generate comprehensive crackling diagnostics report"""
        # Calculate overall metrics
        total_frames = len(self.frame_data)
        total_samples = sum(len(f['samples']) for f in self.frame_data)
        avg_frame_size = total_samples / total_frames if total_frames > 0 else 0
        
        # Build report
        report = {
            "test_info": {
                "focus": "Crackling/Popping Audio Artifacts",
                "text": self.test_text,
                "sample_rate": self.sample_rate,
                "total_frames": total_frames,
                "total_samples": total_samples,
                "avg_frame_size": avg_frame_size
            },
            "crackling_analysis": {
                "frame_boundary_issues": len(self.frame_boundary_issues),
                "boundary_discontinuities": [
                    {
                        "boundary": issue['boundary'],
                        "discontinuity_magnitude": issue['discontinuity'],
                        "severity": issue['severity']
                    } for issue in self.frame_boundary_issues
                ],
                "total_issues_detected": len(self.crackling_issues),
                "issues_list": self.crackling_issues
            },
            "likely_crackling_sources": self.identify_crackling_sources(),
            "recommendations": self.generate_crackling_recommendations()
        }
        
        # Save report
        with open('crackling_diagnostics_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        print("📄 Crackling diagnostics report saved to: crackling_diagnostics_report.json")
        
        # Print summary
        self.print_crackling_summary(report)
    
    def identify_crackling_sources(self):
        """Identify likely sources of crackling based on findings"""
        sources = []
        
        if len(self.frame_boundary_issues) > 0:
            sources.append("Frame boundary discontinuities")
        
        if any("pops detected" in issue for issue in self.crackling_issues):
            sources.append("Audio pops within frames")
        
        if any("clicks detected" in issue for issue in self.crackling_issues):
            sources.append("Audio clicks/rapid oscillations")
        
        if any("HF energy" in issue for issue in self.crackling_issues):
            sources.append("High-frequency artifacts")
        
        if any("HF spike" in issue for issue in self.crackling_issues):
            sources.append("High-frequency spikes")
        
        if not sources:
            sources.append("No obvious crackling sources detected in backend processing")
            sources.append("Crackling likely occurs in frontend Web Audio API")
        
        return sources
    
    def generate_crackling_recommendations(self):
        """Generate specific recommendations for fixing crackling"""
        recommendations = []
        
        if len(self.frame_boundary_issues) > 0:
            recommendations.append("Add crossfading between audio frames (1-2ms overlap)")
            recommendations.append("Ensure frame boundaries align on sample boundaries")
            recommendations.append("Check for timing issues in frame delivery")
        
        if any("pops detected" in issue for issue in self.crackling_issues):
            recommendations.append("Investigate sample rate conversion artifacts")
            recommendations.append("Check for buffer underruns causing audio gaps")
        
        if any("clicks detected" in issue for issue in self.crackling_issues):
            recommendations.append("Look for rapid gain changes or filter instability")
            recommendations.append("Check for floating-point precision issues")
        
        if any("HF" in issue for issue in self.crackling_issues):
            recommendations.append("Add gentle low-pass filtering to remove HF artifacts")
            recommendations.append("Check Web Audio API sample rate matching (22050Hz)")
        
        if not self.crackling_issues:
            recommendations.append("Backend audio is clean - focus on frontend Web Audio API")
            recommendations.append("Check Web Audio API scheduling precision and timing")
            recommendations.append("Verify audio context sample rate matches backend (22050Hz)")
            recommendations.append("Look for buffer underruns in Web Audio playback")
            recommendations.append("Consider using ScriptProcessorNode for sample-accurate timing")
        
        return recommendations
    
    def print_crackling_summary(self, report):
        """Print crackling diagnostics summary"""
        print("\n" + "="*70)
        print("🔊 CRACKLING DIAGNOSTICS SUMMARY")
        print("="*70)
        
        crackling_analysis = report['crackling_analysis']
        issues = crackling_analysis['total_issues_detected']
        boundary_issues = crackling_analysis['frame_boundary_issues']
        
        print(f"📊 Overall Assessment:")
        print(f"   • Total frames analyzed: {report['test_info']['total_frames']}")
        print(f"   • Frame boundary issues: {boundary_issues}")
        print(f"   • Total crackling issues: {issues}")
        
        if issues > 0:
            print(f"\n⚠️ Crackling Issues Detected:")
            for i, issue in enumerate(crackling_analysis['issues_list'], 1):
                print(f"   {i}. {issue}")
        else:
            print(f"\n✅ No crackling artifacts detected in backend processing")
        
        print(f"\n🎯 Likely Crackling Sources:")
        for i, source in enumerate(report['likely_crackling_sources'], 1):
            print(f"   {i}. {source}")
        
        print(f"\n💡 Recommendations:")
        for i, rec in enumerate(report['recommendations'], 1):
            print(f"   {i}. {rec}")
        
        if boundary_issues > 0:
            print(f"\n🚨 Frame Boundary Issues (Top 3):")
            boundaries = crackling_analysis['boundary_discontinuities'][:3]
            for boundary in boundaries:
                print(f"   • {boundary['boundary']}: {boundary['discontinuity_magnitude']:.3f} jump ({boundary['severity']})")
        
        print("="*70)

def main():
    """Run crackling diagnostics"""
    print("🔊 Crackling/Popping Audio Diagnostics Tool")
    print("This tool specifically detects audio artifacts that cause crackling noise.")
    print("")
    
    # Check environment
    if not os.getenv("CARTESIA_API_KEY"):
        print("❌ CARTESIA_API_KEY environment variable not set")
        return 1
    
    diagnostics = CracklingDiagnostics()
    diagnostics.run_crackling_diagnostics()
    
    print("\n🎯 Crackling diagnostics complete! Check crackling_diagnostics_report.json for details.")
    return 0

if __name__ == "__main__":
    exit(main()) 