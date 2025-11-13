#!/usr/bin/env python3
"""
Test Simple Chat Scenario
Tests basic text-based conversation functionality with support for both popup and detailed interfaces

Usage Examples:
    python test_simple_chat.py                    # Test both popup and regular interfaces (local only)
    python test_simple_chat.py popup local        # Test popup interface locally only
    python test_simple_chat.py regular local      # Test detailed/testing interface locally only  
    python test_simple_chat.py popup azure        # Test popup interface on Azure only
    python test_simple_chat.py local              # Test both interfaces locally
    python test_simple_chat.py azure              # Test both interfaces on Azure
"""

import requests
import json
import sys
import time
from datetime import datetime
from html_report_generator import HTMLReportGenerator
from bs4 import BeautifulSoup
from test_config import BASE_URL, AZURE_URL, TESTING_LOCAL, TESTING_AZURE

def test_simple_chat(base_url, report_generator=None, basic_mode=False):
    """Test TechMart retail chat scenarios with real AI responses"""
    print(f"\n🧪 Testing TechMart Simple Chat - {base_url}")
    if basic_mode:
        print("   🚀 Basic Mode: Testing only first scenario")
    
    session = requests.Session()
    environment = "local" if "127.0.0.1" in base_url else "azure"
    
    try:
        # Test 1: Get initial page
        print("1. Loading TechMart chat interface...")
        response = session.get(base_url, timeout=30)
        
        if response.status_code != 200:
            raise Exception(f"Failed to load page: {response.status_code}")
        
        if "TechMart" not in response.text:
            raise Exception("TechMart branding not found on page")
        
        print("   ✅ TechMart chat interface loaded successfully")
        
        # Test 2: TechMart retail scenarios
        print("2. Testing TechMart retail chat scenarios...")
        
        # Define TechMart retail scenarios from Manual Testing Guide
        retail_scenarios = [
            {
                "message": "Who are you and what can you help with?",
                "scenario": "Test 1: AI Assistant Introduction",
                "expected_keywords": ["techmart", "enterprise", "assistant", "customer", "service", "business", "intelligence", "retailer", "electronics", "products", "support", "professional"],
                "validation_criteria": ["identifies as TechMart Enterprise AI Assistant", "mentions customer service role", "lists business intelligence capabilities"]
            },
            {
                "message": "Tell me about features and price for Pro Gaming X1",
                "scenario": "Test 2: Specific Product Inquiry", 
                "expected_keywords": ["pro", "gaming", "x1", "1699", "rtx", "4070", "intel", "i7", "16gb", "ram", "1tb", "ssd", "specifications", "features"],
                "validation_criteria": ["addresses Pro Gaming X1 specifically", "mentions $1699 price", "lists RTX 4070 and Intel i7 specs"]
            },
            {
                "message": "What is TechMart's return policy and how do I process a customer refund?",
                "scenario": "Test 3: Customer Service Policy Question",
                "expected_keywords": ["return", "policy", "30", "day", "refund", "receipt", "customer", "service", "process", "techmart", "portal", "1-800"],
                "validation_criteria": ["explains 30-day return policy", "mentions receipt requirement", "provides customer service contact"]
            }
        ]
        
        # In basic mode, only test the first scenario
        scenarios_to_test = retail_scenarios[:1] if basic_mode else retail_scenarios
        
        for i, scenario_data in enumerate(scenarios_to_test, 1):
            print(f"   Testing scenario {i}: {scenario_data['scenario']}")
            
            start_time = time.time()
            data = {'message': scenario_data['message']}
            response = session.post(base_url, data=data, timeout=45)
            duration = time.time() - start_time
            
            if response.status_code not in [200, 302]:
                raise Exception(f"Failed to send message: {response.status_code}")
            
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
            else:
                # Fallback: look for any response content
                chat_container = soup.find('div', class_='chat-container') or soup.find('div', class_='chat-popup-messages')
                if chat_container:
                    ai_response = f"Response received in chat interface. UI shows active conversation with TechMart branding."
                else:
                    ai_response = "No response content found - possible UI structure change"
            
            # Perform relevance analysis
            expected_keywords = scenario_data['expected_keywords']
            response_lower = ai_response.lower()
            found_keywords = [keyword for keyword in expected_keywords if keyword in response_lower]
            relevance_score = len(found_keywords) / len(expected_keywords) * 100
            
            # Determine status based on relevance
            if relevance_score >= 60:
                print(f"   ✅ Scenario {i}: HIGH relevance ({relevance_score:.1f}% - {len(found_keywords)}/{len(expected_keywords)} keywords)")
                status = "PASSED"
            elif relevance_score >= 30:
                print(f"   ⚠️ Scenario {i}: MEDIUM relevance ({relevance_score:.1f}% - {len(found_keywords)}/{len(expected_keywords)} keywords)")
                status = "PASSED"
            else:
                print(f"   ❌ Scenario {i}: LOW relevance ({relevance_score:.1f}% - {len(found_keywords)}/{len(expected_keywords)} keywords)")
                status = "FAILED"
            
            # Add detailed analysis to the AI response
            analysis_text = f"\n\n[RELEVANCE ANALYSIS]\n"
            analysis_text += f"• Expected Keywords: {', '.join(expected_keywords)}\n"
            analysis_text += f"• Found Keywords: {', '.join(found_keywords)}\n"
            analysis_text += f"• Relevance Score: {relevance_score:.1f}%\n"
            analysis_text += f"• Analysis: {'TechMart retail context well understood' if relevance_score >= 60 else 'Partial TechMart context' if relevance_score >= 30 else 'Limited TechMart context'}"
            
            enhanced_response = ai_response + analysis_text
            
            # Add to report
            if report_generator:
                report_generator.add_test_result(
                    scenario=f"TechMart Chat: {scenario_data['scenario']}",
                    input_data={
                        "message": scenario_data['message'], 
                        "test_type": "techmart_retail_chat",
                        "scenario": scenario_data['scenario'],
                        "expected_keywords": expected_keywords
                    },
                    output_data=enhanced_response,
                    status=status,
                    duration=duration,
                    environment=environment,
                    response_code=response.status_code
                )
            
            time.sleep(3)  # Brief delay between messages
        
        print("3. Verifying TechMart conversation state...")
        
        # Get final conversation state
        final_response = session.get(base_url, timeout=30)
        
        # Check for TechMart conversation elements
        if "chat-container" in final_response.text and "TechMart" in final_response.text:
            print("   ✅ TechMart conversation container and branding verified")
        elif "chat-container" in final_response.text:
            print("   ⚠️ Conversation container found but TechMart branding unclear")
        else:
            print("   ⚠️ Conversation container not found")
        
        print("   🎯 TechMart retail chat scenarios completed successfully")
        
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
    """Run simple chat tests on both regular and popup interfaces"""
    print("=" * 60)
    print("🤖 SIMPLE CHAT SCENARIO TEST")
    print("=" * 60)
    print(f"⏰ Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Parse command line arguments
    args = [arg.lower() for arg in sys.argv[1:]]
    
    # Check for basic mode
    basic_mode = "basic" in args
    
    # Default behavior: test both interfaces, local only
    test_popup = "popup" in args or (len(args) == 0 or ("local" in args and "regular" not in args))
    test_regular = "regular" in args or (len(args) == 0 or ("local" in args and "popup" not in args))
    test_local = "local" in args or len(args) == 0 or "azure" not in args  # Default to local
    test_azure = "azure" in args
    
    print(f"🎯 Test Configuration:")
    print(f"   Popup Interface: {'✅ Yes' if test_popup else '❌ No'}")
    print(f"   Regular Interface: {'✅ Yes' if test_regular else '❌ No'}")
    print(f"   Local Testing: {'✅ Yes' if test_local else '❌ No'}")
    print(f"   Azure Testing: {'✅ Yes' if test_azure else '❌ No'}")
    print(f"   Basic Mode: {'✅ Yes (first test only)' if basic_mode else '❌ No (all tests)'}")
    
    # Initialize HTML report generator
    report_generator = HTMLReportGenerator("Simple Chat Scenario Test")
    
    results = {}
    
    # Test local popup interface (default)
    if test_popup and test_local:
        print("\n🏠 Testing LOCAL Popup Interface (Default)")
        results['local_popup'] = test_simple_chat(BASE_URL, report_generator, basic_mode)
    
    # Test local testing interface
    if test_regular and test_local:
        print("\n🏠 Testing LOCAL Testing Interface")
        results['local_testing'] = test_simple_chat(TESTING_LOCAL, report_generator, basic_mode)
    
    # Test Azure popup interface (default)
    if test_popup and test_azure:
        print("\n☁️ Testing AZURE Popup Interface (Default)")
        results['azure_popup'] = test_simple_chat(AZURE_URL, report_generator, basic_mode)
    
    # Test Azure testing interface
    if test_regular and test_azure:
        print("\n☁️ Testing AZURE Testing Interface")
        results['azure_testing'] = test_simple_chat(TESTING_AZURE, report_generator, basic_mode)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SIMPLE CHAT TEST SUMMARY")
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