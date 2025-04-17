# Use Python 3.11 slim image as base
FROM python:3.11-slim as builder

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Final stage
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

# Install dependencies
RUN pip install --no-cache /wheels/*

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/data /app/temp_uploads /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    COGNISGRAPH_LOG_LEVEL=INFO \
    COGNISGRAPH_DEBUG=false

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "src.cognisgraph.api.endpoints:app", "--host", "0.0.0.0", "--port", "8000"] 