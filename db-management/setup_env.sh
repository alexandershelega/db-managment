#!/bin/bash

# Setup virtual environment for db-management

VENV_DIR=".venv"

if [ -d "$VENV_DIR" ]; then
    echo "Virtual environment '$VENV_DIR' already exists."
else
    echo "Creating virtual environment in '$VENV_DIR'..."
    python3 -m venv "$VENV_DIR"
fi

echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

echo "Installing requirements..."
pip install -r db-management/requirements.txt

echo "Setup complete."
echo "To activate the environment in your current shell, run:"
echo "source $VENV_DIR/bin/activate"
