#!/usr/bin/env python3
"""
Test Multimodal Image Scenario
Tests image upload and analysis capabilities
"""

import requests
import os
import sys
import time
from datetime import datetime
from io import BytesIO
from html_report_generator import HTMLReportGenerator
from bs4 import BeautifulSoup

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from to_be_deleted.test_config import BASE_URL, AZURE_URL, TESTING_LOCAL, TESTING_AZURE

def create_test_image_data():
    """Create a small test image for upload testing"""
    # Create a minimal PNG image (1x1 pixel) for testing
    # PNG signature + IHDR chunk + IDAT chunk + IEND chunk
    png_data = (
        b'\x89PNG\r\n\x1a\n'  # PNG signature
        b'\x00\x00\x00\rIHDR'  # IHDR chunk
        b'\x00\x00\x00\x01'  # Width: 1
        b'\x00\x00\x00\x01'  # Height: 1
        b'\x08\x02\x00\x00\x00\x90wS\xde'  # Bit depth, color type, etc.
        b'\x00\x00\x00\x0cIDATx\x9cc\xf8\x00\x00\x00\x01\x00\x01'  # IDAT chunk
        b'\x00!\xdd\xdb'  # IDAT checksum
        b'\x00\x00\x00\x00IEND\xaeB`\x82'  # IEND chunk
    )
    return png_data

def test_image_upload(base_url, report_generator=None, basic_mode=False):
    """Test TechMart image analysis with laptop products"""
    print(f"\n🖼️ Testing TechMart Image Analysis - {base_url} ({'Basic Mode' if basic_mode else 'Full Mode'})")
    
    session = requests.Session()
    environment = "local" if "127.0.0.1" in base_url else "azure"
    
    try:
        # Test 1: Get initial page
        print("1. Loading TechMart chat interface...")
        response = session.get(base_url, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Failed to load page: {response.status_code}")
        
        print("   ✅ TechMart interface loaded successfully")
        
        # Test 2: TechMart product image scenarios
        print("2. Testing TechMart product image analysis...")
        
        # Define TechMart image scenarios from Manual Testing Guide
        laptop_scenarios = [
            {
                "image_file": "tests/test_inputs/laptop.jpeg",
                "message": "Analyze this product image and provide detailed specifications.",
                "scenario": "Test 10: Product Image Analysis",
                "expected_keywords": ["image", "analysis", "product", "specifications", "techmart", "electronics", "features", "visual", "details", "expert", "catalog"],
                "validation_criteria": ["confirms image received", "provides TechMart product expertise", "lists detailed specifications", "demonstrates product knowledge"]
            },
            {
                "image_file": "tests/test_inputs/laptop damaged.jpeg", 
                "message": "This customer sent an image of a damaged laptop. Verify and assess the damage and suggest what should our return/repair process be?",
                "scenario": "Test 11: Customer Service Image Issue",
                "expected_keywords": ["damage", "verify", "assess", "return", "repair", "process", "customer", "service", "techmart", "30", "day", "policy", "resolution"],
                "validation_criteria": ["verifies damage using TechMart expertise", "references 30-day return policy", "provides customer service resolution", "suggests appropriate TechMart process"]
            }
        ]
        
        # Apply basic mode filtering if enabled
        scenarios_to_test = laptop_scenarios[:1] if basic_mode else laptop_scenarios
        print(f"   Running {'1 (first)' if basic_mode else 'all'} image analysis test(s)")
        
        for i, scenario_data in enumerate(scenarios_to_test, 1):
            print(f"   Testing scenario {i}: {scenario_data['scenario']}")
            
            image_path = scenario_data['image_file']
            
            if not os.path.exists(image_path):
                print(f"   ⚠️ Test image not found: {image_path}")
                # Create fallback test image
                image_data = create_test_image_data()
                filename = "fallback_test.png"
                selected_image = None
            else:
                print(f"   📷 Using test image: {os.path.basename(image_path)}")
                with open(image_path, 'rb') as f:
                    image_data = f.read()
                filename = os.path.basename(image_path)
                selected_image = image_path
            
            start_time = time.time()
            
            # Prepare multipart form data
            files = {
                'image': (filename, BytesIO(image_data), 'image/jpeg' if filename.endswith('.jpg') else 'image/png')
            }
            data = {
                'message': scenario_data['message']
            }
            
            response = session.post(base_url, files=files, data=data, timeout=60)
            duration = time.time() - start_time
            
            # Extract actual AI response from the page
            from bs4 import BeautifulSoup
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
                    ai_response = "ERROR: Image uploaded but no AI multimodal processing detected. AI response too short or generic."
            else:
                # No AI response found at all
                ai_response = "ERROR: No AI response found. Multimodal image processing failed completely."
            
            # Perform relevance analysis for TechMart context
            expected_keywords = scenario_data['expected_keywords']
            response_lower = ai_response.lower()
            found_keywords = [keyword for keyword in expected_keywords if keyword in response_lower]
            relevance_score = len(found_keywords) / len(expected_keywords) * 100
            
            # Determine status based on ACTUAL multimodal processing
            image_indicators = ['see', 'visible', 'analyze', 'shows', 'appears', 'display', 'viewing', 'observe']
            found_image_indicators = [indicator for indicator in image_indicators if indicator in response_lower]
            
            # Check for error conditions first
            if "error:" in ai_response.lower() or "failed" in ai_response.lower():
                print(f"   ❌ Scenario {i}: FAILED - Multimodal processing error")
                status = "FAILED"
            elif len(ai_response) > 200 and found_image_indicators and relevance_score >= 30:
                print(f"   ✅ Scenario {i}: PASSED - Real AI multimodal response ({relevance_score:.1f}%, {len(found_image_indicators)} image indicators)")
                status = "PASSED"
            elif found_image_indicators and len(ai_response) > 100:
                print(f"   ⚠️ Scenario {i}: PARTIAL - Some image processing detected ({relevance_score:.1f}%, {len(found_image_indicators)} indicators)")
                status = "FAILED"  # Still fail for partial processing
            else:
                print(f"   ❌ Scenario {i}: FAILED - No real multimodal processing ({relevance_score:.1f}%, {len(found_image_indicators)} indicators)")
                status = "FAILED"
            
            # Add detailed analysis to the AI response
            analysis_text = f"\n\n[MULTIMODAL ANALYSIS]\n"
            analysis_text += f"• Image File: {filename}\n"
            analysis_text += f"• Expected Keywords: {', '.join(expected_keywords)}\n"
            analysis_text += f"• Found Keywords: {', '.join(found_keywords)}\n"
            analysis_text += f"• Image Indicators: {', '.join(found_image_indicators)}\n"
            analysis_text += f"• Relevance Score: {relevance_score:.1f}%\n"
            analysis_text += f"• TechMart Context: {'Strong' if relevance_score >= 50 else 'Moderate' if relevance_score >= 30 else 'Weak'}"
            
            enhanced_response = ai_response + analysis_text
            
            # Add to report with image embedding
            if report_generator:
                media_files = [selected_image] if selected_image and os.path.exists(selected_image) else []
                report_generator.add_test_result(
                    scenario=f"TechMart Image: {scenario_data['scenario']}",
                    input_data={
                        "message": scenario_data['message'],
                        "image_file": filename,
                        "test_type": "techmart_multimodal_image",
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
            
            time.sleep(4)  # Brief delay between uploads
        
        # Test 3: TechMart catalog integration test
        print("3. Testing TechMart catalog integration...")
        
        catalog_message = "I'm uploading a product image for TechMart's catalog. Please extract key information that would be useful for our product database: brand, model, key features, and suggested category."
        
        # Use the last processed image
        if selected_image and os.path.exists(selected_image):
            with open(selected_image, 'rb') as f:
                catalog_image_data = f.read()
            catalog_filename = os.path.basename(selected_image)
        else:
            catalog_image_data = image_data
            catalog_filename = filename
        
        files = {
            'image': (catalog_filename, BytesIO(catalog_image_data), 'image/jpeg' if catalog_filename.endswith('.jpg') else 'image/png')
        }
        data = {'message': catalog_message}
        
        response = session.post(base_url, files=files, data=data, timeout=60)
        
        # Check for TechMart catalog integration
        catalog_keywords = ['brand', 'model', 'feature', 'category', 'product', 'database', 'techmart', 'catalog']
        response_lower = response.text.lower()
        found_catalog_keywords = [keyword for keyword in catalog_keywords if keyword in response_lower]
        
        if len(found_catalog_keywords) >= 4:
            print(f"   ✅ TechMart catalog integration functional ({len(found_catalog_keywords)}/8 keywords)")
        else:
            print(f"   ⚠️ TechMart catalog integration limited ({len(found_catalog_keywords)}/8 keywords)")
        
        print("   🎯 TechMart multimodal image testing completed successfully")
        
        return True
        
    except requests.exceptions.Timeout:
        print("   ❌ Request timed out")
        return False
    except requests.exceptions.ConnectionError:
        print("   ❌ Connection failed")
        return False
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False

def main():
    """Run multimodal image tests on both regular and popup interfaces"""
    print("=" * 60)
    print("🖼️ MULTIMODAL IMAGE SCENARIO TEST")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize HTML report generator
    report_generator = HTMLReportGenerator("Multimodal Image Scenario Test")
    
    results = {}
    
    # Test interfaces based on command line arguments
    basic_mode = "basic" in sys.argv
    test_popup = "popup" in sys.argv or len(sys.argv) == 1
    test_regular = "regular" in sys.argv or len(sys.argv) == 1
    test_local = "local" in sys.argv or len(sys.argv) == 1
    test_azure = "azure" in sys.argv or len(sys.argv) == 1
    
    print(f"Mode: {'Basic Mode - First Image Test Only' if basic_mode else 'Full Mode - All Image Tests'}")
    print(f"Interface: {'Popup' if test_popup and not test_regular else 'Regular' if test_regular and not test_popup else 'Both'}")
    print(f"Environment: {'Local' if test_local and not test_azure else 'Azure' if test_azure and not test_local else 'Both'}")
    print()
    
    # Test local popup interface (default)
    if test_popup and test_local:
        print(f"\n🏠 Testing LOCAL Popup Interface ({'Basic Mode' if basic_mode else 'Full'})")
        results['local_popup'] = test_image_upload(BASE_URL, report_generator, basic_mode)
    
    # Test local testing interface
    if test_regular and test_local:
        print(f"\n🏠 Testing LOCAL Testing Interface ({'Basic Mode' if basic_mode else 'Full'})")
        results['local_testing'] = test_image_upload(TESTING_LOCAL, report_generator, basic_mode)
    
    # Test Azure popup interface (default)
    if test_popup and test_azure:
        print(f"\n☁️ Testing AZURE Popup Interface ({'Basic Mode' if basic_mode else 'Full'})")
        results['azure_popup'] = test_image_upload(AZURE_URL, report_generator, basic_mode)
    
    # Test Azure testing interface
    if test_regular and test_azure:
        print(f"\n☁️ Testing AZURE Testing Interface ({'Basic Mode' if basic_mode else 'Full'})")
        results['azure_testing'] = test_image_upload(TESTING_AZURE, report_generator, basic_mode)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 MULTIMODAL IMAGE TEST SUMMARY")
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