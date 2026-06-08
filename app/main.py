"""
Main entry point for the FastAPI application.
"""
import uvicorn

from app.composition_root import build_app

app = build_app()

if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)