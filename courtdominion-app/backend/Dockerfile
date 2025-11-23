FROM python:3.11-slim
WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy new backend structure
COPY main.py /app/main.py
COPY routers /app/routers
COPY services /app/services
COPY models /app/models
COPY shared /app/shared
COPY utils /app/utils

# Keep legacy code for reference (not used by new backend)
COPY app/legacy /app/app/legacy

# Ensure DATA_DIR exists (env var set via docker-compose)
RUN mkdir -p /data/outputs

EXPOSE 8000

# Run new backend structure
CMD [ "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000" ]
