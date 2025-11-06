"""
Test script to verify API endpoints work with real Supabase data.
"""

import sys
import os
import asyncio

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.handlers import (
    handle_get_stock,
    handle_create_reorder,
    handle_get_sales_summary,
    handle_get_supplier_info,
    handle_get_delivery_status
)


async def test_get_stock():
    """Test get_stock handler."""
    print("\n[TEST] Testing get_stock handler...")
    
    # Test 1: Get stock for black jackets
    print("\n  Test 1: Search for 'Jacket' in category")
    result = await handle_get_stock({
        "category": "Jackets",
        "color": "Black"
    })
    
    if result.get("error"):
        print(f"  [ERROR] {result.get('error_message')}")
    else:
        items = result.get("items", [])
        print(f"  [OK] Found {len(items)} items")
        for item in items[:3]:
            print(f"    - {item['product_id']}: {item['name']} ({item['color']}) - Stock: {item['quantity']}")
    
    # Test 2: Get low stock items
    print("\n  Test 2: Get any products")
    result = await handle_get_stock({})
    
    if result.get("error"):
        print(f"  [ERROR] {result.get('error_message')}")
    else:
        items = result.get("items", [])
        low_stock_items = [item for item in items if item['low_stock']]
        print(f"  [OK] Found {len(items)} items total, {len(low_stock_items)} are low stock")


async def test_sales_summary():
    """Test sales summary handler."""
    print("\n[TEST] Testing get_sales_summary handler...")
    
    result = await handle_get_sales_summary({"window_days": 30})
    
    if result.get("error"):
        print(f"  [ERROR] {result.get('error_message')}")
    else:
        print(f"  [OK] Sales Summary (last 30 days):")
        print(f"    - Total Revenue: ${result.get('total_revenue', 0):,.2f}")
        print(f"    - Total Quantity Sold: {result.get('total_quantity', 0):,}")
        print(f"    - Transaction Count: {result.get('transaction_count', 0):,}")


async def test_create_reorder():
    """Test create reorder handler."""
    print("\n[TEST] Testing create_reorder handler...")
    
    # First get a product
    stock_result = await handle_get_stock({"category": "Tops"})
    
    if stock_result.get("items"):
        product = stock_result["items"][0]
        product_id = product["product_id"]
        
        print(f"\n  Creating reorder for: {product['name']} ({product_id})")
        
        result = await handle_create_reorder({
            "product_id": product_id,
            "quantity": 100
        })
        
        if result.get("error"):
            print(f"  [ERROR] {result.get('error_message')}")
        else:
            print(f"  [OK] Reorder task created:")
            print(f"    - Task ID: {result.get('task_id')}")
            print(f"    - Product: {result.get('product_name')}")
            print(f"    - Quantity: {result.get('quantity')}")
            print(f"    - Status: {result.get('status')}")
            print(f"    - Due Date: {result.get('due_date')}")
    else:
        print("  [SKIP] No products found to create reorder")


async def test_supplier_info():
    """Test get supplier info handler."""
    print("\n[TEST] Testing get_supplier_info handler...")
    
    # First get a product with supplier
    stock_result = await handle_get_stock({})
    
    if stock_result.get("items"):
        product = stock_result["items"][0]
        product_id = product["product_id"]
        
        print(f"\n  Getting supplier info for: {product['name']} ({product_id})")
        
        result = await handle_get_supplier_info({"product_id": product_id})
        
        if result.get("error"):
            print(f"  [ERROR] {result.get('error_message')}")
        else:
            print(f"  [OK] Supplier Info:")
            print(f"    - Supplier: {result.get('supplier_name')}")
            print(f"    - Contact: {result.get('contact_name')}")
            print(f"    - Email: {result.get('contact_email')}")
            print(f"    - Phone: {result.get('phone')}")
    else:
        print("  [SKIP] No products found")


async def test_delivery_status():
    """Test get delivery status handler."""
    print("\n[TEST] Testing get_delivery_status handler...")
    
    # Get recent orders
    result = await handle_get_delivery_status({})
    
    if result.get("error"):
        print(f"  [ERROR] {result.get('error_message')}")
    else:
        orders = result.get("orders", [])
        print(f"  [OK] Found {len(orders)} recent orders:")
        for order in orders[:5]:
            print(f"    - {order['purchase_order_id']}: {order['supplier_name']}")
            print(f"      Status: {order['status']}, Delivery: {order['delivery_date']}")
            if order.get('days_until_delivery'):
                print(f"      ETA: {order['days_until_delivery']} days")


async def main():
    """Run all tests."""
    print("=" * 70)
    print("API ENDPOINT TESTS")
    print("=" * 70)
    
    try:
        await test_get_stock()
        await test_sales_summary()
        await test_create_reorder()
        await test_supplier_info()
        await test_delivery_status()
        
        print("\n" + "=" * 70)
        print("ALL TESTS COMPLETED!")
        print("=" * 70)
        print("\nNext steps:")
        print("  1. Start the API server: python app.py")
        print("  2. Test with curl or Postman")
        print("  3. Integrate with your OMI device")
        print("  4. Build the frontend dashboard")
        
    except Exception as e:
        print(f"\n[FATAL ERROR] {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

