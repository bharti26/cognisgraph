# Makefile for cognisgraph project

# Project Variables
PROJECT_NAME := cognisgraph
VENV_NAME := cognisgraph_venv_new
PYTHON := $(VENV_NAME)/bin/python
PIP := $(VENV_NAME)/bin/pip
SRC_DIR := src/$(PROJECT_NAME)

.PHONY: help install clean run test

help:
	@echo "Available commands:"
	@echo "  install      : Creates a virtual environment $(VENV_NAME) and installs dependencies."
	@echo "  run          : Runs the Streamlit application."
	@echo "  test         : Runs the pytest test suite."
	@echo "  clean        : Removes the virtual environment $(VENV_NAME) and __pycache__ directories."

# Default target (optional, can be useful)
all: install

# Install project dependencies
install: $(VENV_NAME)/bin/activate
	@echo "Installing dependencies from requirements.txt into $(VENV_NAME)..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Installing project in editable mode..."
	$(PIP) install -e .
	@echo "Installation complete."

# Rule to ensure the virtual environment exists
$(VENV_NAME)/bin/activate:
	@echo "Checking virtual environment $(VENV_NAME)..."
	@if [ ! -d "$(VENV_NAME)" ]; then \
		echo "Creating virtual environment $(VENV_NAME)..."; \
		python3 -m venv $(VENV_NAME); \
	else \
		echo "Virtual environment $(VENV_NAME) already exists."; \
	fi
	@touch $(VENV_NAME)/bin/activate # Ensure timestamp updates
	@echo "Virtual environment ready."

# Run tests
test:
	@echo "Running pytest test suite in $(VENV_NAME)..."
	$(PYTHON) -m pytest

# Run Streamlit application
run:
	@echo "Starting the CognisGraph Streamlit app using $(VENV_NAME)..."
	$(VENV_NAME)/bin/streamlit run $(SRC_DIR)/ui/app.py --server.fileWatcherType none

# Clean up build artifacts and venv
clean:
	@echo "Cleaning up $(VENV_NAME)..."
	rm -rf $(VENV_NAME)
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -rf {} +
	@echo "Cleanup complete."