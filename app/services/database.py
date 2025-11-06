"""Database utilities and helpers."""
from typing import Dict, Any
from app.services.supabase_client import get_supabase_client
from app.constants import MAX_QUERY_RESULTS, TABLE_INVENTORY


def build_inventory_query(filters: Dict[str, Any]) -> Any:
    """
    Build a Supabase query for inventory with filters.
    
    Args:
        filters: Dictionary with filter keys (product_id, name, category, color, size)
        
    Returns:
        Supabase query object
    """
    supabase = get_supabase_client()
    query = supabase.table(TABLE_INVENTORY).select("*")
    
    if filters.get("product_id"):
        query = query.eq("product_id", filters["product_id"])
    else:
        if filters.get("name"):
            query = query.ilike("name", f"%{filters['name']}%")
        if filters.get("category"):
            query = query.ilike("category", f"%{filters['category']}%")
        if filters.get("color"):
            query = query.ilike("color", f"%{filters['color']}%")
        if filters.get("size"):
            query = query.eq("size", filters["size"])
    
    return query.limit(MAX_QUERY_RESULTS)


def format_inventory_item(row: Dict[str, Any]) -> Dict[str, Any]:
    """Format inventory row data into standardized format."""
    quantity = row.get("stock_quantity", 0)
    reorder_threshold = row.get("reorder_threshold", 0)
    
    return {
        "product_id": row.get("product_id"),
        "name": row.get("name", ""),
        "category": row.get("category"),
        "color": row.get("color"),
        "size": row.get("size"),
        "quantity": quantity,
        "low_stock": quantity <= reorder_threshold,
        "reorder_threshold": reorder_threshold,
        "location": row.get("location"),
        "selling_price": row.get("selling_price"),
        "supplier_id": row.get("supplier_id")
    }

