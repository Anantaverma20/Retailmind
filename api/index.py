"""
Vercel serverless function entry point for FastAPI app.
This file is required for Vercel to properly deploy FastAPI applications.
"""
import sys
import os
import traceback
import json

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Initialize handler to None - will be set below
handler = None
import_error = None

# Try to import and create the app with comprehensive error handling
try:
    # Method 1: Try direct import from app.py using importlib (avoids package conflicts)
    import importlib.util
    app_file = os.path.join(project_root, "app.py")
    
    if os.path.exists(app_file):
        try:
            spec = importlib.util.spec_from_file_location("main_app", app_file)
            if spec is None or spec.loader is None:
                raise ImportError("Could not create spec from app.py")
            
            mod = importlib.util.module_from_spec(spec)
            # Execute the module to load it
            spec.loader.exec_module(mod)
            
            # Get the FastAPI app instance
            if hasattr(mod, "app"):
                handler = mod.app
            else:
                raise AttributeError("app.py does not define 'app' variable")
                
        except Exception as importlib_error:
            import_error = importlib_error
            # Fallback to regular import
            try:
                # Import from app package (which now exposes app from app.py)
                from app import app as imported_app
                handler = imported_app
            except ImportError as fallback_error:
                # If both fail, we'll handle it below
                import_error = fallback_error
    else:
        # app.py doesn't exist, try package import
        from app import app as imported_app
        handler = imported_app
        
except ImportError as e:
    import_error = e
    # Continue to error handling below
except Exception as e:
    import_error = e
    # Continue to error handling below

# If import failed, create an error app that provides helpful information
if handler is None or import_error is not None:
    try:
        # Try to create a FastAPI error app
        from fastapi import FastAPI
        from fastapi.responses import JSONResponse
        
        error_app = FastAPI(
            title="OMI Inventory Assistant - Initialization Error",
            description="The application failed to initialize. Check error details below."
        )
        
        error_trace = traceback.format_exc() if import_error else "No traceback available"
        error_message = str(import_error) if import_error else "Unknown import error"
        
        @error_app.get("/")
        @error_app.get("/health")
        @error_app.get("/{full_path:path}")
        @error_app.post("/{full_path:path}")
        @error_app.put("/{full_path:path}")
        @error_app.delete("/{full_path:path}")
        async def error_handler(full_path: str = None):
            """Handle all requests with error information."""
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Application initialization failed",
                    "message": error_message,
                    "type": type(import_error).__name__ if import_error else "UnknownError",
                    "traceback": error_trace,
                    "help": "Please check the following:",
                    "checklist": [
                        "1. Verify all environment variables are set in Vercel dashboard",
                        "2. Check that requirements.txt includes all dependencies",
                        "3. Ensure app.py exists and defines 'app' variable",
                        "4. Review Vercel function logs for detailed error information"
                    ],
                    "required_env_vars": [
                        "SUPABASE_URL",
                        "SUPABASE_KEY", 
                        "OMI_WEBHOOK_TOKEN",
                        "OPENAI_API_KEY"
                    ],
                    "project_root": project_root,
                    "app_file_exists": os.path.exists(os.path.join(project_root, "app.py"))
                }
            )
        
        handler = error_app
        
    except Exception as fallback_error:
        # If even FastAPI can't be imported, create a minimal ASGI app manually
        async def minimal_asgi_app(scope, receive, send):
            """Minimal ASGI handler as last resort."""
            if scope["type"] == "http":
                error_info = {
                    "error": "Critical initialization failure",
                    "message": str(import_error) if import_error else "Unknown error",
                    "fallback_error": str(fallback_error),
                    "traceback": traceback.format_exc(),
                    "help": "FastAPI could not be imported. Check requirements.txt"
                }
                response_body = json.dumps(error_info, indent=2).encode('utf-8')
                
                await send({
                    'type': 'http.response.start',
                    'status': 500,
                    'headers': [
                        [b'content-type', b'application/json'],
                        [b'content-length', str(len(response_body)).encode()]
                    ],
                })
                await send({
                    'type': 'http.response.body',
                    'body': response_body,
                })
        
        handler = minimal_asgi_app

# Ensure handler is always set
if handler is None:
    # Last resort - create a basic ASGI handler
    async def basic_asgi_app(scope, receive, send):
        """Basic ASGI handler when everything else fails."""
        if scope["type"] == "http":
            response_body = json.dumps({
                "error": "Handler initialization completely failed",
                "message": "No handler could be created. This indicates a critical configuration issue."
            }, indent=2).encode('utf-8')
            
            await send({
                'type': 'http.response.start',
                'status': 500,
                'headers': [
                    [b'content-type', b'application/json'],
                    [b'content-length', str(len(response_body)).encode()]
                ],
            })
            await send({
                'type': 'http.response.body',
                'body': response_body,
            })
    
    handler = basic_asgi_app

# Export ASGI app for Vercel runtime
# Vercel's @vercel/python expects a variable named `app` at module level
app = handler

# Also export as handler for compatibility
__all__ = ['app', 'handler']
