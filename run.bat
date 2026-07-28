@echo off
:: AgentCare FastAPI Startup Script (Windows Batch)

:: Check if Python is available
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not installed. Please install Python first.
    pause
    exit /b 1
)

:: Check if virtual environment should be activated
if exist "venv" (
    echo Activating virtual environment...
    call venv\Scripts\activate
)

:: Install dependencies if not already installed
python -c "import uvicorn" >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo Installing dependencies...
    pip install -r requirements.txt
)

:: Start the FastAPI application
echo Starting AgentCare FastAPI application...
python start_api.py