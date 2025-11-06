"""
Test script to verify Supabase connection and data after CSV import.
Run this after you've uploaded all CSV data to Supabase.
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.supabase_client import get_supabase_client


def test_connection():
    """Test basic Supabase connection."""
    print("[CONNECTION] Testing Supabase connection...")
    try:
        supabase = get_supabase_client()
        print("[SUCCESS] Connected to Supabase!")
        return supabase
    except Exception as e:
        print(f"[ERROR] Failed to connect to Supabase: {e}")
        sys.exit(1)


def test_table_counts(supabase):
    """Check row counts for all tables."""
    print("\n[TABLES] Checking table row counts...")
    
    tables = [
        "clothing_retail_inventory",
        "employee_task_logs",
        "retail_sales_transactions",
        "supplier_purchase_orders",
        "voice_queries_inventory_assistant"
    ]
    
    for table in tables:
        try:
            response = supabase.table(table).select("id", count="exact").limit(1).execute()
            count = response.count if hasattr(response, 'count') else len(response.data)
            print(f"  [OK] {table}: {count} rows")
        except Exception as e:
            print(f"  [ERROR] {table}: Error - {e}")


def test_inventory_queries(supabase):
    """Test common inventory queries."""
    print("\n[INVENTORY] Testing inventory queries...")
    
    # Test 1: Get low stock items
    try:
        response = supabase.table("clothing_retail_inventory") \
            .select("product_id, name, stock_quantity, reorder_threshold") \
            .lt("stock_quantity", 20) \
            .limit(5) \
            .execute()
        
        print(f"\n  Low Stock Items (stock < 20):")
        for item in response.data[:5]:
            print(f"    - {item['product_id']}: {item['name']} (Stock: {item['stock_quantity']})")
        print(f"  [OK] Found {len(response.data)} low stock items")
    except Exception as e:
        print(f"  [ERROR] Low stock query failed: {e}")
    
    # Test 2: Get products by category
    try:
        response = supabase.table("clothing_retail_inventory") \
            .select("category", count="exact") \
            .limit(1) \
            .execute()
        print(f"\n  Inventory by category query working")
        print(f"  [OK] Categories accessible")
    except Exception as e:
        print(f"  [ERROR] Category query failed: {e}")


def test_sales_queries(supabase):
    """Test sales transaction queries."""
    print("\n[SALES] Testing sales queries...")
    
    try:
        response = supabase.table("retail_sales_transactions") \
            .select("sale_id, product_id, quantity_sold, revenue, sale_date") \
            .order("sale_date", desc=True) \
            .limit(5) \
            .execute()
        
        print(f"\n  Recent Sales:")
        for sale in response.data[:5]:
            print(f"    - {sale['sale_id']}: ${sale['revenue']} ({sale['quantity_sold']} units)")
        print(f"  [OK] Sales data accessible")
    except Exception as e:
        print(f"  [ERROR] Sales query failed: {e}")


def test_voice_queries(supabase):
    """Test voice queries data."""
    print("\n[VOICE] Testing voice queries data...")
    
    try:
        response = supabase.table("voice_queries_inventory_assistant") \
            .select("query_id, query_text, intent, response_text") \
            .limit(5) \
            .execute()
        
        print(f"\n  Sample Voice Queries:")
        for query in response.data[:3]:
            print(f"    - Intent: {query['intent']}")
            print(f"      Query: {query['query_text'][:60]}...")
        print(f"  [OK] Voice queries data accessible")
    except Exception as e:
        print(f"  [ERROR] Voice queries failed: {e}")


def test_employee_tasks(supabase):
    """Test employee task queries."""
    print("\n[TASKS] Testing employee tasks...")
    
    try:
        response = supabase.table("employee_task_logs") \
            .select("task_id, employee_name, task_type, status") \
            .eq("status", "Pending") \
            .limit(5) \
            .execute()
        
        print(f"\n  Pending Tasks:")
        for task in response.data[:5]:
            print(f"    - {task['task_id']}: {task['task_type']} ({task['employee_name']})")
        print(f"  [OK] Employee tasks accessible")
    except Exception as e:
        print(f"  [ERROR] Employee tasks query failed: {e}")


def test_supplier_orders(supabase):
    """Test supplier and purchase order queries."""
    print("\n[SUPPLIERS] Testing supplier orders...")
    
    try:
        response = supabase.table("supplier_purchase_orders") \
            .select("purchase_order_id, supplier_name, status, total_cost") \
            .limit(5) \
            .execute()
        
        print(f"\n  Recent Purchase Orders:")
        for order in response.data[:5]:
            print(f"    - {order['purchase_order_id']}: {order['supplier_name']} (${order['total_cost']})")
        print(f"  [OK] Supplier orders accessible")
    except Exception as e:
        print(f"  [ERROR] Supplier orders query failed: {e}")


def main():
    """Run all tests."""
    print("=" * 60)
    print("SUPABASE CONNECTION & DATA TEST")
    print("=" * 60)
    
    # Test connection
    supabase = test_connection()
    
    # Test all tables
    test_table_counts(supabase)
    test_inventory_queries(supabase)
    test_sales_queries(supabase)
    test_voice_queries(supabase)
    test_employee_tasks(supabase)
    test_supplier_orders(supabase)
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("   1. Your Supabase database is ready to use")
    print("   2. You can start building your inventory assistant features")
    print("   3. Use the voice_queries_inventory_assistant table for training/testing")
    print("   4. Check SUPABASE_SETUP_GUIDE.md for more SQL query examples")


if __name__ == "__main__":
    main()

