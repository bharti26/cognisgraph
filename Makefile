# Makefile for cognisgraph project

# Project variables
PROJECT_NAME := cognisgraph
VENV_NAME := cognisgraph_venv
PYTHON := $(VENV_NAME)/bin/python
PIP := $(VENV_NAME)/bin/pip

.PHONY: help install test run clean

help:
	@echo "Available targets:"
	@echo "  install    - Create virtual environment and install dependencies"
	@echo "  test       - Run test suite"
	@echo "  run        - Run Streamlit app"
	@echo "  clean      - Remove virtual environment and cache files"

install:
	@echo "Creating virtual environment..."
	python3.11 -m venv $(VENV_NAME)
	@echo "Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	@echo "Installation complete!"

test:
	@echo "Running tests..."
	$(PYTHON) -m pytest

run:
	@echo "Starting Streamlit app..."
	$(PYTHON) -m streamlit run src/cognisgraph/ui/app.py

clean:
	@echo "Cleaning up..."
	# rm -rf $(VENV_NAME)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.pyd" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	@echo "Cleanup complete!"