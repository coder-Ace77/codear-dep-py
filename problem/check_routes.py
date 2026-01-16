import sys
import os
from fastapi import FastAPI

# Add current directory to path
sys.path.append(os.getcwd())

try:
    from app.main import app
    print("Successfully imported app")
    
    print("\n--- Registered Routes ---")
    for route in app.routes:
        if hasattr(route, "path"):
            print(f"{route.methods} {route.path}")
            
except Exception as e:
    print(f"FAILED: {e}")
    import traceback
    traceback.print_exc()
