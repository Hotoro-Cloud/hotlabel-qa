#!/bin/bash
set -e

echo "Waiting for PostgreSQL to be ready..."
max_retries=30
counter=0
until pg_isready -h postgres -U postgres; do
    >&2 echo "PostgreSQL is unavailable - sleeping"
    counter=$((counter+1))
    if [ $counter -ge $max_retries ]; then
        >&2 echo "PostgreSQL connection failed after $max_retries attempts. Exiting."
        exit 1
    fi
    sleep 2
done
echo "PostgreSQL is up and running!"

# Check if our specific database exists
echo "Checking if database hotlabel_qa exists..."
counter=0
until psql -h postgres -U postgres -c "SELECT 1 FROM pg_database WHERE datname = 'hotlabel_qa'" | grep -q 1; do
    >&2 echo "Database hotlabel_qa does not exist yet - sleeping"
    counter=$((counter+1))
    if [ $counter -ge $max_retries ]; then
        >&2 echo "Creating database hotlabel_qa..."
        psql -h postgres -U postgres -c "CREATE DATABASE hotlabel_qa;"
        break
    fi
    sleep 2
done
echo "Database hotlabel_qa is available!"

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

# Start the application
echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000