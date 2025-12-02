#!/usr/bin/env python3
"""
Test script for GeoGLI Chatbot Dify API
Run this after starting the service to verify all endpoints work correctly
"""
import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
API_PREFIX = "/api/dify"

# Test queries
TEST_QUERIES = [
    {
        "name": "Country Profile - Wildfires",
        "query": "Saudi Arabia wildfires",
        "expected_domain": "country_profile"
    },
    {
        "name": "Country Profile - Drought",
        "query": "China drought trends",
        "expected_domain": "country_profile"
    },
    {
        "name": "Legislation",
        "query": "Ghana logging law 2020",
        "expected_domain": "legislation"
    },
    {
        "name": "Commitment - Region",
        "query": "MENA restoration commitments",
        "expected_domain": "commitment"
    }
]


def print_header(text: str):
    """Print a formatted header"""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_result(success: bool, message: str):
    """Print a test result"""
    status = "✓ PASS" if success else "✗ FAIL"
    print(f"{status}: {message}")


def test_health() -> bool:
    """Test health endpoint"""
    print_header("Testing Health Endpoint")
    
    try:
        response = requests.get(f"{BASE_URL}{API_PREFIX}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"Status: {data.get('status')}")
            print(f"Service: {data.get('service')}")
            print(f"Version: {data.get('version')}")
            print(f"BM25 Enabled: {data.get('bm25_enabled')}")
            print_result(True, "Health check passed")
            return True
        else:
            print_result(False, f"HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return False


def test_recognize(query: str, expected_domain: str = None) -> Dict[str, Any]:
    """Test intent recognition endpoint"""
    try:
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/recognize",
            json={"query": query},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ["targets", "domain", "iso3_codes", "query"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                print_result(False, f"Missing fields: {missing_fields}")
                return None
            
            # Check expected domain if provided
            if expected_domain and data["domain"] != expected_domain:
                print_result(False, f"Expected domain '{expected_domain}', got '{data['domain']}'")
                return data
            
            print_result(True, f"Recognized domain: {data['domain']}")
            print(f"  Targets: {data['targets']}")
            print(f"  ISO3: {data['iso3_codes']}")
            print(f"  Section: {data.get('section_hint', 'N/A')}")
            return data
            
        else:
            print_result(False, f"HTTP {response.status_code}")
            return None
            
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return None


def test_chat(query: str, conversation_id: str = None) -> Dict[str, Any]:
    """Test chat endpoint"""
    try:
        payload = {
            "query": query,
            "user": "test_user",
            "response_mode": "blocking"
        }
        
        if conversation_id:
            payload["conversation_id"] = conversation_id
        
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}{API_PREFIX}/chat",
            json=payload,
            timeout=30
        )
        latency = int((time.time() - start_time) * 1000)
        
        if response.status_code == 200:
            data = response.json()
            
            # Validate response structure
            required_fields = ["event", "message_id", "conversation_id", "answer", "metadata"]
            missing_fields = [f for f in required_fields if f not in data]
            
            if missing_fields:
                print_result(False, f"Missing fields: {missing_fields}")
                return None
            
            print_result(True, f"Got answer (latency: {latency}ms)")
            print(f"  Message ID: {data['message_id']}")
            print(f"  Conversation ID: {data['conversation_id']}")
            print(f"  Answer length: {len(data['answer'])} chars")
            print(f"  Source: {data['metadata'].get('source', 'unknown')}")
            
            # Print first 200 chars of answer
            answer_preview = data['answer'][:200]
            if len(data['answer']) > 200:
                answer_preview += "..."
            print(f"  Preview: {answer_preview}")
            
            return data
            
        else:
            print_result(False, f"HTTP {response.status_code}")
            print(f"  Response: {response.text}")
            return None
            
    except Exception as e:
        print_result(False, f"Error: {str(e)}")
        return None


def run_all_tests():
    """Run all test cases"""
    print("\n" + "🚀 " * 20)
    print("  GeoGLI Chatbot Dify API Test Suite")
    print("🚀 " * 20)
    
    # Test 1: Health check
    health_ok = test_health()
    
    if not health_ok:
        print("\n❌ Health check failed. Please ensure the service is running.")
        print("   Start the service with: docker-compose -f docker-compose.dify.yml up -d")
        return
    
    # Test 2: Recognition endpoint
    print_header("Testing Intent Recognition Endpoint")
    
    recognition_results = []
    for test_case in TEST_QUERIES:
        print(f"\nTest: {test_case['name']}")
        print(f"Query: '{test_case['query']}'")
        result = test_recognize(test_case['query'], test_case['expected_domain'])
        recognition_results.append(result is not None)
    
    # Test 3: Chat endpoint
    print_header("Testing Chat Endpoint")
    
    chat_results = []
    for test_case in TEST_QUERIES:
        print(f"\nTest: {test_case['name']}")
        print(f"Query: '{test_case['query']}'")
        result = test_chat(test_case['query'])
        chat_results.append(result is not None)
    
    # Summary
    print_header("Test Summary")
    
    total_tests = 1 + len(TEST_QUERIES) * 2  # health + (recognize + chat) * queries
    passed_tests = sum([health_ok] + recognition_results + chat_results)
    
    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {passed_tests / total_tests * 100:.1f}%")
    
    if passed_tests == total_tests:
        print("\n✅ All tests passed! The API is ready for Dify integration.")
    else:
        print("\n⚠️  Some tests failed. Please check the logs for details.")
        print("   View logs: docker-compose -f docker-compose.dify.yml logs -f")


if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user.")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {str(e)}")
