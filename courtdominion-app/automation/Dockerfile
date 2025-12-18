FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy ALL Python files (includes dbb2_projections, fetch_real_*, etc.)
COPY *.py /app/

# Copy blacklist file for content generation
COPY superstar_blacklist.txt /app/

# Copy directories
COPY utils /app/utils
COPY schemas /app/schemas

# Set environment variables
ENV DATA_DIR=/data/outputs
ENV LOG_LEVEL=INFO
ENV PYTHONUNBUFFERED=1

# Run pipeline
CMD ["python", "pipeline.py"]
