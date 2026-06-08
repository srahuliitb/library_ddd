"""
Entry point of the application.

The only thing this file does is call composition_root.py to build the app,
then run the server. It contains zero business logic and knows nothing
about modules, layers, or infrastructure.
"""
from composition_root import build_app

app = build_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
