"""
Simple script to start the Omi Inventory Assistant API server.
"""

import os
import sys

def check_env():
    """Check if .env file exists and has required variables."""
    if not os.path.exists(".env"):
        print("[WARNING] No .env file found!")
        print("Create a .env file with your Supabase credentials.")
        print("\nRequired variables:")
        print("  - SUPABASE_URL")
        print("  - SUPABASE_KEY")
        print("  - OMI_WEBHOOK_TOKEN")
        print("  - OPENAI_API_KEY")
        return False
    return True

def main():
    print("=" * 70)
    print("OMI INVENTORY ASSISTANT - API SERVER")
    print("=" * 70)
    
    if not check_env():
        print("\n[INFO] Create .env file first, then run this script again.")
        return
    
    print("\n[INFO] Starting API server...")
    print("[INFO] API will be available at: http://localhost:8000")
    print("[INFO] API documentation at: http://localhost:8000/docs")
    print("\n[INFO] Press Ctrl+C to stop the server\n")
    
    # Start the server
    import uvicorn
    from app import app
    
    try:
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n\n[INFO] Server stopped by user")
    except Exception as e:
        print(f"\n[ERROR] Failed to start server: {e}")
        print("\nTroubleshooting:")
        print("  1. Check your .env file has correct credentials")
        print("  2. Run: pip install -r requirements.txt")
        print("  3. Test connection: python scripts/test_supabase_connection.py")

if __name__ == "__main__":
    main()

