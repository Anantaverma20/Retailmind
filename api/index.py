"""
Vercel serverless function entry point for FastAPI app.
This file is required for Vercel to properly deploy FastAPI applications.
"""
import sys
import os
import traceback
import json

# CRITICAL: Prevent any process exit during import
# Vercel's Python runtime will exit if any uncaught exception occurs
_original_exit = sys.exit
def _safe_exit(code=0):
    """Intercept sys.exit to prevent process termination."""
    raise RuntimeError(f"sys.exit({code}) called - preventing process termination")

# Add the project root to Python path
try:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
except Exception:
    project_root = os.getcwd()

# Initialize handler to None - will be set below
handler = None
import_error = None

# Wrap EVERYTHING in try-except to prevent any exit
try:
    # Temporarily intercept sys.exit
    sys.exit = _safe_exit
    
    # Try to import and create the app with comprehensive error handling
    try:
        # Method 1: Try direct import from app.py using importlib
        import importlib.util
        app_file = os.path.join(project_root, "app.py")
        
        if os.path.exists(app_file):
            try:
                spec = importlib.util.spec_from_file_location("main_app", app_file)
                if spec is None or spec.loader is None:
                    raise ImportError("Could not create spec from app.py")
                
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                
                # Get the FastAPI app instance
                if hasattr(mod, "app"):
                    handler = mod.app
                    if not callable(handler):
                        raise AttributeError("app.py defines 'app' but it is not callable")
                else:
                    raise AttributeError("app.py does not define 'app' variable")
                    
            except Exception as importlib_error:
                import_error = importlib_error
                # Fallback to regular import
                try:
                    from app import app as imported_app
                    handler = imported_app
                except Exception as fallback_error:
                    import_error = fallback_error
        else:
            # app.py doesn't exist, try package import
            try:
                from app import app as imported_app
                handler = imported_app
            except Exception as pkg_error:
                import_error = pkg_error
    except Exception as e:
        import_error = e
    finally:
        # Always restore sys.exit
        sys.exit = _original_exit

except Exception as critical_error:
    # Even if everything above fails, we must create an app
    import_error = critical_error
    sys.exit = _original_exit

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
                "message": "No handler could be created. This indicates a critical configuration issue.",
                "traceback": traceback.format_exc()
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
# CRITICAL: This must ALWAYS be set, even if everything fails
app = handler

# Also export as handler for compatibility
__all__ = ['app', 'handler']

# Final verification - ensure app is callable
if not callable(app):
    # Absolute last resort
    async def final_fallback_app(scope, receive, send):
        if scope["type"] == "http":
            response_body = json.dumps({
                "error": "Critical: app variable is not callable",
                "message": f"Expected ASGI app, got {type(app)}"
            }).encode('utf-8')
            await send({
                'type': 'http.response.start',
                'status': 500,
                'headers': [[b'content-type', b'application/json']],
            })
            await send({'type': 'http.response.body', 'body': response_body})
    app = final_fallback_app
