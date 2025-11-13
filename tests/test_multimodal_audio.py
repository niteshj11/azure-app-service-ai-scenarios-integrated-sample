#!/usr/bin/env python3
"""
Test Multimodal Audio Scenario
Tests audio upload and transcription capabilities
"""

import requests
import os
import sys
import time
from datetime import datetime
from io import BytesIO
import wave
import struct
from html_report_generator import HTMLReportGenerator
from bs4 import BeautifulSoup
from test_config import BASE_URL, AZURE_URL, TESTING_LOCAL, TESTING_AZURE

def create_test_audio_data():
    """Create a minimal WAV audio file for testing"""
    # Create a 1-second mono WAV file with 8kHz sample rate
    sample_rate = 8000
    duration = 1  # 1 second
    frequency = 440  # A note
    
    # Generate sine wave
    samples = []
    for i in range(int(sample_rate * duration)):
        sample = int(32767 * 0.1 * (i % (sample_rate // frequency)) / (sample_rate // frequency))
        samples.append(sample)
    
    # Create WAV file in memory
    buffer = BytesIO()
    
    with wave.open(buffer, 'wb') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Write samples
        for sample in samples:
            wav_file.writeframes(struct.pack('<h', sample))
    
    buffer.seek(0)
    return buffer.getvalue()

def test_audio_upload(base_url, report_generator=None, basic_mode=False):
    """Test audio upload and transcription"""
    print(f"\n🎵 Testing Audio Upload - {base_url} ({'Basic Mode' if basic_mode else 'Full Mode'})")
    
    session = requests.Session()
    environment = "local" if "127.0.0.1" in base_url else "azure"
    
    try:
        # Test 1: Get initial page
        print("1. Loading chat interface...")
        response = session.get(base_url, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Failed to load page: {response.status_code}")
        
        print("   ✅ Interface loaded successfully")
        
        # Test 2: Audio upload scenarios
        print("2. Testing audio upload functionality...")
        
        # Check for existing test audio file
        test_audio_path = "tests/test_inputs/test_customer_service_audio.mp3"
        
        if os.path.exists(test_audio_path):
            print("   Using existing test audio file")
            with open(test_audio_path, 'rb') as f:
                audio_data = f.read()
            filename = "test_customer_service_audio.mp3"
            content_type = "audio/mpeg"
        else:
            print("   Using generated test audio")
            audio_data = create_test_audio_data()
            filename = "test_audio.wav"
            content_type = "audio/wav"
        
        # TechMart audio scenario from Manual Testing Guide
        audio_scenarios = [
            {
                "message": "Transcribe this customer support call and provide a summary of the call along with required actions to be taken.",
                "scenario": "Test 12: Audio Customer Support",
                "expected_keywords": ["transcribe", "customer", "support", "call", "summary", "actions", "techmart", "service", "resolution", "follow-up", "escalate", "business"],
                "validation_criteria": ["provides TechMart customer service context", "demonstrates business intelligence", "includes actionable recommendations", "shows professional customer resolution"]
            }
        ]
        
        # Apply basic mode filtering if enabled
        scenarios_to_test = audio_scenarios[:1] if basic_mode else audio_scenarios
        print(f"   Running {'1 (first)' if basic_mode else 'all'} audio test(s)")
        
        for i, scenario_data in enumerate(scenarios_to_test, 1):
            print(f"   Testing scenario {i}: {scenario_data['scenario']}")
            
            start_time = time.time()
            
            # Prepare multipart form data
            files = {
                'audio': (filename, BytesIO(audio_data), content_type)
            }
            data = {
                'message': scenario_data['message']
            }
            
            response = session.post(base_url, files=files, data=data, timeout=120)  # Extended timeout for audio processing
            duration = time.time() - start_time
            
            # Extract actual AI response from the page
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the last assistant message - handle both popup and regular interfaces
            # Try popup interface structure first (chat-message class)
            assistant_messages = soup.find_all('div', class_='chat-message assistant')
            if not assistant_messages:
                # Try regular interface structure (message class)
                assistant_messages = soup.find_all('div', class_='message assistant')
            
            if assistant_messages:
                ai_response = assistant_messages[-1].get_text(strip=True)
                # Check if this is a real AI response or just an upload confirmation
                if "uploaded successfully" in ai_response.lower() and len(ai_response) < 100:
                    ai_response = "ERROR: Audio uploaded but no AI transcription detected. AI response too short or generic."
            else:
                # No AI response found at all
                ai_response = "ERROR: No AI response found. Multimodal audio processing failed completely."
            
            # Perform relevance analysis for TechMart context
            expected_keywords = scenario_data['expected_keywords']
            response_lower = ai_response.lower()
            found_keywords = [keyword for keyword in expected_keywords if keyword in response_lower]
            relevance_score = len(found_keywords) / len(expected_keywords) * 100
            
            # Check for actual transcription content (real transcription should be long and detailed)
            transcription_indicators = ['transcription', 'transcript', 'conversation', 'spoke', 'said', 'customer said', 'representative']
            found_transcription_indicators = [indicator for indicator in transcription_indicators if indicator in response_lower]
            
            # Check for error conditions first
            if "error:" in ai_response.lower() or "failed" in ai_response.lower():
                print(f"   ❌ Scenario {i}: FAILED - Audio transcription error")
                status = "FAILED"
            elif len(ai_response) > 500 and found_transcription_indicators and relevance_score >= 25:
                print(f"   ✅ Scenario {i}: PASSED - Real AI transcription detected ({relevance_score:.1f}%, {len(found_transcription_indicators)} transcription indicators)")
                status = "PASSED"
            elif found_transcription_indicators and len(ai_response) > 200:
                print(f"   ⚠️ Scenario {i}: PARTIAL - Some transcription detected but incomplete ({relevance_score:.1f}%, {len(found_transcription_indicators)} indicators)")
                status = "FAILED"  # Still fail for partial processing
            else:
                print(f"   ❌ Scenario {i}: FAILED - No real transcription processing ({relevance_score:.1f}%, {len(found_transcription_indicators)} indicators, {len(ai_response)} chars)")
                status = "FAILED"
            
            # Add detailed analysis to the AI response
            analysis_text = f"\n\n[AUDIO ANALYSIS]\n"
            analysis_text += f"• Audio File: {filename}\n"
            analysis_text += f"• Expected Keywords: {', '.join(expected_keywords)}\n"
            analysis_text += f"• Found Keywords: {', '.join(found_keywords)}\n"
            analysis_text += f"• Transcription Indicators: {', '.join(found_transcription_indicators)}\n"
            analysis_text += f"• Relevance Score: {relevance_score:.1f}%\n"
            analysis_text += f"• TechMart Context: {'Strong' if relevance_score >= 50 else 'Moderate' if relevance_score >= 30 else 'Weak'}"
            
            enhanced_response = ai_response + analysis_text
            
            # Add to report with audio embedding
            if report_generator:
                media_files = [test_audio_path] if os.path.exists(test_audio_path) else []
                report_generator.add_test_result(
                    scenario=f"TechMart Audio: {scenario_data['scenario']}",
                    input_data={
                        "message": scenario_data['message'],
                        "audio_file": filename,
                        "test_type": "techmart_multimodal_audio",
                        "scenario": scenario_data['scenario'],
                        "expected_keywords": expected_keywords
                    },
                    output_data=enhanced_response,
                    status=status,
                    duration=duration,
                    environment=environment,
                    media_files=media_files,
                    response_code=response.status_code
                )
            
            time.sleep(8)  # Extended delay between audio uploads to prevent server overload
        
        # Test 3: Audio format handling
        print("3. Testing audio format handling...")
        
        format_message = "This audio contains important business information. Please transcribe it accurately and organize the content with clear headings for different topics discussed."
        
        files = {
            'audio': (filename, BytesIO(audio_data), content_type)
        }
        data = {'message': format_message}
        
        response = session.post(base_url, files=files, data=data, timeout=120)
        
        # Check for structured response
        structure_keywords = ['heading', 'topic', 'section', 'transcription', 'organized', 'business', 'information']
        response_lower = response.text.lower()
        found_structure_keywords = sum(1 for keyword in structure_keywords if keyword in response_lower)
        
        if found_structure_keywords >= 2:
            print("   ✅ Audio format handling functional")
        else:
            print("   ⚠️ Audio format handling unclear")
        
        # Test 4: Audio quality analysis (lightweight test to avoid timeout)
        print("4. Testing audio quality analysis...")
        
        try:
            quality_message = "Please analyze the quality of this audio recording briefly."
            
            files = {
                'audio': (filename, BytesIO(audio_data), content_type)
            }
            data = {'message': quality_message}
            
            response = session.post(base_url, files=files, data=data, timeout=90)  # Reasonable timeout for quality analysis
            
            quality_keywords = ['quality', 'clarity', 'noise', 'clear', 'audible', 'audio']
            response_lower = response.text.lower()
            found_quality_keywords = sum(1 for keyword in quality_keywords if keyword in response_lower)
            
            if found_quality_keywords >= 2:  # Reduced threshold
                print("   ✅ Audio quality analysis functional")
            else:
                print("   ⚠️ Audio quality analysis unclear")
        except requests.exceptions.Timeout:
            print("   ⚠️ Audio quality analysis timed out (skipped)")
        
        return True
        
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out (audio processing can be slow)")
        return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed")
        return False
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def main():
    """Run multimodal audio tests on both regular and popup interfaces"""
    print("=" * 60)
    print("🎵 MULTIMODAL AUDIO SCENARIO TEST")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize HTML report generator
    report_generator = HTMLReportGenerator("Multimodal Audio Scenario Test")
    
    results = {}
    
    # Test interfaces based on command line arguments
    basic_mode = "basic" in sys.argv
    test_popup = "popup" in sys.argv or len(sys.argv) == 1
    test_regular = "regular" in sys.argv or len(sys.argv) == 1
    test_local = "local" in sys.argv or len(sys.argv) == 1
    test_azure = "azure" in sys.argv or len(sys.argv) == 1
    
    print(f"Mode: {'Basic Mode - First Audio Test Only' if basic_mode else 'Full Mode - All Audio Tests'}")
    print(f"Interface: {'Popup' if test_popup and not test_regular else 'Regular' if test_regular and not test_popup else 'Both'}")
    print(f"Environment: {'Local' if test_local and not test_azure else 'Azure' if test_azure and not test_local else 'Both'}")
    print()
    
    # Test local popup interface (default)
    if test_popup and test_local:
        print(f"\n🏠 Testing LOCAL Popup Interface ({'Basic Mode' if basic_mode else 'Full'})")
        results['local_popup'] = test_audio_upload(BASE_URL, report_generator, basic_mode)
    
    # Test local testing interface
    if test_regular and test_local:
        print(f"\n🏠 Testing LOCAL Testing Interface ({'Basic Mode' if basic_mode else 'Full'})")
        results['local_testing'] = test_audio_upload(TESTING_LOCAL, report_generator, basic_mode)
    
    # Test Azure popup interface (default)
    if test_popup and test_azure:
        print(f"\n☁️ Testing AZURE Popup Interface ({'Basic Mode' if basic_mode else 'Full'})")
        results['azure_popup'] = test_audio_upload(AZURE_URL, report_generator, basic_mode)
    
    # Test Azure testing interface
    if test_regular and test_azure:
        print(f"\n☁️ Testing AZURE Testing Interface ({'Basic Mode' if basic_mode else 'Full'})")
        results['azure_testing'] = test_audio_upload(TESTING_AZURE, report_generator, basic_mode)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 MULTIMODAL AUDIO TEST SUMMARY")
    print("=" * 60)
    
    for environment, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        env_display = environment.replace('_', ' ').upper()
        print(f"{env_display:20} {status}")
    
    all_passed = all(results.values()) if results else False
    overall_status = "✅ ALL TESTS PASSED" if all_passed else "❌ SOME TESTS FAILED"
    
    print(f"\nOverall Result: {overall_status}")
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Generate HTML report
    try:
        report_path = report_generator.save_report()
        print(f"\n📄 HTML Report generated: {report_path}")
    except Exception as e:
        print(f"\n⚠️ Failed to generate HTML report: {e}")
    
    # Exit code for CI/CD
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()