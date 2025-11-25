FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (none required for Phase 1)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy automation code
COPY __init__.py /app/__init__.py
COPY pipeline.py /app/pipeline.py
COPY ingest_injuries.py /app/ingest_injuries.py
COPY projection_generator.py /app/projection_generator.py
COPY insights_generator.py /app/insights_generator.py
COPY risk_metrics.py /app/risk_metrics.py
COPY utils /app/utils
COPY schemas /app/schemas

# Create data directory
RUN mkdir -p /data/outputs

# Set Python path
ENV PYTHONPATH=/app

# Default command (can be overridden in docker-compose)
CMD ["python", "pipeline.py"]
