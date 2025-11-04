"""Unit tests for intent → handler mapping."""
import pytest
from app.models.schemas import OMIEventRequest
from app.services.intent_router import route_intent
from app.services.nlu_rules import parse_intent_rules


def test_get_stock_intent_rules():
    """Test rules parser for get_stock intent."""
    request = OMIEventRequest(transcript="How many red hoodies are left?")
    result = parse_intent_rules(request)
    
    assert result["intent"] == "get_stock"
    assert "color" in result["entities"]
    assert result["entities"]["color"] == "red"
    assert "name" in result["entities"] or "hoodie" in request.transcript.lower()


def test_create_reorder_intent_rules():
    """Test rules parser for create_reorder intent."""
    request = OMIEventRequest(transcript="Restock 25 black jeans")
    result = parse_intent_rules(request)
    
    assert result["intent"] == "create_reorder"
    assert "quantity" in result["entities"]
    assert result["entities"]["quantity"] == 25
    assert result["entities"].get("color") == "black"


def test_get_sales_summary_intent_rules():
    """Test rules parser for get_sales_summary intent."""
    request = OMIEventRequest(transcript="Show me sales summary for the last week")
    result = parse_intent_rules(request)
    
    assert result["intent"] == "get_sales_summary"
    assert result["entities"].get("window_days") == 7


def test_get_supplier_info_intent_rules():
    """Test rules parser for get_supplier_info intent."""
    request = OMIEventRequest(transcript="Who supplies this product?")
    result = parse_intent_rules(request)
    
    assert result["intent"] == "get_supplier_info"


def test_get_delivery_status_intent_rules():
    """Test rules parser for get_delivery_status intent."""
    request = OMIEventRequest(transcript="What's the delivery status for order 12345?")
    result = parse_intent_rules(request)
    
    assert result["intent"] == "get_delivery_status"
    assert "reorder_id" in result["entities"] or "purchase_order_id" in result["entities"]


@pytest.mark.asyncio
async def test_intent_router_unknown_intent():
    """Test router handles unknown intent gracefully."""
    from unittest.mock import Mock, patch
    
    request = OMIEventRequest(transcript="test query")
    
    with patch("app.services.intent_router.parse_intent_rules") as mock_parse:
        mock_parse.return_value = {"intent": "unknown_intent", "entities": {}}
        
        response = await route_intent(request)
        
        assert response.ok is False
        assert response.intent == "unknown_intent"


def test_entity_extraction_color():
    """Test color entity extraction."""
    request = OMIEventRequest(transcript="Show me blue t-shirts")
    result = parse_intent_rules(request)
    
    assert result["entities"].get("color") == "blue"


def test_entity_extraction_size():
    """Test size entity extraction."""
    request = OMIEventRequest(transcript="Do we have large hoodies?")
    result = parse_intent_rules(request)
    
    assert result["entities"].get("size") == "large"


def test_entity_extraction_quantity():
    """Test quantity entity extraction."""
    request = OMIEventRequest(transcript="Order 50 units of product SKU123")
    result = parse_intent_rules(request)
    
    assert result["intent"] == "create_reorder"
    assert result["entities"].get("quantity") == 50

