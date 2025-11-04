"""
Vercel serverless function entry point for FastAPI app.
This file is required for Vercel to properly deploy FastAPI applications.
"""
import sys
import os
import traceback
import json

# Prevent Python from exiting on SystemExit during import
# This is critical for Vercel serverless functions
_original_excepthook = sys.excepthook

def _safe_excepthook(exc_type, exc_value, exc_traceback):
    """Prevent SystemExit from terminating the process during import."""
    if exc_type is SystemExit:
        # Convert SystemExit to a regular exception that we can catch
        raise RuntimeError(f"SystemExit intercepted: {exc_value}") from exc_value
    else:
        _original_excepthook(exc_type, exc_value, exc_traceback)

# Only intercept during import phase
_sys_exit_intercepted = False

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Initialize handler to None - will be set below
handler = None
import_error = None

# Try to import and create the app with comprehensive error handling
# IMPORTANT: Catch ALL exceptions including SystemExit to prevent Python process exit
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
            # Execute the module to load it - catch ALL exceptions including SystemExit
            # Temporarily intercept sys.exit to prevent process termination
            original_exit = sys.exit
            def safe_exit(code=0):
                """Intercept sys.exit() calls and convert to exceptions."""
                raise RuntimeError(f"sys.exit({code}) called during module import")
            
            try:
                sys.exit = safe_exit
                spec.loader.exec_module(mod)
            except SystemExit as sys_exit:
                # SystemExit during import means something called sys.exit() or exit()
                # This is often caused by missing dependencies or validation errors
                import_error = ImportError(f"Module execution failed with SystemExit: {sys_exit.code}")
                raise import_error
            except RuntimeError as runtime_err:
                # This might be from our intercepted sys.exit
                if "sys.exit" in str(runtime_err):
                    import_error = ImportError(f"Module tried to exit during import: {runtime_err}")
                    raise import_error
                raise
            except BaseException as base_exc:
                # Catch everything including KeyboardInterrupt, SystemExit, etc.
                import_error = ImportError(f"Module execution failed: {type(base_exc).__name__}: {base_exc}")
                raise import_error
            finally:
                # Restore original sys.exit
                sys.exit = original_exit
            
            # Get the FastAPI app instance
            if hasattr(mod, "app"):
                handler = mod.app
                # Verify it's actually a FastAPI app or callable
                if not callable(handler):
                    raise AttributeError("app.py defines 'app' but it is not callable (not a valid ASGI app)")
            else:
                raise AttributeError("app.py does not define 'app' variable")
                
        except (ImportError, AttributeError, Exception, BaseException) as importlib_error:
            import_error = importlib_error
            # Fallback to regular import
            try:
                # Import from app package (which now exposes app from app.py)
                from app import app as imported_app
                handler = imported_app
            except (ImportError, Exception, BaseException) as fallback_error:
                # If both fail, we'll handle it below
                import_error = fallback_error
    else:
        # app.py doesn't exist, try package import
        try:
            from app import app as imported_app
            handler = imported_app
        except (ImportError, Exception, BaseException) as pkg_error:
            import_error = pkg_error
        
except (ImportError, Exception, BaseException) as e:
    # Catch EVERYTHING including SystemExit, KeyboardInterrupt, etc.
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
# IMPORTANT: This must always be set, even if handler is None (it will be the error app)
try:
    app = handler if handler is not None else basic_asgi_app
except NameError:
    # If handler is None and basic_asgi_app wasn't defined, create a minimal one
    async def minimal_fallback_app(scope, receive, send):
        if scope["type"] == "http":
            response_body = json.dumps({
                "error": "Critical failure: No handler could be created",
                "message": "The application could not be initialized. Check Vercel logs for details."
            }).encode('utf-8')
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
    app = minimal_fallback_app

# Also export as handler for compatibility
__all__ = ['app', 'handler']

# Final safety check - ensure app is always callable
if not callable(app):
    # Last resort: create a minimal ASGI app
    async def final_fallback_app(scope, receive, send):
        if scope["type"] == "http":
            response_body = json.dumps({
                "error": "Critical: app variable is not callable",
                "message": f"Expected ASGI app, got {type(app)}"
            }).encode('utf-8')
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
    app = final_fallback_app
