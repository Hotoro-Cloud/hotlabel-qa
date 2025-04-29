FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all code (app, scripts, migrations, etc.)
COPY . .

# Make scripts executable
RUN chmod +x /app/scripts/ensure_db_ready.py
RUN chmod +x /app/start.py

# Run with start.py script
CMD ["python", "start.py"]
