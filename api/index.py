"""
Vercel serverless function entry point for FastAPI app.
This file is required for Vercel to properly deploy FastAPI applications.
"""
import sys
import os
import traceback

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    # Import app - this will now handle missing env vars gracefully
    from app import app
    # Export the FastAPI app for Vercel
    # Vercel Python runtime supports ASGI apps directly
    handler = app
except Exception as e:
    # If import fails, create a minimal error handler with detailed error info
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    error_app = FastAPI(title="OMI Inventory Assistant - Error")
    
    error_trace = traceback.format_exc()
    
    @error_app.get("/{full_path:path}")
    @error_app.post("/{full_path:path}")
    @error_app.put("/{full_path:path}")
    @error_app.delete("/{full_path:path}")
    async def error_handler(full_path: str = None):
        return JSONResponse(
            status_code=500,
            content={
                "error": "Application initialization failed",
                "message": str(e),
                "traceback": error_trace,
                "help": "Please check environment variables in Vercel dashboard",
                "required_vars": [
                    "SUPABASE_URL",
                    "SUPABASE_KEY", 
                    "OMI_WEBHOOK_TOKEN",
                    "OPENAI_API_KEY"
                ]
            }
        )
    
    handler = error_app

