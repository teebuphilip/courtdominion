FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for layer caching)
COPY requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY main.py /app/main.py
COPY routers /app/routers
COPY services /app/services
COPY models /app/models
COPY shared /app/shared
COPY utils /app/utils
COPY data /app/data

# Create data directory
RUN mkdir -p /data/outputs

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run backend
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
