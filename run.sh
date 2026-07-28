#!/bin/bash
# AgentCare FastAPI Startup Script (Bash)

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if virtual environment should be activated
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

# Install dependencies if not already installed
if ! python3 -c "import uvicorn" &> /dev/null; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Start the FastAPI application
echo "Starting AgentCare FastAPI application..."
python3 start_api.py