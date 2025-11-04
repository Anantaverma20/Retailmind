"""FastAPI entry point for OMI Voice Inventory Assistant."""
import logging
import os
import uuid
from datetime import datetime
from fastapi import FastAPI, Request, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

# Conditional imports for rate limiting (might not be available in all environments)
try:
    from slowapi import Limiter, _rate_limit_exceeded_handler
    from slowapi.util import get_remote_address
    from slowapi.errors import RateLimitExceeded
    SLOWAPI_AVAILABLE = True
except ImportError:
    # Rate limiting not available - create dummy classes
    SLOWAPI_AVAILABLE = False
    Limiter = None
    _rate_limit_exceeded_handler = None
    get_remote_address = None
    RateLimitExceeded = Exception
from app.config import settings
from app.constants import (
    MAX_REQUEST_BODY_SIZE,
    RATE_LIMIT_PER_MINUTE,
    TABLE_INVENTORY,
    TABLE_TASKS,
    TABLE_VOICE_QUERIES,
    TASK_TYPE_REORDER,
    DEFAULT_PRODUCT_NAME
)
from app.models.schemas import (
    OMIEventRequest,
    QueryStockRequest,
    CreateReorderRequest,
    SalesSummaryRequest,
    SupplierInfoRequest,
    DeliveryStatusRequest,
    OMIResponse
)
from app.services.intent_router import route_intent
from app.services.handlers import (
    handle_get_stock,
    handle_create_reorder,
    handle_get_sales_summary,
    handle_get_supplier_info,
    handle_get_delivery_status
)
from app.services.supabase_client import get_supabase_client
from app.services.speech_generator import get_translation


# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)
logger = structlog.get_logger()

# FastAPI app
app = FastAPI(
    title="OMI Voice Inventory Assistant",
    description="Voice-powered inventory management system for clothing stores",
    version="1.0.0"
)

# CORS - Allow specific origins or all for development
# In production, set CORS_ORIGINS environment variable
cors_origins = getattr(settings, "CORS_ORIGINS", "*").split(",") if hasattr(settings, "CORS_ORIGINS") else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiting - optional for serverless environments
# Auto-disable on Vercel (detected via VERCEL environment variable)
is_vercel = os.getenv("VERCEL") == "1"
enable_rate_limiting = getattr(settings, "ENABLE_RATE_LIMITING", True) and not is_vercel

rate_limit = f"{RATE_LIMIT_PER_MINUTE}/minute"
limiter = None
if enable_rate_limiting and SLOWAPI_AVAILABLE:
    try:
        limiter = Limiter(key_func=get_remote_address)
        app.state.limiter = limiter
        app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    except Exception as e:
        # Rate limiting might not work in all serverless environments
        logger.warning(f"Rate limiting disabled: {e}")
        limiter = None
else:
    if not SLOWAPI_AVAILABLE:
        logger.info("Rate limiting disabled (slowapi not available)")
    else:
        logger.info("Rate limiting disabled (serverless environment or ENABLE_RATE_LIMITING=false)")

# Helper decorator for conditional rate limiting
def rate_limit_decorator():
    """Return rate limit decorator if limiter exists, otherwise no-op."""
    if limiter:
        return limiter.limit(rate_limit)
    else:
        # Return a no-op decorator
        def noop_decorator(func):
            return func
        return noop_decorator


# Authentication dependency
async def verify_omi_token(x_omi_token: str = Header(None)):
    """Verify OMI webhook token."""
    # Validate settings before use
    if hasattr(settings, 'validate_required'):
        try:
            settings.validate_required()
        except ValueError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Configuration error: {str(e)}. Please check environment variables."
            )
    
    if not settings.OMI_WEBHOOK_TOKEN:
        raise HTTPException(
            status_code=500,
            detail="OMI_WEBHOOK_TOKEN environment variable is required. Please set it in Vercel settings."
        )
    
    if not x_omi_token or x_omi_token != settings.OMI_WEBHOOK_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid or missing OMI token")
    return x_omi_token


@app.get("/")
async def root():
    """Root endpoint - provides helpful information."""
    return {
        "service": "OMI Voice Inventory Assistant",
        "status": "running",
        "version": "1.0.0",
        "endpoints": {
            "health": "/health",
            "omi_webhook": "/omi/event",
            "api_docs": "/docs"
        },
        "note": "Set environment variables in Vercel dashboard if you see errors"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"ok": True}


@app.get("/favicon.ico")
@app.get("/favicon.png")
async def favicon():
    """Favicon handler - return 204 No Content."""
    from fastapi.responses import Response
    return Response(status_code=204)


def _log_voice_interaction(event: OMIEventRequest, response: OMIResponse) -> None:
    """Log voice interaction to database (non-blocking)."""
    try:
        supabase = get_supabase_client()
        voice_log_data = {
            "id": str(uuid.uuid4()),
            "transcript": event.transcript,
            "intent": response.intent,
            "entities": response.entities,
            "result": response.result,
            "created_at": datetime.utcnow().isoformat()
        }
        supabase.table("voice_logs").insert(voice_log_data).execute()
    except Exception as log_error:
        # Non-critical - don't fail the request if logging fails
        logger.debug(f"Voice log insert failed (non-critical): {log_error}")


@app.post("/omi/event", response_model=OMIResponse)
async def omi_event(
    request: Request,
    event: OMIEventRequest,
    token: str = Depends(verify_omi_token)
):
    """
    Main webhook endpoint for OMI device events.
    
    Requires X-OMI-Token header.
    """
    try:
        # Limit request body size
        if hasattr(request, "_body") and len(request._body) > MAX_REQUEST_BODY_SIZE:
            raise HTTPException(status_code=413, detail="Request body too large")
        
        response = await route_intent(event)
        
        # Log voice interaction (non-blocking)
        _log_voice_interaction(event, response)
        
        return response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("OMI event processing failed", error=str(e), exc_info=True)
        
        language = getattr(event, "language", "en") or "en"
        error_speech = get_translation(language, "error_generic")
        
        return JSONResponse(
            status_code=500,
            content={
                "ok": False,
                "intent": "unknown",
                "entities": {},
                "result": {"error": str(e)},
                "speech": error_speech
            }
        )


@app.post("/query_stock")
@rate_limit_decorator()
async def query_stock(
    request: Request,
    query: QueryStockRequest
):
    """Direct endpoint to query stock levels."""
    entities = {
        "sku": query.sku,
        "name": query.name,
        "color": query.color,
        "size": query.size
    }
    return await handle_get_stock(entities)


@app.post("/create_reorder")
@rate_limit_decorator()
async def create_reorder(
    request: Request,
    reorder: CreateReorderRequest
):
    """Direct endpoint to create a reorder."""
    entities = {
        "product_id": reorder.product_id,
        "sku": reorder.sku,
        "quantity": reorder.quantity
    }
    return await handle_create_reorder(entities)


@app.post("/get_sales_summary")
@rate_limit_decorator()
async def get_sales_summary(
    request: Request,
    summary: SalesSummaryRequest
):
    """Direct endpoint to get sales summary."""
    entities = {"window_days": summary.window_days}
    return await handle_get_sales_summary(entities)


@app.post("/get_supplier_info")
@rate_limit_decorator()
async def get_supplier_info(
    request: Request,
    info: SupplierInfoRequest
):
    """Direct endpoint to get supplier information."""
    entities = {
        "product_id": info.product_id,
        "sku": info.sku
    }
    return await handle_get_supplier_info(entities)


@app.post("/get_delivery_status")
@rate_limit_decorator()
async def get_delivery_status(
    request: Request,
    status: DeliveryStatusRequest
):
    """Direct endpoint to get delivery status."""
    entities = {
        "reorder_id": status.reorder_id,
        "purchase_order_id": status.purchase_order_id
    }
    return await handle_get_delivery_status(entities)


@app.get("/reorders")
@rate_limit_decorator()
async def get_all_reorders(request: Request):
    """Get all reorder tasks (for frontend dashboard)."""
    try:
        supabase = get_supabase_client()
        
        # Get reorder tasks
        response = supabase.table(TABLE_TASKS).select("*").eq("task_type", TASK_TYPE_REORDER).order("assigned_date", desc=True).limit(100).execute()
        
        # Get product info
        product_ids = [row["related_product"] for row in response.data if row.get("related_product")]
        product_map = {}
        
        if product_ids:
            products_resp = supabase.table(TABLE_INVENTORY).select("product_id, name, category, color, size").in_("product_id", product_ids).execute()
            for product in products_resp.data:
                product_map[product["product_id"]] = {
                    "name": product.get("name", DEFAULT_PRODUCT_NAME),
                    "category": product.get("category", ""),
                    "color": product.get("color", ""),
                    "size": product.get("size", "")
                }
        
        default_product_info = {"name": DEFAULT_PRODUCT_NAME, "category": "", "color": "", "size": ""}
        reorders = []
        
        for row in response.data:
            product_id = row.get("related_product")
            product_info = product_map.get(product_id, default_product_info)
            
            reorders.append({
                "task_id": row.get("task_id"),
                "product_id": product_id,
                "product_name": product_info.get("name", DEFAULT_PRODUCT_NAME),
                "category": product_info.get("category"),
                "color": product_info.get("color"),
                "size": product_info.get("size"),
                "employee_name": row.get("employee_name"),
                "status": row.get("status", "Pending"),
                "assigned_date": row.get("assigned_date"),
                "due_date": row.get("due_date"),
                "completion_date": row.get("completion_date")
            })
        
        return {"reorders": reorders}
    
    except Exception as e:
        logger.error("Error fetching reorders", error=str(e), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "reorders": []}
        )


@app.get("/voice_logs")
@rate_limit_decorator()
async def get_voice_logs(request: Request, limit: int = 50):
    """Get recent voice query examples (for frontend dashboard)."""
    try:
        supabase = get_supabase_client()
        
        response = supabase.table(TABLE_VOICE_QUERIES).select("*").order("query_id", desc=False).limit(limit).execute()
        
        logs = [
            {
                "id": row.get("query_id"),
                "transcript": row.get("query_text", ""),
                "intent": row.get("intent", "unknown"),
                "entities": row.get("entities", {}),
                "response": row.get("response_text", ""),
                "created_at": row.get("created_at")
            }
            for row in response.data
        ]
        
        return {"logs": logs}
    
    except Exception as e:
        logger.error("Error fetching voice logs", error=str(e), exc_info=True)
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "logs": []}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

