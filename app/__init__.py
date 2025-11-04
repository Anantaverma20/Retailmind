# OMI Voice Inventory Assistant
# Import the FastAPI app from the root app.py file
import sys
import os
from pathlib import Path

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# Import app from app.py (the root file)
try:
    import importlib.util
    app_file = parent_dir / "app.py"
    spec = importlib.util.spec_from_file_location("app_module", app_file)
    app_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(app_module)
    app = app_module.app
except Exception as e:
    # Fallback: try direct import
    import app as app_module
    app = app_module.app
