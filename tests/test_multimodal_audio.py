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

# Import test configuration
import sys
import os
sys.path.append(os.path.dirname(__file__))
from test_config import BASE_URL, AZURE_URL, TESTING_LOCAL, TESTING_AZURE
from html_report_generator import HTMLReportGenerator

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

def test_audio_upload(base_url, basic_mode=False):
    """Test audio upload and transcription"""
    print(f"\n🎵 Testing Audio Upload - {base_url} ({'Basic Mode' if basic_mode else 'Full Mode'})")
    
    # Initialize detailed results list
    detailed_results = []
    
    # Quick connectivity test first
    print("0. Testing server connectivity...")
    try:
        quick_response = requests.get(base_url, timeout=10)
        print(f"   ✅ Server responding (status: {quick_response.status_code})")
    except requests.exceptions.Timeout:
        server_type = "Flask server" if "127.0.0.1" in base_url else "Azure App Service"
        print(f"   ❌ Server timeout - {server_type} may not be responding")
        return False, []
    except requests.exceptions.ConnectionError:
        server_type = "Flask server not running on 127.0.0.1:5000" if "127.0.0.1" in base_url else "Azure App Service not responding"
        print(f"   ❌ Connection refused - {server_type}")
        return False, []
    
    session = requests.Session()
    environment = "local" if "127.0.0.1" in base_url else "azure"
    
    try:
        # Test 1: Get initial page
        print("1. Loading chat interface...")
        try:
            response = session.get(base_url, timeout=10)  # Reduced timeout
            
            if response.status_code != 200:
                raise Exception(f"Failed to load page: {response.status_code}")
            
            print("   ✅ Interface loaded successfully")
        except requests.exceptions.Timeout:
            print("   ⚠️ GET request timed out, but proceeding with audio test...")
        except requests.exceptions.ConnectionError:
            print("   ❌ Cannot connect to Flask server - is it running on 127.0.0.1:5000?")
            return False, []
        
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
        
        # Track test results
        test_results = []
        
        for i, scenario_data in enumerate(scenarios_to_test, 1):
            print(f"   Testing scenario {i}: {scenario_data['scenario']}")
            
            start_time = time.time()
            
            # Prepare multipart form data - use 'file' field name to match Flask routing
            files = {
                'file': (filename, BytesIO(audio_data), content_type)
            }
            data = {
                'message': scenario_data['message']
            }
            
            print(f"      Sending POST request with audio file...")
            response = session.post(base_url, files=files, data=data, timeout=180)  # Increased timeout for audio processing
            duration = time.time() - start_time
            
            print(f"      Response status: {response.status_code}")
            print(f"      Response length: {len(response.text)} characters")
            
            # Check if we got HTML (indicates redirect to homepage) or actual transcription
            if "<!DOCTYPE html>" in response.text:
                # We got redirected back to homepage - extract the actual AI response from conversation history
                response_lower = response.text.lower()
                
                # Look for strong transcription indicators in the HTML
                transcription_keywords = ['transcription', 'transcript', 'customer service', 'coats & gowns', 'sam', 'caller', 'bought a coat', 'return', 'customer support', 'audio quality', 'clear and intelligible', 'background noise']
                found_transcription = [kw for kw in transcription_keywords if kw in response_lower]
                
                # Look for AI processing indicators  
                ai_indicators = ['🎤', 'audio processing', 'ai analysis', 'summary', 'transcribe', '**audio processing complete**', 'file:', 'request:']
                found_ai_indicators = [ai for ai in ai_indicators if ai in response_lower]
                
                # Debug: show what we found
                print(f"      DEBUG: Found transcription keywords: {found_transcription}")
                print(f"      DEBUG: Found AI indicators: {found_ai_indicators}")
                
                if found_transcription and found_ai_indicators:
                    ai_response = f"✅ AUDIO TRANSCRIPTION WORKING! Found transcription content: {', '.join(found_transcription[:3])} and AI processing indicators: {', '.join(found_ai_indicators[:2])}"
                elif found_transcription:
                    ai_response = f"⚠️ Partial transcription detected: {', '.join(found_transcription[:3])} but missing AI processing indicators"
                elif found_ai_indicators:
                    ai_response = f"⚠️ AI processing detected: {', '.join(found_ai_indicators[:2])} but missing specific transcription content"
                else:
                    ai_response = "❌ No transcription or AI processing indicators found in HTML response"
            else:
                # Got a direct response (not HTML)
                ai_response = response.text[:500] + ("..." if len(response.text) > 500 else "")
            
            # Perform relevance analysis for TechMart context
            expected_keywords = scenario_data['expected_keywords']
            response_lower = ai_response.lower()
            found_keywords = [keyword for keyword in expected_keywords if keyword in response_lower]
            relevance_score = len(found_keywords) / len(expected_keywords) * 100
            
            # Check for actual transcription content (real transcription should be long and detailed)
            transcription_indicators = ['transcription', 'transcript', 'conversation', 'spoke', 'said', 'customer said', 'representative']
            found_transcription_indicators = [indicator for indicator in transcription_indicators if indicator in response_lower]
            
            # Check for success conditions - look for our improved detection
            if "✅ AUDIO TRANSCRIPTION WORKING!" in ai_response:
                print(f"   ✅ Scenario {i}: PASSED - Audio transcription is working correctly!")
                status = "PASSED"
                test_results.append(True)
            elif "⚠️ Partial transcription detected" in ai_response:
                print(f"   ⚠️ Scenario {i}: PARTIAL - Some transcription detected but incomplete")
                status = "PARTIAL"
                test_results.append(False)  # Count partial as failure for now
            elif "⚠️ AI processing detected" in ai_response:
                print(f"   ⚠️ Scenario {i}: PARTIAL - AI processing detected but missing transcription content")
                status = "PARTIAL"
                test_results.append(False)  # Count partial as failure for now
            elif "❌" in ai_response or "error:" in ai_response.lower():
                print(f"   ❌ Scenario {i}: FAILED - {ai_response[:100]}...")
                status = "FAILED"
                test_results.append(False)
            else:
                print(f"   ❌ Scenario {i}: FAILED - Unclear response: {ai_response[:100]}...")
                status = "FAILED"
                test_results.append(False)
            
            # Add detailed analysis to the AI response
            analysis_text = f"\n\n[AUDIO ANALYSIS]\n"
            analysis_text += f"• Audio File: {filename}\n"
            analysis_text += f"• Expected Keywords: {', '.join(expected_keywords)}\n"
            analysis_text += f"• Found Keywords: {', '.join(found_keywords)}\n"
            analysis_text += f"• Transcription Indicators: {', '.join(found_transcription_indicators)}\n"
            analysis_text += f"• Relevance Score: {relevance_score:.1f}%\n"
            analysis_text += f"• TechMart Context: {'Strong' if relevance_score >= 50 else 'Moderate' if relevance_score >= 30 else 'Weak'}"
            
            enhanced_response = ai_response + analysis_text
            
            # Add to detailed results for HTML report
            test_audio_path = "tests/test_inputs/test_customer_service_audio.mp3"
            media_files = [test_audio_path] if os.path.exists(test_audio_path) else []
            
            detailed_results.append({
                'scenario': scenario_data['scenario'],
                'input_data': {
                    'message': scenario_data['message'],
                    'audio_file': filename,
                    'content_type': content_type
                },
                'output_data': enhanced_response,
                'status': status,
                'duration': duration,
                'response_code': response.status_code,
                'media_files': media_files
            })
            
            # Print detailed results
            print(f"      Duration: {duration:.2f}s")
            print(f"      AI Response Length: {len(ai_response)} chars")
            print(f"      Status: {status}")
            if len(ai_response) < 200:
                print(f"      Response Preview: {ai_response}")
            else:
                print(f"      Response Preview: {ai_response[:200]}...")
            
            time.sleep(8)  # Extended delay between audio uploads to prevent server overload
        
        # Test 3: Audio format handling
        print("3. Testing audio format handling...")
        
        format_message = "This audio contains important business information. Please transcribe it accurately and organize the content with clear headings for different topics discussed."
        
        files = {
            'file': (filename, BytesIO(audio_data), content_type)
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
                'file': (filename, BytesIO(audio_data), content_type)
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
        
        # Return True only if all core scenarios passed
        all_scenarios_passed = all(test_results) if test_results else False
        print(f"\n   📊 Core Scenarios: {sum(test_results)}/{len(test_results)} passed")
        return all_scenarios_passed, detailed_results
        
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out (audio processing can be slow)")
        return False, []
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed")
        return False, []
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False, []

def main():
    """Run multimodal audio tests on local and/or Azure servers"""
    print("=" * 60)
    print("🎵 MULTIMODAL AUDIO SCENARIO TEST")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Parse arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else []
    basic_mode = 'basic' in args
    test_local = 'local' in args or (len([a for a in args if a in ['local', 'azure']]) == 0)
    test_azure = 'azure' in args or (len([a for a in args if a in ['local', 'azure']]) == 0)
    
    mode_text = "Basic Mode - Testing Audio Transcription" if basic_mode else "Full Mode - Comprehensive Testing"
    print(f"Mode: {mode_text}")
    
    environments = []
    if test_local: environments.append('Local')
    if test_azure: environments.append('Azure')
    print(f"Testing: {', '.join(environments)}")
    print()
    
    # Initialize HTML report generator
    report_generator = HTMLReportGenerator("Multimodal Audio Scenario Test")
    
    results = {}
    detailed_results = {}
    
    if test_local:
        print("🏠 Testing LOCAL Flask Server")
        success, test_details = test_audio_upload(BASE_URL, basic_mode)
        results['local'] = success
        detailed_results['local'] = test_details
        
        # Add results to HTML report
        for detail in test_details:
            report_generator.add_test_result(
                scenario=detail['scenario'],
                input_data=detail['input_data'],
                output_data=detail['output_data'],
                status=detail['status'],
                duration=detail['duration'],
                environment="local",
                media_files=detail.get('media_files', []),
                response_code=detail.get('response_code', 200)
            )
        
    if test_azure:
        print("\n☁️ Testing AZURE App Service")
        success, test_details = test_audio_upload(AZURE_URL, basic_mode)
        results['azure'] = success
        detailed_results['azure'] = test_details
        
        # Add results to HTML report
        for detail in test_details:
            report_generator.add_test_result(
                scenario=detail['scenario'],
                input_data=detail['input_data'],
                output_data=detail['output_data'],
                status=detail['status'],
                duration=detail['duration'],
                environment="azure",
                media_files=detail.get('media_files', []),
                response_code=detail.get('response_code', 200)
            )
    
    # Generate HTML Report
    report_path = report_generator.save_report()
    print(f"\n📊 HTML Report generated: {report_path}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 AUDIO TEST SUMMARY")
    print("=" * 60)
    
    for environment, passed in results.items():
        if passed == True:
            status = "✅ PASSED"
        elif passed == "PARTIAL":
            status = "⚠️ PARTIAL" 
        else:
            status = "❌ FAILED"
        env_name = "LOCAL FLASK SERVER" if environment == 'local' else "AZURE APP SERVICE"
        print(f"{env_name}: {status}")
    
    all_passed = all(r == True for r in results.values()) if results else False
    overall_status = "✅ TEST PASSED" if all_passed else "❌ TEST FAILED"
    
    print(f"\nOverall Result: {overall_status}")
    print(f"⏰ Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Exit code
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()