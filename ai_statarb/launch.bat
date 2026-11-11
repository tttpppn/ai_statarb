@echo off
REM Ed Thorp StatArb Agent Launcher

echo.
echo ============================================================================
echo   Ed Thorp Statistical Arbitrage Agent - AI4Trade
echo   Daily Screening + Trading Signals
echo ============================================================================
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install from https://www.python.org/
    pause
    exit /b 1
)

echo Installing dependencies...
pip install -q -r requirements.txt

echo.
echo Running agent...
echo.
python main.py --mode daily --sample-data

pause
