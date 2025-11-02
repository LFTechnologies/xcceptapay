#!/bin/bash

echo "============================================"
echo "XRPL Buyer App - Desktop Mode Setup"
echo "============================================"
echo

# Check if venv exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    echo
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo
echo "Installing/updating dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo
echo "============================================"
echo "Setup complete! Starting app..."
echo "============================================"
echo

python main.py
