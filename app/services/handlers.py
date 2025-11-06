"""Business logic handlers for each intent."""
import logging
from typing import Dict, Any
from datetime import datetime, date, timedelta
import uuid
from app.services.supabase_client import get_supabase_client
from app.services.database import build_inventory_query, format_inventory_item
from app.services.errors import handle_database_error
from app.constants import (
    TABLE_INVENTORY,
    TABLE_TASKS,
    TABLE_SALES,
    TABLE_SUPPLIERS,
    DEFAULT_REORDER_QUANTITY,
    DEFAULT_SALES_WINDOW_DAYS,
    REORDER_DUE_DAYS,
    TASK_TYPE_REORDER,
    TASK_STATUS_PENDING,
    EMPLOYEE_SYSTEM,
    ORDER_STATUS_PENDING,
    ORDER_STATUS_SHIPPED,
    MAX_DELIVERY_ORDERS
)

logger = logging.getLogger(__name__)


async def handle_get_stock(entities: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get_stock intent."""
    try:
        query = build_inventory_query(entities)
        response = query.execute()
        
        items = [format_inventory_item(row) for row in response.data]
        return {"items": items}
    
    except Exception as e:
        return handle_database_error(e, logger)


async def handle_create_reorder(entities: Dict[str, Any]) -> Dict[str, Any]:
    """Handle create_reorder intent - creates a task for reordering."""
    supabase = get_supabase_client()
    
    try:
        quantity = entities.get("quantity", DEFAULT_REORDER_QUANTITY)
        
        # Find product
        query = build_inventory_query(entities)
        product_resp = query.limit(1).execute()
        
        if not product_resp.data:
            return {"error": True, "error_message": "Product not found"}
        
        product_info = product_resp.data[0]
        product_id = product_info.get("product_id")
        
        # Create reorder task
        task_id = f"TASK{str(uuid.uuid4())[:6].upper()}"
        task_data = {
            "task_id": task_id,
            "employee_name": EMPLOYEE_SYSTEM,
            "employee_role": EMPLOYEE_SYSTEM,
            "task_type": TASK_TYPE_REORDER,
            "assigned_date": date.today().isoformat(),
            "due_date": (date.today() + timedelta(days=REORDER_DUE_DAYS)).isoformat(),
            "status": TASK_STATUS_PENDING,
            "related_product": product_id
        }
        
        task_resp = supabase.table(TABLE_TASKS).insert(task_data).execute()
        
        if not task_resp.data:
            return {"error": True, "error_message": "Failed to create reorder task"}
        
        task = task_resp.data[0]
        
        return {
            "task_id": task["task_id"],
            "product_id": product_id,
            "product_name": product_info.get("name", "items"),
            "quantity": quantity,
            "status": "pending",
            "supplier_id": product_info.get("supplier_id"),
            "due_date": task.get("due_date")
        }
    
    except Exception as e:
        return handle_database_error(e, logger)


async def handle_get_sales_summary(entities: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get_sales_summary intent."""
    supabase = get_supabase_client()
    
    try:
        window_days = entities.get("window_days", DEFAULT_SALES_WINDOW_DAYS)
        
        # Get the most recent sale date to work with relative dates
        # This handles cases where data is from a different year
        recent_sales = supabase.table(TABLE_SALES).select("sale_date").order("sale_date", desc=True).limit(1).execute()
        
        if recent_sales.data and recent_sales.data[0].get("sale_date"):
            # Use the most recent sale date as the reference point
            try:
                latest_date_str = recent_sales.data[0].get("sale_date")
                if isinstance(latest_date_str, str):
                    # Handle both date strings and datetime strings
                    date_part = latest_date_str.split("T")[0] if "T" in latest_date_str else latest_date_str
                    latest_date = datetime.fromisoformat(date_part).date()
                else:
                    latest_date = latest_date_str
                reference_date = latest_date
            except (ValueError, AttributeError) as e:
                logger.debug(f"Could not parse latest sale date: {e}")
                # Fallback: try to get all sales and calculate from there
                all_sales = supabase.table(TABLE_SALES).select("*").limit(1000).execute()
                if all_sales.data:
                    # Use the latest date from the fetched data
                    dates = [datetime.fromisoformat(r.get("sale_date", "").split("T")[0]).date() 
                            for r in all_sales.data if r.get("sale_date")]
                    if dates:
                        reference_date = max(dates)
                    else:
                        reference_date = date.today()
                else:
                    reference_date = date.today()
        else:
            # No sales data, use today as reference
            reference_date = date.today()
        
        start_date = (reference_date - timedelta(days=window_days)).isoformat()
        end_date = reference_date.isoformat()
        
        # Query sales within the date range
        response = supabase.table(TABLE_SALES).select("*").gte("sale_date", start_date).lte("sale_date", end_date).execute()
        
        total_quantity = sum(row.get("quantity_sold", 0) for row in response.data)
        total_revenue = sum(float(row.get("revenue", 0) or 0) for row in response.data)
        
        logger.debug(f"Sales summary query: window={window_days} days, start={start_date}, end={end_date}, found={len(response.data)} rows")
        
        return {
            "total_quantity": total_quantity,
            "total_revenue": round(total_revenue, 2),
            "window_days": window_days,
            "transaction_count": len(response.data),
            "start_date": start_date,
            "end_date": end_date
        }
    
    except Exception as e:
        logger.error(f"Error in handle_get_sales_summary: {e}", exc_info=True)
        return handle_database_error(e, logger)


async def handle_get_supplier_info(entities: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get_supplier_info intent."""
    supabase = get_supabase_client()
    
    try:
        product_id = entities.get("product_id")
        if not product_id:
            return {"error": True, "error_message": "Product ID required"}
        
        # Get product supplier_id
        product_resp = supabase.table(TABLE_INVENTORY).select("supplier_id, name").eq("product_id", product_id).limit(1).execute()
        
        if not product_resp.data:
            return {"error": True, "error_message": "Product not found"}
        
        supplier_id = product_resp.data[0].get("supplier_id")
        product_name = product_resp.data[0].get("name")
        
        if not supplier_id:
            return {"error": True, "error_message": "Supplier ID not found for this product"}
        
        # Try to match supplier by partial ID (formats differ: SUP-007 vs SUP00054)
        supplier_resp = supabase.table(TABLE_SUPPLIERS).select("*").ilike("supplier_id", f"%{supplier_id[-3:]}%").limit(1).execute()
        
        if not supplier_resp.data:
            supplier_resp = supabase.table(TABLE_SUPPLIERS).select("*").limit(1).execute()
        
        if not supplier_resp.data:
            return {"error": True, "error_message": "Supplier information not found"}
        
        supplier = supplier_resp.data[0]
        return {
            "supplier_id": supplier.get("supplier_id"),
            "supplier_name": supplier.get("supplier_name", ""),
            "contact_name": supplier.get("contact_name"),
            "contact_email": supplier.get("contact_email"),
            "phone": supplier.get("phone_number"),
            "city": supplier.get("city"),
            "state": supplier.get("state"),
            "product_categories": supplier.get("product_categories_supplied"),
            "note": f"Supplier info for product: {product_name or product_id}"
        }
    
    except Exception as e:
        return handle_database_error(e, logger)


async def handle_get_delivery_status(entities: Dict[str, Any]) -> Dict[str, Any]:
    """Handle get_delivery_status intent."""
    supabase = get_supabase_client()
    
    try:
        purchase_order_id = entities.get("purchase_order_id")
        supplier_id = entities.get("supplier_id")
        
        if purchase_order_id:
            response = supabase.table(TABLE_SUPPLIERS).select("*").eq("purchase_order_id", purchase_order_id).limit(1).execute()
        elif supplier_id:
            response = supabase.table(TABLE_SUPPLIERS).select("*").eq("supplier_id", supplier_id).order("order_date", desc=True).limit(1).execute()
        else:
            # Get recent pending/shipped orders
            response = supabase.table(TABLE_SUPPLIERS).select("*").in_("status", [ORDER_STATUS_PENDING, ORDER_STATUS_SHIPPED]).order("order_date", desc=True).limit(MAX_DELIVERY_ORDERS).execute()
        
        if not response.data:
            return {"error": True, "error_message": "No delivery information found"}
        
        orders = []
        today = date.today()
        
        for order in response.data:
            delivery_date = order.get("delivery_date")
            days_until_delivery = None
            
            if delivery_date:
                try:
                    if isinstance(delivery_date, str):
                        delivery_date_obj = datetime.fromisoformat(delivery_date).date()
                    else:
                        delivery_date_obj = delivery_date
                    days_until_delivery = (delivery_date_obj - today).days
                except (ValueError, AttributeError) as e:
                    logger.debug(f"Could not parse delivery_date {delivery_date}: {e}")
            
            orders.append({
                "purchase_order_id": order.get("purchase_order_id"),
                "supplier_name": order.get("supplier_name"),
                "status": order.get("status", "unknown"),
                "order_date": order.get("order_date"),
                "delivery_date": delivery_date,
                "days_until_delivery": days_until_delivery,
                "total_cost": order.get("total_cost"),
                "payment_status": order.get("payment_status")
            })
        
        return {"orders": orders}
    
    except Exception as e:
        return handle_database_error(e, logger)

