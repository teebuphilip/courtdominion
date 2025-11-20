FROM python:3.10-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy automation scripts and config
COPY scripts /app/scripts
COPY config /app/config
COPY quality /app/quality

# Create outputs directory
RUN mkdir -p /app/courtdominion-automation/outputs/generated
RUN mkdir -p /app/courtdominion-automation/outputs/logs

# Set working directory for scripts
WORKDIR /app

# Run automation workflow
CMD ["sh", "-c", "python scripts/claude_runner.py && python scripts/generator.py"]
