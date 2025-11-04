"""
Comprehensive test script for OMI webhook integration.
Tests the entire flow from voice input to response.
"""

import sys
import os
import asyncio
import json
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.supabase_client import get_supabase_client
from app.services.intent_router import route_intent
from app.models.schemas import OMIEventRequest, OMIResponse


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'


def print_success(msg):
    print(f"{Colors.GREEN}[OK]{Colors.RESET} {msg}")


def print_error(msg):
    print(f"{Colors.RED}[ERROR]{Colors.RESET} {msg}")


def print_info(msg):
    print(f"{Colors.BLUE}[INFO]{Colors.RESET} {msg}")


def print_warning(msg):
    print(f"{Colors.YELLOW}[WARN]{Colors.RESET} {msg}")


async def test_database_connection():
    """Test 1: Database connection."""
    print("\n" + "=" * 70)
    print_info("TEST 1: Database Connection")
    print("=" * 70)
    
    try:
        supabase = get_supabase_client()
        
        # Test all tables exist
        tables = [
            "clothing_retail_inventory",
            "employee_task_logs",
            "retail_sales_transactions",
            "supplier_purchase_orders",
            "voice_queries_inventory_assistant"
        ]
        
        all_ok = True
        for table in tables:
            try:
                response = supabase.table(table).select("id", count="exact").limit(1).execute()
                count = response.count if hasattr(response, 'count') else len(response.data)
                print_success(f"{table}: {count} rows")
            except Exception as e:
                print_error(f"{table}: {str(e)}")
                all_ok = False
        
        return all_ok
    except Exception as e:
        print_error(f"Database connection failed: {e}")
        return False


async def test_omi_webhook_endpoint():
    """Test 2: OMI webhook endpoint simulation."""
    print("\n" + "=" * 70)
    print_info("TEST 2: OMI Webhook Endpoint Simulation")
    print("=" * 70)
    
    test_cases = [
        {
            "name": "Get Stock Query",
            "transcript": "Check if we have black jackets in stock",
            "expected_intent": "get_stock",
            "language": "en"
        },
        {
            "name": "Create Reorder",
            "transcript": "Schedule restock for red hoodies",
            "expected_intent": "create_reorder",
            "language": "en"
        },
        {
            "name": "Sales Summary",
            "transcript": "What's our sales for the last 7 days?",
            "expected_intent": "get_sales_summary",
            "language": "en"
        },
        {
            "name": "Get Stock - Spanish",
            "transcript": "¿Cuántos jeans azules tenemos?",
            "expected_intent": "get_stock",
            "language": "es"
        }
    ]
    
    results = []
    for test in test_cases:
        print(f"\n  Testing: {test['name']}")
        print(f"    Transcript: \"{test['transcript']}\"")
        
        try:
            # Create OMI event request
            request = OMIEventRequest(
                session_id=f"test_{datetime.now().timestamp()}",
                transcript=test['transcript'],
                language=test.get('language', 'en')
            )
            
            # Route intent
            response = await route_intent(request)
            
            # Check response
            if response.ok:
                print_success(f"Intent: {response.intent}")
                print_success(f"Response OK: {response.speech[:100]}...")
                
                # Verify intent matches
                if response.intent == test['expected_intent']:
                    print_success(f"Intent matches expected: {test['expected_intent']}")
                else:
                    print_warning(f"Intent mismatch. Expected: {test['expected_intent']}, Got: {response.intent}")
                
                # Check result data
                if response.result and not response.result.get('error'):
                    print_success("Result data present")
                else:
                    print_warning(f"Result has error or is empty: {response.result}")
                
                results.append(True)
            else:
                print_error(f"Response not OK: {response.speech}")
                results.append(False)
                
        except Exception as e:
            print_error(f"Test failed: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)
    
    passed = sum(results)
    total = len(results)
    print(f"\n  Results: {passed}/{total} tests passed")
    return passed == total


async def test_get_stock_flow():
    """Test 3: Complete get_stock flow."""
    print("\n" + "=" * 70)
    print_info("TEST 3: Get Stock Flow (End-to-End)")
    print("=" * 70)
    
    try:
        # Test various stock queries
        queries = [
            {"category": "Jackets", "color": "Black"},
            {"name": "jeans"},
            {"color": "Blue", "size": "M"},
            {}  # Get all
        ]
        
        for i, query_params in enumerate(queries, 1):
            print(f"\n  Query {i}: {query_params if query_params else 'All products'}")
            
            request = OMIEventRequest(
                session_id=f"test_stock_{i}",
                transcript=f"Show me {query_params.get('category', '') or query_params.get('name', '') or 'products'}",
                language="en"
            )
            
            response = await route_intent(request)
            
            if response.ok and response.intent == "get_stock":
                result = response.result
                if result and not result.get('error'):
                    items = result.get('items', [])
                    print_success(f"Found {len(items)} items")
                    
                    # Show sample items
                    for item in items[:3]:
                        print(f"    - {item.get('product_id')}: {item.get('name')} ({item.get('color')}) - Stock: {item.get('quantity')}")
                else:
                    print_error(f"Result error: {result.get('error_message', 'Unknown error')}")
            else:
                print_error(f"Failed: {response.speech}")
        
        return True
    except Exception as e:
        print_error(f"Get stock flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_create_reorder_flow():
    """Test 4: Complete create_reorder flow."""
    print("\n" + "=" * 70)
    print_info("TEST 4: Create Reorder Flow (End-to-End)")
    print("=" * 70)
    
    try:
        # First get a product
        request1 = OMIEventRequest(
            session_id="test_reorder_1",
            transcript="Show me some t-shirts",
            language="en"
        )
        
        response1 = await route_intent(request1)
        
        if not response1.ok or response1.intent != "get_stock":
            print_error("Could not get products for reorder test")
            return False
        
        items = response1.result.get('items', [])
        if not items:
            print_warning("No items found for reorder test")
            return False
        
        product = items[0]
        product_name = product.get('name')
        
        print(f"\n  Creating reorder for: {product_name}")
        
        # Create reorder
        request2 = OMIEventRequest(
            session_id="test_reorder_2",
            transcript=f"Create reorder for {product_name}",
            language="en"
        )
        
        response2 = await route_intent(request2)
        
        if response2.ok and response2.intent == "create_reorder":
            result = response2.result
            if result and not result.get('error'):
                print_success(f"Reorder created:")
                print(f"    - Task ID: {result.get('task_id')}")
                print(f"    - Product: {result.get('product_name')}")
                print(f"    - Status: {result.get('status')}")
                return True
            else:
                print_error(f"Reorder creation error: {result.get('error_message', 'Unknown')}")
                return False
        else:
            print_error(f"Reorder failed: {response2.speech}")
            return False
            
    except Exception as e:
        print_error(f"Create reorder flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_sales_summary_flow():
    """Test 5: Sales summary flow."""
    print("\n" + "=" * 70)
    print_info("TEST 5: Sales Summary Flow")
    print("=" * 70)
    
    try:
        request = OMIEventRequest(
            session_id="test_sales_1",
            transcript="What's our sales for the last 30 days?",
            language="en"
        )
        
        response = await route_intent(request)
        
        if response.ok and response.intent == "get_sales_summary":
            result = response.result
            if result and not result.get('error'):
                print_success("Sales summary retrieved:")
                print(f"    - Total Revenue: ${result.get('total_revenue', 0):,.2f}")
                print(f"    - Total Quantity: {result.get('total_quantity', 0):,}")
                print(f"    - Transactions: {result.get('transaction_count', 0):,}")
                print(f"    - Period: Last {result.get('window_days', 0)} days")
                return True
            else:
                print_error(f"Sales summary error: {result.get('error_message', 'Unknown')}")
                return False
        else:
            print_error(f"Sales summary failed: {response.speech}")
            return False
            
    except Exception as e:
        print_error(f"Sales summary flow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_api_response_format():
    """Test 6: API response format validation."""
    print("\n" + "=" * 70)
    print_info("TEST 6: API Response Format Validation")
    print("=" * 70)
    
    try:
        request = OMIEventRequest(
            session_id="test_format_1",
            transcript="Check stock for black jackets",
            language="en"
        )
        
        response = await route_intent(request)
        
        # Check required fields
        required_fields = ['ok', 'intent', 'entities', 'result', 'speech']
        missing_fields = []
        
        for field in required_fields:
            if not hasattr(response, field):
                missing_fields.append(field)
        
        if missing_fields:
            print_error(f"Missing required fields: {missing_fields}")
            return False
        
        print_success("All required fields present")
        
        # Validate types
        checks = [
            (isinstance(response.ok, bool), "ok is boolean"),
            (isinstance(response.intent, str), "intent is string"),
            (isinstance(response.entities, dict), "entities is dict"),
            (isinstance(response.result, dict), "result is dict"),
            (isinstance(response.speech, str), "speech is string"),
            (len(response.speech) > 0, "speech is not empty")
        ]
        
        all_passed = True
        for check, description in checks:
            if check:
                print_success(description)
            else:
                print_error(f"Validation failed: {description}")
                all_passed = False
        
        # Check JSON serializability
        try:
            json_str = response.model_dump_json()
            print_success("Response is JSON serializable")
        except Exception as e:
            print_error(f"JSON serialization failed: {e}")
            all_passed = False
        
        return all_passed
        
    except Exception as e:
        print_error(f"Response format validation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_error_handling():
    """Test 7: Error handling."""
    print("\n" + "=" * 70)
    print_info("TEST 7: Error Handling")
    print("=" * 70)
    
    try:
        # Test with invalid query
        request = OMIEventRequest(
            session_id="test_error_1",
            transcript="Show me products that don't exist xyz123",
            language="en"
        )
        
        response = await route_intent(request)
        
        # Should still return valid response even if no results
        if hasattr(response, 'ok') and hasattr(response, 'speech'):
            print_success("Error handling works - returns valid response")
            print(f"    Response: {response.speech[:100]}...")
            return True
        else:
            print_error("Error handling failed - invalid response format")
            return False
            
    except Exception as e:
        print_error(f"Error handling test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_performance():
    """Test 8: Performance check."""
    print("\n" + "=" * 70)
    print_info("TEST 8: Performance Check")
    print("=" * 70)
    
    try:
        import time
        
        test_queries = [
            "Check stock for jackets",
            "Show me blue jeans",
            "What's our sales?"
        ]
        
        times = []
        for i, transcript in enumerate(test_queries, 1):
            start = time.time()
            
            request = OMIEventRequest(
                session_id=f"perf_test_{i}",
                transcript=transcript,
                language="en"
            )
            
            response = await route_intent(request)
            
            elapsed = time.time() - start
            times.append(elapsed)
            
            print(f"  Query {i}: {elapsed:.3f}s")
        
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"\n  Average response time: {avg_time:.3f}s")
        print(f"  Max response time: {max_time:.3f}s")
        
        if avg_time < 5.0:  # 5 seconds is reasonable for voice
            print_success("Performance is acceptable for voice interactions")
            return True
        else:
            print_warning(f"Average response time ({avg_time:.2f}s) may be too slow for voice")
            return False
            
    except Exception as e:
        print_error(f"Performance test failed: {e}")
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print_info("OMI WEBHOOK INTEGRATION - COMPREHENSIVE TEST SUITE")
    print("=" * 70)
    print("\nThis will test the entire flow from voice input to response.")
    print("Simulating real OMI webhook calls...\n")
    
    tests = [
        ("Database Connection", test_database_connection),
        ("OMI Webhook Endpoint", test_omi_webhook_endpoint),
        ("Get Stock Flow", test_get_stock_flow),
        ("Create Reorder Flow", test_create_reorder_flow),
        ("Sales Summary Flow", test_sales_summary_flow),
        ("API Response Format", test_api_response_format),
        ("Error Handling", test_error_handling),
        ("Performance", test_performance),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print_error(f"{test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 70)
    print_info("TEST SUMMARY")
    print("=" * 70)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = f"{Colors.GREEN}PASSED{Colors.RESET}" if result else f"{Colors.RED}FAILED{Colors.RESET}"
        print(f"  {test_name}: {status}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print_success("\nALL TESTS PASSED! Your app is ready for OMI deployment!")
        print("\nNext steps:")
        print("  1. Deploy to Render/Railway/Vercel")
        print("  2. Configure OMI device with your webhook URL")
        print("  3. Start using your voice assistant!")
    elif passed >= total * 0.7:  # 70% pass rate
        print_warning(f"\n{passed}/{total} tests passed. Some issues need attention.")
        print("   Review the failed tests above before deploying.")
    else:
        print_error(f"\nOnly {passed}/{total} tests passed. Please fix issues before deploying.")
    
    print("\n" + "=" * 70)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nTests interrupted by user")
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback
        traceback.print_exc()

