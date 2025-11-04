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

# Initialize handler to None - will be set below
handler = None

# Try to import and create the app with comprehensive error handling
try:
    # Prefer loading the FastAPI app directly from the root app.py to avoid
    # package/module name conflicts between `app.py` and the `app/` package.
    import importlib.util
    app_file = os.path.join(project_root, "app.py")
    if os.path.exists(app_file):
        spec = importlib.util.spec_from_file_location("main_app", app_file)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        handler = getattr(mod, "app")
    else:
        # Fallback to regular import (works locally)
        from app import app as imported_app
        handler = imported_app
except ImportError as e:
    # Handle import errors (missing dependencies, module not found, etc.)
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        
        error_app = FastAPI(title="OMI Inventory Assistant - Import Error")
        error_trace = traceback.format_exc()
        
        @error_app.get("/{full_path:path}")
        @error_app.post("/{full_path:path}")
        @error_app.put("/{full_path:path}")
        @error_app.delete("/{full_path:path}")
        async def error_handler(full_path: str = None):
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Application import failed",
                    "message": str(e),
                    "traceback": error_trace,
                    "help": "Missing dependency or module not found. Check requirements.txt",
                    "type": "ImportError"
                }
            )
        
        handler = error_app
    except Exception as fallback_error:
        # If even FastAPI can't be imported, we can't create an ASGI handler
        # Log the error and create a minimal string response handler
        import json
        error_info = {
            "error": "Critical import failure",
            "message": str(e),
            "fallback_error": str(fallback_error),
            "traceback": traceback.format_exc()
        }
        
        # Create a minimal ASGI app manually
        async def minimal_asgi_app(scope, receive, send):
            """Minimal ASGI handler as last resort."""
            if scope["type"] == "http":
                response_body = json.dumps(error_info).encode('utf-8')
                await send({
                    'type': 'http.response.start',
                    'status': 500,
                    'headers': [[b'content-type', b'application/json']],
                })
                await send({
                    'type': 'http.response.body',
                    'body': response_body,
                })
        
        handler = minimal_asgi_app
        
except Exception as e:
    # Handle any other exceptions during import
    try:
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        
        error_app = FastAPI(title="OMI Inventory Assistant - Initialization Error")
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
                    ],
                    "type": type(e).__name__
                }
            )
        
        handler = error_app
    except Exception as fallback_error:
        # If even FastAPI can't be imported, we can't create an ASGI handler
        # Log the error and create a minimal ASGI app manually
        import json
        error_info = {
            "error": "Critical initialization failure",
            "message": str(e),
            "fallback_error": str(fallback_error),
            "traceback": traceback.format_exc()
        }
        
        # Create a minimal ASGI app manually
        async def minimal_asgi_app(scope, receive, send):
            """Minimal ASGI handler as last resort."""
            if scope["type"] == "http":
                response_body = json.dumps(error_info).encode('utf-8')
                await send({
                    'type': 'http.response.start',
                    'status': 500,
                    'headers': [[b'content-type', b'application/json']],
                })
                await send({
                    'type': 'http.response.body',
                    'body': response_body,
                })
        
        handler = minimal_asgi_app

# Ensure handler is always set
if handler is None:
    # Last resort - create a basic ASGI handler
    import json
    async def basic_asgi_app(scope, receive, send):
        """Basic ASGI handler when everything else fails."""
        if scope["type"] == "http":
            response_body = json.dumps({
                "error": "Handler initialization completely failed"
            }).encode('utf-8')
            await send({
                'type': 'http.response.start',
                'status': 500,
                'headers': [[b'content-type', b'application/json']],
            })
            await send({
                'type': 'http.response.body',
                'body': response_body,
            })
    
    handler = basic_asgi_app

# Export ASGI app for Vercel runtime (expects variable named `app`)
# Alias `handler` to `app` for compatibility
app = handler

