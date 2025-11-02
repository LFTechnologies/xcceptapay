@echo off
echo ============================================
echo XRPL Buyer App - Clean Install
echo ============================================
echo.

echo Removing old virtual environment...
if exist ".venv" (
    rmdir /s /q .venv
    echo Virtual environment removed.
) else (
    echo No virtual environment found.
)
echo.

echo Creating fresh virtual environment...
python -m venv .venv
echo.

echo Activating virtual environment...
call .venv\Scripts\activate

echo.
echo Installing dependencies (without pyjnius)...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo ============================================
echo Clean install complete! Starting app...
echo ============================================
echo.

python main.py

pause
