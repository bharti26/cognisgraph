import pytest
import os
import logging
from cognisgraph.config import Config
from cognisgraph.utils.logger import setup_logging

@pytest.fixture(autouse=True)
def setup_test_config():
    """Set up test configuration and logging."""
    config = Config(
        log_level="DEBUG",
        log_file=None,
        debug=True
    )
    
    # Set up logging for tests
    setup_logging(config.log_level)
    
    # Create test data directory if it doesn't exist
    test_data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.exists(test_data_dir):
        os.makedirs(test_data_dir)
    
    return config

@pytest.fixture
def test_pdf_path():
    """Get path to an existing PDF file from the project's data folder.
    
    This fixture provides access to sample.pdf in the project's data directory
    for use across multiple tests.
    """
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    pdf_path = os.path.join(data_dir, "sample.pdf")
    assert os.path.exists(pdf_path), f"PDF file not found at {pdf_path}"
    return pdf_path 