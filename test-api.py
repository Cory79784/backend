"""
Comprehensive API Test Script for GeoGLI Chatbot
Tests all endpoints with various scenarios
"""
import requests
import json
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 30

# ANSI color codes for pretty output
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(text: str):
    """Print a formatted header"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.YELLOW}ℹ️  {text}{Colors.END}")

def print_result(label: str, value: Any):
    """Print a result"""
    print(f"{Colors.BOLD}{label}:{Colors.END} {value}")

def test_health_check():
    """Test the health check endpoint"""
    print_header("Testing Health Check Endpoints")
    
    # Test main health endpoint
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Main health check: {data}")
        else:
            print_error(f"Main health check failed: {response.status_code}")
    except Exception as e:
        print_error(f"Main health check error: {e}")
    
    # Test Dify health endpoint
    try:
        response = requests.get(f"{BASE_URL}/api/dify/health", timeout=TIMEOUT)
        if response.status_code == 200:
            data = response.json()
            print_success(f"Dify health check: {data}")
            print_result("  Status", data.get("status"))
            print_result("  Service", data.get("service"))
            print_result("  Version", data.get("version"))
            print_result("  BM25 Enabled", data.get("bm25_enabled"))
        else:
            print_error(f"Dify health check failed: {response.status_code}")
    except Exception as e:
        print_error(f"Dify health check error: {e}")

def test_dify_chat(query: str, description: str):
    """Test the Dify chat endpoint"""
    print_info(f"Testing: {description}")
    print_result("  Query", query)
    
    try:
        start_time = time.time()
        response = requests.post(
            f"{BASE_URL}/api/dify/chat",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Chat request successful ({elapsed:.2f}s)")
            print_result("  Message ID", data.get("message_id"))
            print_result("  Conversation ID", data.get("conversation_id"))
            print_result("  Answer Length", len(data.get("answer", "")))
            
            # Print metadata
            metadata = data.get("metadata", {})
            print_result("  Intent", metadata.get("intent"))
            print_result("  Source", metadata.get("source"))
            print_result("  Latency (ms)", metadata.get("latency_ms"))
            print_result("  Hits Count", len(metadata.get("hits", [])))
            
            # Print first 200 chars of answer
            answer = data.get("answer", "")
            if answer:
                preview = answer[:200] + "..." if len(answer) > 200 else answer
                print_result("  Answer Preview", f"\n    {preview}")
            
            return data
        else:
            print_error(f"Chat request failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Chat request error: {e}")
        return None

def test_dify_recognize(query: str, description: str):
    """Test the Dify recognize endpoint"""
    print_info(f"Testing: {description}")
    print_result("  Query", query)
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/dify/recognize",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Recognition successful")
            print_result("  Targets", data.get("targets"))
            print_result("  Domain", data.get("domain"))
            print_result("  Section Hint", data.get("section_hint"))
            print_result("  ISO3 Codes", data.get("iso3_codes"))
            return data
        else:
            print_error(f"Recognition failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Recognition error: {e}")
        return None

def test_query_endpoint(query: str, description: str):
    """Test the direct query endpoint"""
    print_info(f"Testing: {description}")
    print_result("  Query", query)
    
    try:
        # Test GET method
        response = requests.get(
            f"{BASE_URL}/query",
            params={"q": query},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success("Query request successful (GET)")
            print_result("  Session ID", data.get("session_id"))
            print_result("  Route", data.get("route"))
            
            # Check if it's a BM25 response
            if "intent" in data:
                print_result("  Intent", data.get("intent"))
                print_result("  Hits Count", len(data.get("hits", [])))
            else:
                print_result("  Answer Length", len(data.get("answer", "")))
            
            return data
        else:
            print_error(f"Query request failed: {response.status_code}")
            print_error(f"Response: {response.text}")
            return None
    except Exception as e:
        print_error(f"Query request error: {e}")
        return None

def test_debug_bm25(query: str):
    """Test the debug BM25 endpoint"""
    print_info(f"Testing BM25 debug endpoint")
    print_result("  Query", query)
    
    try:
        response = requests.get(
            f"{BASE_URL}/debug/bm25",
            params={"q": query},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            if "error" in data:
                print_error(f"BM25 debug error: {data['error']}")
            else:
                print_success("BM25 debug successful")
                print_result("  Intent", data.get("intent"))
                print_result("  Hits Count", data.get("hits_count"))
                print_result("  Available Stores", data.get("available_stores"))
            return data
        else:
            print_error(f"BM25 debug failed: {response.status_code}")
            return None
    except Exception as e:
        print_error(f"BM25 debug error: {e}")
        return None

def test_session_management():
    """Test session management"""
    print_header("Testing Session Management")
    
    # First request without session ID
    print_info("Request 1: No session ID provided")
    response1 = requests.post(
        f"{BASE_URL}/api/dify/chat",
        json={"query": "What is Kenya's drought status?"},
        timeout=TIMEOUT
    )
    
    if response1.status_code == 200:
        data1 = response1.json()
        session_id = data1.get("conversation_id")
        print_success(f"Session created: {session_id}")
        
        # Second request with same session ID
        print_info("Request 2: Using same session ID")
        response2 = requests.post(
            f"{BASE_URL}/api/dify/chat",
            json={
                "query": "What about wildfires?",
                "conversation_id": session_id
            },
            timeout=TIMEOUT
        )
        
        if response2.status_code == 200:
            data2 = response2.json()
            session_id2 = data2.get("conversation_id")
            if session_id == session_id2:
                print_success(f"Session maintained: {session_id2}")
            else:
                print_error(f"Session changed: {session_id} -> {session_id2}")
        else:
            print_error("Second request failed")
    else:
        print_error("First request failed")

def run_all_tests():
    """Run all API tests"""
    print_header("GeoGLI Chatbot API Test Suite")
    print_info(f"Testing API at: {BASE_URL}")
    print_info(f"Timeout: {TIMEOUT}s\n")
    
    # Test 1: Health checks
    test_health_check()
    
    # Test 2: Dify Chat Endpoint
    print_header("Testing Dify Chat Endpoint")
    
    test_cases = [
        ("What are the drought trends in Kenya?", "Country-specific drought query"),
        ("Tell me about Saudi Arabia wildfires", "Country-specific wildfire query"),
        ("Show me climate hazards in Brazil", "Country-specific climate query"),
        ("What are the land degradation commitments in Africa?", "Regional commitment query"),
        ("What legislation exists for land restoration?", "Legislation query"),
    ]
    
    for query, description in test_cases:
        test_dify_chat(query, description)
        print()  # Add spacing
    
    # Test 3: Dify Recognize Endpoint
    print_header("Testing Dify Recognize Endpoint")
    
    recognize_cases = [
        ("Saudi Arabia wildfires", "Wildfire recognition"),
        ("Kenya drought trends", "Drought recognition"),
        ("Brazil climate hazards", "Climate hazard recognition"),
        ("Africa land restoration", "Restoration recognition"),
    ]
    
    for query, description in recognize_cases:
        test_dify_recognize(query, description)
        print()
    
    # Test 4: Direct Query Endpoint
    print_header("Testing Direct Query Endpoint")
    test_query_endpoint("What are drought trends in Kenya?", "Direct query test")
    print()
    
    # Test 5: Debug BM25 Endpoint
    print_header("Testing Debug BM25 Endpoint")
    test_debug_bm25("Kenya drought")
    print()
    
    # Test 6: Session Management
    test_session_management()
    
    # Final summary
    print_header("Test Suite Complete")
    print_success("All tests executed!")
    print_info("Review the results above for any failures")
    print_info(f"\nAPI Documentation: {BASE_URL}/docs")
    print_info(f"Health Check: {BASE_URL}/api/dify/health")

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print_error("\n\nTests interrupted by user")
    except Exception as e:
        print_error(f"\n\nUnexpected error: {e}")
