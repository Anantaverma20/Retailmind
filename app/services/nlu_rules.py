"""Rules-based intent parser (fallback when OpenAI is unavailable)."""
import re
from typing import Dict, Any, Optional
from app.models.schemas import OMIEventRequest


def parse_intent_rules(request: OMIEventRequest) -> Dict[str, Any]:
    """
    Parse intent using keyword and pattern matching rules.
    
    Returns:
        Dictionary with 'intent' and 'entities' keys.
    """
    transcript = request.transcript.lower()
    entities = request.entities or {}
    intent = None
    
    # Stock queries
    stock_patterns = [
        r"how many.*left",
        r"how many.*in stock",
        r"stock.*level",
        r"inventory.*count",
        r"quantity.*available",
        r"do we have.*",
        r"what.*stock",
    ]
    if any(re.search(pattern, transcript) for pattern in stock_patterns):
        intent = "get_stock"
        # Extract product attributes
        for color in ["red", "blue", "black", "white", "green", "yellow", "brown", "gray", "grey"]:
            if color in transcript:
                entities["color"] = color
        for size in ["xs", "small", "s", "medium", "m", "large", "l", "xl", "xxl"]:
            if size in transcript:
                entities["size"] = size
        # Extract numbers that might be SKUs
        numbers = re.findall(r'\b\d+\b', transcript)
        if numbers and len(numbers[-1]) >= 4:
            entities["sku"] = numbers[-1]
    
    # Reorder requests
    reorder_patterns = [
        r"restock",
        r"reorder",
        r"order.*more",
        r"purchase.*order",
        r"buy.*more",
    ]
    if any(re.search(pattern, transcript) for pattern in reorder_patterns):
        intent = "create_reorder"
        # Extract quantity
        quantity_match = re.search(r'(\d+)\s*(?:units?|pieces?|items?)?', transcript)
        if quantity_match:
            entities["quantity"] = int(quantity_match.group(1))
        # Extract product attributes (same as stock)
        for color in ["red", "blue", "black", "white", "green", "yellow", "brown", "gray", "grey"]:
            if color in transcript:
                entities["color"] = color
        for size in ["xs", "small", "s", "medium", "m", "large", "l", "xl", "xxl"]:
            if size in transcript:
                entities["size"] = size
    
    # Sales summary
    sales_patterns = [
        r"sales.*summary",
        r"how many.*sold",
        r"total.*sales",
        r"revenue",
        r"sales.*report",
    ]
    if any(re.search(pattern, transcript) for pattern in sales_patterns):
        intent = "get_sales_summary"
        # Extract time window
        if "week" in transcript or "7" in transcript:
            entities["window_days"] = 7
        elif "month" in transcript or "30" in transcript:
            entities["window_days"] = 30
        elif "day" in transcript:
            entities["window_days"] = 1
        else:
            entities["window_days"] = 7
    
    # Supplier info
    supplier_patterns = [
        r"supplier",
        r"vendor",
        r"who.*supplies",
        r"supplier.*info",
    ]
    if any(re.search(pattern, transcript) for pattern in supplier_patterns):
        intent = "get_supplier_info"
        # Try to extract product identifier
        numbers = re.findall(r'\b\d+\b', transcript)
        if numbers and len(numbers[-1]) >= 4:
            entities["sku"] = numbers[-1]
    
    # Delivery status
    delivery_patterns = [
        r"delivery.*status",
        r"when.*arrive",
        r"shipment",
        r"order.*status",
        r"when.*deliver",
    ]
    if any(re.search(pattern, transcript) for pattern in delivery_patterns):
        intent = "get_delivery_status"
        # Try to extract PO or reorder ID
        numbers = re.findall(r'\b\d+\b', transcript)
        if numbers:
            entities["reorder_id"] = numbers[-1]
            entities["purchase_order_id"] = numbers[-1]
    
    # Default fallback
    if not intent:
        intent = "get_stock"  # Most common query
    
    return {
        "intent": intent,
        "entities": entities
    }

