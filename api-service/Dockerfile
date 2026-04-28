FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY api-service/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api-service/ .

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run API service
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
