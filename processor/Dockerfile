FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY processor/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY processor/ .

# Expose Prometheus metrics port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8001/metrics')" || exit 1

# Run processor
CMD ["python", "main.py"]
