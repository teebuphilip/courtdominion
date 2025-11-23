FROM python:3.10-slim

WORKDIR /app

# Copy requirements
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy automation scripts and config
COPY scripts /app/scripts
COPY config /app/config
COPY quality /app/quality

# Copy the run script
COPY run_automation.sh /app/run_automation.sh
RUN chmod +x /app/run_automation.sh

# Create outputs directory
RUN mkdir -p /app/courtdominion-automation/outputs/generated
RUN mkdir -p /app/courtdominion-automation/outputs/logs

# Set working directory for scripts
WORKDIR /app

# Run automation workflow using the shell script
CMD ["/app/run_automation.sh"]
