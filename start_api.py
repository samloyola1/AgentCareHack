#!/usr/bin/env python3
"""
AgentCare FastAPI Startup Script

This script starts the Uvicorn ASGI server for the AgentCare FastAPI application.
"""

import uvicorn
import logging
from pathlib import Path
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("api-server.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

def start_fastapi_app():
    """Start the FastAPI application using Uvicorn"""
    try:
        logging.info("Starting AgentCare FastAPI application...")

        # Check if app/main.py exists
        app_path = Path("app/main.py")
        if not app_path.exists():
            logging.error(f"FastAPI app not found at {app_path}")
            return False

        # Start Uvicorn server
        uvicorn.run(
            "app.main:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info",
            workers=1,  # Single worker for development
            timeout_keep_alive=30,
            server_header=False,
            forwarded_allow_ips="*"
        )

        logging.info("AgentCare API server started successfully!")
        return True

    except ImportError as e:
        logging.error(f"Import error: {e}")
        logging.error("Please make sure all dependencies are installed.")
        return False
    except Exception as e:
        logging.error(f"Error starting server: {e}")
        return False

if __name__ == "__main__":
    success = start_fastapi_app()
    if not success:
        sys.exit(1)