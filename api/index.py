"""
Vercel serverless function entry point for FastAPI app.
This file is required for Vercel to properly deploy FastAPI applications.
"""
import sys
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from app import app
    # Export the FastAPI app for Vercel
    handler = app
except Exception as e:
    # If import fails, create a minimal error handler
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse
    
    error_app = FastAPI()
    
    @error_app.get("/{full_path:path}")
    @error_app.post("/{full_path:path}")
    async def error_handler():
        return JSONResponse(
            status_code=500,
            content={
                "error": "Application initialization failed",
                "message": str(e),
                "help": "Please check environment variables and dependencies"
            }
        )
    
    handler = error_app

