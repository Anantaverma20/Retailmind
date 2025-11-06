"""OpenAI JSON intent parser (default NLU provider)."""
import json
import logging
from typing import Dict, Any, Optional
from openai import OpenAI
from app.config import settings
from app.models.schemas import OMIEventRequest


logger = logging.getLogger(__name__)


def parse_intent_openai(request: OMIEventRequest) -> Dict[str, Any]:
    """
    Parse intent using OpenAI with structured JSON output.
    
    Returns:
        Dictionary with 'intent' and 'entities' keys.
    """
    # Validate settings before use
    if hasattr(settings, 'validate_required'):
        settings.validate_required()
    
    if not settings.OPENAI_API_KEY:
        raise ValueError(
            "OPENAI_API_KEY environment variable is required. "
            "Please set it in your Vercel project settings."
        )
    
    client = OpenAI(api_key=settings.OPENAI_API_KEY)
    
    system_prompt = """You are an intent parser for a voice inventory management system.
Extract the intent and entities from the user's voice transcript.

Canonical intents:
- get_stock: Query stock levels for products
- create_reorder: Create a reorder/purchase order
- get_sales_summary: Get sales summary for a time period
- get_supplier_info: Get supplier information for a product
- get_delivery_status: Get delivery status for a reorder

Entities to extract:
- sku: Product SKU code
- name: Product name (e.g., "hoodie", "jeans", "t-shirt")
- color: Product color
- size: Product size
- quantity: Number of items
- window_days: Number of days for sales summary (default 7)
- reorder_id: Reorder identifier
- purchase_order_id: Purchase order identifier

Return JSON in this exact format:
{
  "intent": "get_stock",
  "entities": {
    "name": "hoodie",
    "color": "red",
    "size": "large"
  }
}"""

    user_prompt = f"Transcript: {request.transcript}\n\nExtract intent and entities."
    
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            timeout=5.0
        )
        
        result = json.loads(response.choices[0].message.content)
        
        # Merge with any entities from device
        entities = request.entities or {}
        if "entities" in result:
            entities.update(result.get("entities", {}))
        
        return {
            "intent": result.get("intent", "get_stock"),
            "entities": entities
        }
    
    except Exception as e:
        logger.error(f"OpenAI intent parsing failed: {e}", exc_info=True)
        raise

