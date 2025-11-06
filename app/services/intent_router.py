"""Intent router that maps intents to handlers."""
import logging
from typing import Dict, Any
from app.config import settings
from app.models.schemas import OMIEventRequest, OMIResponse
from app.services.nlu_openai import parse_intent_openai
from app.services.nlu_rules import parse_intent_rules
from app.services.speech_generator import generate_speech, get_translation
from app.services.handlers import (
    handle_get_stock,
    handle_create_reorder,
    handle_get_sales_summary,
    handle_get_supplier_info,
    handle_get_delivery_status
)


logger = logging.getLogger(__name__)


INTENT_HANDLERS = {
    "get_stock": handle_get_stock,
    "create_reorder": handle_create_reorder,
    "get_sales_summary": handle_get_sales_summary,
    "get_supplier_info": handle_get_supplier_info,
    "get_delivery_status": handle_get_delivery_status,
}


async def route_intent(request: OMIEventRequest) -> OMIResponse:
    """
    Parse intent from request and route to appropriate handler.
    
    Args:
        request: OMI event request with transcript
        
    Returns:
        OMIResponse with result and speech text
    """
    # Get language preference
    language = request.language or settings.DEFAULT_LANGUAGE
    
    # Parse intent based on provider
    try:
        if settings.INTENT_PROVIDER == "openai":
            try:
                parsed = parse_intent_openai(request)
            except Exception as e:
                logger.warning(f"OpenAI parsing failed, falling back to rules: {e}")
                parsed = parse_intent_rules(request)
        else:
            parsed = parse_intent_rules(request)
        
        intent = parsed["intent"]
        entities = parsed.get("entities", {})
        
    except Exception as e:
        logger.error(f"Intent parsing failed: {e}", exc_info=True)
        return OMIResponse(
            ok=False,
            intent="unknown",
            entities={},
            result={"error": str(e)},
            speech=get_translation(language, "error_parse")
        )
    
    # Route to handler
    handler = INTENT_HANDLERS.get(intent)
    if not handler:
        logger.warning(f"No handler for intent: {intent}")
        return OMIResponse(
            ok=False,
            intent=intent,
            entities=entities,
            result={"error": f"Unknown intent: {intent}"},
            speech=get_translation(language, "error_unknown_intent")
        )
    
    try:
        result = await handler(entities)
        
        # Generate speech text based on result with language support
        speech = generate_speech(intent, result, language=language)
        
        return OMIResponse(
            ok=True,
            intent=intent,
            entities=entities,
            result=result,
            speech=speech
        )
    
    except Exception as e:
        logger.error(f"Handler {intent} failed: {e}", exc_info=True)
        # Try to extract more helpful error message
        error_message = str(e)
        if "not found" in error_message.lower():
            speech = get_translation(language, "error_not_found")
        elif "connection" in error_message.lower() or "timeout" in error_message.lower():
            speech = get_translation(language, "error_generic") + " " + get_translation(language, "error_parse")
        else:
            speech = get_translation(language, "error_generic")
        
        return OMIResponse(
            ok=False,
            intent=intent,
            entities=entities,
            result={"error": error_message},
            speech=speech
        )


