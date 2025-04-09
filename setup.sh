#!/bin/bash

# Create virtual environment if it doesn't exist
if [ ! -d "cognisgraph_venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv cognisgraph_venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source cognisgraph_venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Install the package in development mode
echo "Installing cognisgraph in development mode..."
pip install -e .

echo "Setup complete! You can now run the examples."
echo "To activate the virtual environment in the future, run:"
echo "source cognisgraph_venv/bin/activate" 