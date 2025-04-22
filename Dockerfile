FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Run database migrations on startup
# Add a startup script
RUN echo '#!/bin/bash\n\
echo "Waiting for database to be ready..."\n\
sleep 5\n\
echo "Running database migrations..."\n\
alembic upgrade head\n\
echo "Starting application..."\n\
exec uvicorn app.main:app --host 0.0.0.0 --port 8000\n\
' > /app/start.sh && chmod +x /app/start.sh

# Set environment variables (these will be overridden by docker-compose)
ENV SERVICE_NAME=quality-assurance
ENV API_V1_STR=/api/v1
ENV LOG_LEVEL=INFO
ENV DATABASE_URL=postgresql://postgres:postgres@postgres:5432/hotlabel_qa
ENV REDIS_URL=redis://redis:6379/2

# Run the application using the startup script
CMD ["/app/start.sh"]