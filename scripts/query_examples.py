"""
Example queries for working with the inventory data in Supabase.
These demonstrate common use cases for your voice inventory assistant.
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.supabase_client import get_supabase_client


class InventoryQueries:
    """Common inventory query patterns."""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def get_product_by_id(self, product_id: str):
        """Get a specific product by ID."""
        response = self.supabase.table("clothing_retail_inventory") \
            .select("*") \
            .eq("product_id", product_id) \
            .single() \
            .execute()
        return response.data
    
    def get_low_stock_items(self, limit: int = 50):
        """Get items below reorder threshold."""
        response = self.supabase.table("clothing_retail_inventory") \
            .select("product_id, name, category, stock_quantity, reorder_threshold, supplier_id") \
            .filter("stock_quantity", "lt", "reorder_threshold") \
            .order("stock_quantity", desc=False) \
            .limit(limit) \
            .execute()
        return response.data
    
    def search_products(self, category: str = None, color: str = None, size: str = None):
        """Search products by category, color, or size."""
        query = self.supabase.table("clothing_retail_inventory").select("*")
        
        if category:
            query = query.eq("category", category)
        if color:
            query = query.ilike("color", f"%{color}%")
        if size:
            query = query.eq("size", size)
        
        response = query.execute()
        return response.data
    
    def get_stock_by_location(self, location: str):
        """Get all inventory for a specific location."""
        response = self.supabase.table("clothing_retail_inventory") \
            .select("*") \
            .eq("location", location) \
            .execute()
        return response.data
    
    def get_products_by_supplier(self, supplier_id: str):
        """Get all products from a specific supplier."""
        response = self.supabase.table("clothing_retail_inventory") \
            .select("*") \
            .eq("supplier_id", supplier_id) \
            .execute()
        return response.data


class SalesQueries:
    """Common sales query patterns."""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def get_sales_by_product(self, product_id: str):
        """Get all sales for a specific product."""
        response = self.supabase.table("retail_sales_transactions") \
            .select("*") \
            .eq("product_id", product_id) \
            .order("sale_date", desc=True) \
            .execute()
        return response.data
    
    def get_sales_by_date_range(self, start_date: str, end_date: str):
        """Get sales within a date range."""
        response = self.supabase.table("retail_sales_transactions") \
            .select("*") \
            .gte("sale_date", start_date) \
            .lte("sale_date", end_date) \
            .execute()
        return response.data
    
    def get_top_selling_products(self, limit: int = 10):
        """Get top selling products (note: aggregation done client-side)."""
        response = self.supabase.table("retail_sales_transactions") \
            .select("product_id, quantity_sold, revenue") \
            .execute()
        
        # Aggregate on client side
        product_sales = {}
        for sale in response.data:
            pid = sale['product_id']
            if pid not in product_sales:
                product_sales[pid] = {'quantity': 0, 'revenue': 0}
            product_sales[pid]['quantity'] += sale['quantity_sold']
            product_sales[pid]['revenue'] += float(sale['revenue'])
        
        # Sort and return top N
        sorted_products = sorted(
            product_sales.items(),
            key=lambda x: x[1]['quantity'],
            reverse=True
        )
        return sorted_products[:limit]
    
    def get_revenue_by_channel(self):
        """Get revenue breakdown by sales channel."""
        response = self.supabase.table("retail_sales_transactions") \
            .select("channel, revenue") \
            .execute()
        
        # Aggregate by channel
        channel_revenue = {}
        for sale in response.data:
            channel = sale['channel']
            if channel not in channel_revenue:
                channel_revenue[channel] = 0
            channel_revenue[channel] += float(sale['revenue'])
        
        return channel_revenue


class TaskQueries:
    """Common employee task query patterns."""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def get_pending_tasks(self):
        """Get all pending tasks."""
        response = self.supabase.table("employee_task_logs") \
            .select("*") \
            .eq("status", "Pending") \
            .order("due_date", desc=False) \
            .execute()
        return response.data
    
    def get_tasks_by_employee(self, employee_name: str):
        """Get all tasks for a specific employee."""
        response = self.supabase.table("employee_task_logs") \
            .select("*") \
            .eq("employee_name", employee_name) \
            .order("assigned_date", desc=True) \
            .execute()
        return response.data
    
    def get_overdue_tasks(self):
        """Get tasks that are past their due date."""
        today = datetime.now().strftime("%Y-%m-%d")
        response = self.supabase.table("employee_task_logs") \
            .select("*") \
            .in_("status", ["Pending", "Delayed"]) \
            .lt("due_date", today) \
            .execute()
        return response.data


class SupplierQueries:
    """Common supplier and purchase order query patterns."""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    def get_pending_orders(self):
        """Get all pending purchase orders."""
        response = self.supabase.table("supplier_purchase_orders") \
            .select("*") \
            .eq("status", "Pending") \
            .execute()
        return response.data
    
    def get_orders_by_supplier(self, supplier_id: str):
        """Get all orders from a specific supplier."""
        response = self.supabase.table("supplier_purchase_orders") \
            .select("*") \
            .eq("supplier_id", supplier_id) \
            .order("order_date", desc=True) \
            .execute()
        return response.data
    
    def get_upcoming_deliveries(self, days: int = 7):
        """Get orders expected to be delivered in the next N days."""
        today = datetime.now()
        future_date = (today + timedelta(days=days)).strftime("%Y-%m-%d")
        today_str = today.strftime("%Y-%m-%d")
        
        response = self.supabase.table("supplier_purchase_orders") \
            .select("*") \
            .gte("delivery_date", today_str) \
            .lte("delivery_date", future_date) \
            .in_("status", ["Pending", "Shipped"]) \
            .execute()
        return response.data


# Example usage
if __name__ == "__main__":
    print("📚 Inventory Query Examples\n")
    
    # Initialize query classes
    inventory = InventoryQueries()
    sales = SalesQueries()
    tasks = TaskQueries()
    suppliers = SupplierQueries()
    
    # Example 1: Low stock items
    print("1️⃣ Low Stock Items:")
    low_stock = inventory.get_low_stock_items(limit=5)
    for item in low_stock[:5]:
        print(f"   - {item['product_id']}: {item['name']} (Stock: {item['stock_quantity']})")
    
    # Example 2: Search products
    print("\n2️⃣ Searching for Blue Jeans:")
    products = inventory.search_products(category="Bottomwear", color="Blue")
    print(f"   Found {len(products)} products")
    
    # Example 3: Pending tasks
    print("\n3️⃣ Pending Tasks:")
    pending = tasks.get_pending_tasks()
    for task in pending[:5]:
        print(f"   - {task['task_id']}: {task['task_type']} (Due: {task['due_date']})")
    
    # Example 4: Upcoming deliveries
    print("\n4️⃣ Upcoming Deliveries (Next 7 days):")
    deliveries = suppliers.get_upcoming_deliveries(days=7)
    for order in deliveries[:5]:
        print(f"   - {order['purchase_order_id']}: {order['supplier_name']} (ETA: {order['delivery_date']})")
    
    print("\n✅ Query examples completed!")

