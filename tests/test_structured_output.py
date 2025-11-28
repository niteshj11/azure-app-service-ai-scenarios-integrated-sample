#!/usr/bin/env python3
"""
Test Structured Output Scenario
Tests JSON/structured data generation capabilities
"""

import requests
import json
import sys
import time
import os
from datetime import datetime
from html_report_generator import HTMLReportGenerator
from bs4 import BeautifulSoup

# Add project root to path for imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from test_config import BASE_URL, AZURE_URL, TESTING_LOCAL, TESTING_AZURE

def test_structured_output(base_url, report_generator=None, basic_mode=False):
    """Test structured output generation"""
    print(f"\n📋 Testing Structured Output - {base_url} ({'Basic Mode' if basic_mode else 'Full Mode'})")
    
    session = requests.Session()
    environment = "local" if "127.0.0.1" in base_url else "azure"
    
    try:
        # Test 1: Get initial page
        print("1. Loading chat interface...")
        response = session.get(base_url, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Failed to load page: {response.status_code}")
        
        print("   ✅ Interface loaded successfully")
        
        # Test 2: JSON structure requests
        print("2. Testing JSON output generation...")
        
        # Zava structured output scenarios from Manual Testing Guide
        json_requests = [
            {
                "message": "Generate a complete JSON product catalog entry for the Zava UltraGame Elite 15 including all technical specifications and metadata.",
                "scenario": "Test 7: Product Catalog JSON Generation",
                "expected_keywords": ["json", "ultragame", "elite", "15", "1899", "rtx", "4070", "ti", "amd", "ryzen", "9", "7900hx", "32gb", "ram", "1tb", "ssd", "zava", "gaming"],
                "validation_criteria": ["response contains valid JSON", "includes UltraGame Elite 15 specs", "mentions $1899 price", "contains RTX 4070 Ti and AMD Ryzen specifications"]
            },
            {
                "message": "Create a structured customer data format for John Smith, a business client who purchased 5 laptops, needs support contact, and has premium service plan.",
                "scenario": "Test 8: Customer Data Structure",
                "expected_keywords": ["customer", "data", "john", "smith", "business", "client", "laptops", "support", "service", "plan", "zava", "enterprise", "contact"],
                "validation_criteria": ["customer data properly structured", "purchase details included", "Zava enterprise context", "contact information structured"]
            },
            {
                "message": "Design a structured inventory report format showing current stock levels, reorder points, and supplier information for Zava's laptop category.",
                "scenario": "Test 9: Inventory Report Structure",
                "expected_keywords": ["inventory", "report", "stock", "levels", "reorder", "points", "supplier", "zava", "laptop", "sku", "operations", "management"],
                "validation_criteria": ["report structure defined", "stock level fields included", "Zava operations context", "supplier information structured"]
            }
        ]
        
        # Apply basic mode filtering if enabled
        requests_to_test = json_requests[:1] if basic_mode else json_requests
        print(f"   Running {'1 (first)' if basic_mode else 'all'} structured output test(s)")
        
        for i, request_data in enumerate(requests_to_test, 1):
            print(f"   Testing scenario {i}: {request_data['scenario']}")
            
            start_time = time.time()
            data = {'message': request_data['message']}
            response = session.post(base_url, data=data, timeout=45)
            duration = time.time() - start_time
            
            if response.status_code not in [200, 302]:
                raise Exception(f"Failed to process structured output request: {response.status_code}")
            
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
            else:
                # No real AI response found
                ai_response = f"ERROR: No AI structured output response found for {request_data['scenario']}. Interface structure may have changed."
            
            # Perform relevance analysis for Zava structured output
            expected_keywords = request_data['expected_keywords']
            response_lower = ai_response.lower()
            found_keywords = [keyword for keyword in expected_keywords if keyword in response_lower]
            relevance_score = len(found_keywords) / len(expected_keywords) * 100
            
            # Look for structured output indicators
            structure_indicators = ['json', '{', '}', '[', ']', 'structure', 'format', 'table', 'data', 'field']
            found_structure = [indicator for indicator in structure_indicators if indicator in response_lower]
            
            if relevance_score >= 50 and found_structure:
                print(f"   ✅ Scenario {i}: HIGH structured output quality ({relevance_score:.1f}%, {len(found_structure)} structure indicators)")
                status = "PASSED"
            elif relevance_score >= 30 or found_structure:
                print(f"   ⚠️ Scenario {i}: MEDIUM structured output quality ({relevance_score:.1f}%, {len(found_structure)} structure indicators)")
                status = "PASSED"
            else:
                print(f"   ❌ Scenario {i}: LOW structured output quality ({relevance_score:.1f}%, no structure indicators)")
                status = "FAILED"
            
            # Add detailed analysis to the AI response
            analysis_text = f"\n\n[STRUCTURED OUTPUT ANALYSIS]\n"
            analysis_text += f"• Expected Keywords: {', '.join(expected_keywords)}\n"
            analysis_text += f"• Found Keywords: {', '.join(found_keywords)}\n"
            analysis_text += f"• Structure Indicators: {', '.join(found_structure)}\n"
            analysis_text += f"• Relevance Score: {relevance_score:.1f}%\n"
            analysis_text += f"• Structure Quality: {'Strong structured format' if relevance_score >= 50 else 'Moderate structure' if relevance_score >= 30 else 'Limited structure formatting'}"
            
            enhanced_response = ai_response + analysis_text
            
            # Add to report
            if report_generator:
                report_generator.add_test_result(
                    scenario=f"Zava Structured: {request_data['scenario']}",
                    input_data={
                        "message": request_data['message'],
                        "scenario_type": request_data['scenario'],
                        "test_type": "zava_structured_output",
                        "expected_keywords": expected_keywords,
                        "validation_criteria": request_data['validation_criteria']
                    },
                    output_data=enhanced_response,
                    status=status,
                    duration=duration,
                    environment=environment,
                    response_code=response.status_code
                )
            
            time.sleep(3)  # Brief delay for processing
        
        # Test 3: Table format requests
        print("3. Testing table format generation...")
        
        table_requests = [
            {
                "message": "Create a comparison table of Zava's 3 service tiers: Basic ($50/month), Professional ($150/month), Enterprise ($400/month). Include features, support level, and limits for each tier. Format as a clear table.",
                "indicators": ["basic", "professional", "enterprise", "month", "features", "support", "|", "-"]
            },
            {
                "message": "Generate a product inventory table with columns: Product ID, Product Name, Stock Quantity, Unit Price, Total Value. Include 4 sample products with realistic data.",
                "indicators": ["product", "stock", "quantity", "price", "total", "value", "|", "-"]
            }
        ]
        
        for i, request_data in enumerate(table_requests, 1):
            print(f"   Testing table request {i}...")
            
            data = {'message': request_data['message']}
            response = session.post(base_url, data=data, timeout=45)
            
            if response.status_code not in [200, 302]:
                raise Exception(f"Failed to process table request: {response.status_code}")
            
            # Check for table indicators
            response_text = response.text.lower()
            found_indicators = sum(1 for indicator in request_data['indicators'] if indicator in response_text)
            
            if found_indicators >= len(request_data['indicators']) // 2:
                print(f"   ✅ Table request {i} shows structured format ({found_indicators} indicators)")
            else:
                print(f"   ⚠️ Table request {i} may lack clear structure ({found_indicators} indicators)")
            
            time.sleep(2)
        
        # Test 4: List format requests
        print("4. Testing list format generation...")
        
        list_message = "Create a numbered action plan for implementing a new customer loyalty program at Zava. Include 8 specific steps with clear priorities and timelines."
        
        data = {'message': list_message}
        response = session.post(base_url, data=data, timeout=45)
        
        if response.status_code not in [200, 302]:
            raise Exception(f"Failed to process list request: {response.status_code}")
        
        # Check for list structure
        list_indicators = ["1.", "2.", "3.", "step", "action", "timeline", "priority", "loyalty", "program"]
        response_text = response.text.lower()
        found_list_indicators = sum(1 for indicator in list_indicators if indicator in response_text)
        
        if found_list_indicators >= 5:
            print("   ✅ List format shows clear structure")
        else:
            print("   ⚠️ List format unclear")
        
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
    """Run structured output tests on both regular and popup interfaces"""
    print("=" * 60)
    print("📋 STRUCTURED OUTPUT SCENARIO TEST")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize HTML report generator
    report_generator = HTMLReportGenerator("Structured Output Scenario Test")
    
    results = {}
    
    # Test interfaces based on command line arguments
    basic_mode = "basic" in sys.argv
    test_popup = "popup" in sys.argv or len(sys.argv) == 1
    test_regular = "regular" in sys.argv or len(sys.argv) == 1
    test_local = "local" in sys.argv or len(sys.argv) == 1
    test_azure = "azure" in sys.argv or len(sys.argv) == 1
    
    print(f"Mode: {'Basic Mode - First Structured Output Test Only' if basic_mode else 'Full Mode - All Structured Output Tests'}")
    print(f"Interface: {'Popup' if test_popup and not test_regular else 'Regular' if test_regular and not test_popup else 'Both'}")
    print(f"Environment: {'Local' if test_local and not test_azure else 'Azure' if test_azure and not test_local else 'Both'}")
    print()
    
    # Test local popup interface (default)
    if test_popup and test_local:
        print(f"\n🏠 Testing LOCAL Popup Interface ({'Basic Mode' if basic_mode else 'Full'})")
        results['local_popup'] = test_structured_output(BASE_URL, report_generator, basic_mode)
    
    # Test local testing interface
    if test_regular and test_local:
        print(f"\n🏠 Testing LOCAL Testing Interface ({'Basic Mode' if basic_mode else 'Full'})")
        results['local_testing'] = test_structured_output(TESTING_LOCAL, report_generator, basic_mode)
    
    # Test Azure popup interface (default)
    if test_popup and test_azure:
        print(f"\n☁️ Testing AZURE Popup Interface ({'Basic Mode' if basic_mode else 'Full'})")
        results['azure_popup'] = test_structured_output(AZURE_URL, report_generator, basic_mode)
    
    # Test Azure testing interface
    if test_regular and test_azure:
        print(f"\n☁️ Testing AZURE Testing Interface ({'Basic Mode' if basic_mode else 'Full'})")
        results['azure_testing'] = test_structured_output(TESTING_AZURE, report_generator, basic_mode)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 STRUCTURED OUTPUT TEST SUMMARY")
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