@echo off
echo ============================================
echo XRPL Buyer App - Desktop Mode Setup
echo ============================================
echo.

REM Check if venv exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo.
)

echo Activating virtual environment...
call .venv\Scripts\activate

echo.
echo Installing/updating dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ============================================
echo Setup complete! Starting app...
echo ============================================
echo.

python main.py

pause
