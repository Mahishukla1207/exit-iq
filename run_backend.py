import os
import sys
import uvicorn

# Add backend directory to Python sys.path
backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print(f"[ExitIQ] Starting FastAPI backend server on port {port}...")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)
