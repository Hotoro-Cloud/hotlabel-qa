#!/bin/bash
# setup-env.sh - Script to configure environment variables for infrastructure alignment

# Ensure .env file exists
if [ ! -f .env ]; then
  cp .env.example .env
  
  # Update environment variables to match infrastructure
  sed -i 's|postgresql://postgres:postgres@db:5432/hotlabel_qa|postgresql://postgres:postgres@postgres:5432/hotlabel_qa|g' .env
  sed -i 's|redis://redis:6379/0|redis://redis:6379/2|g' .env
  sed -i 's|http://hotlabel-tasks:8001/api/v1|http://tasks:8000/api/v1|g' .env
  sed -i 's|http://hotlabel-users:8003/api/v1|http://users:8000/api/v1|g' .env
  
  echo "Created .env file with proper configurations for infrastructure"
else
  echo ".env file already exists."
  
  # Prompt to update existing .env
  read -p "Do you want to update the existing .env file? (y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Update environment variables to match infrastructure
    sed -i 's|postgresql://postgres:postgres@db:5432/hotlabel_qa|postgresql://postgres:postgres@postgres:5432/hotlabel_qa|g' .env
    sed -i 's|redis://redis:6379/0|redis://redis:6379/2|g' .env
    sed -i 's|http://hotlabel-tasks:8001/api/v1|http://tasks:8000/api/v1|g' .env
    sed -i 's|http://hotlabel-users:8003/api/v1|http://users:8000/api/v1|g' .env
    
    echo "Updated .env file with proper configurations for infrastructure"
  fi
fi

# Make sure services directory exists
mkdir -p app/services

# Create a connection test utility
cat > app/services/connection_test.py << 'EOF'
"""Utility to test database and Redis connections."""
import asyncio
from sqlalchemy import text
from app.db.session import get_db
from app.core.redis import get_redis_pool
import logging

logger = logging.getLogger(__name__)

async def test_database_connection():
    """Test database connection."""
    try:
        db = next(get_db())
        result = db.execute(text("SELECT 1")).scalar()
        db.close()
        return result == 1
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return False

async def test_redis_connection():
    """Test Redis connection."""
    try:
        redis = await get_redis_pool()
        await redis.set("connection_test", "success")
        result = await redis.get("connection_test")
        await redis.delete("connection_test")
        return result == "success"
    except Exception as e:
        logger.error(f"Redis connection test failed: {str(e)}")
        return False

async def test_all_connections():
    """Test all connections."""
    db_ok = await test_database_connection()
    redis_ok = await test_redis_connection()
    
    return {
        "database": "ok" if db_ok else "error",
        "redis": "ok" if redis_ok else "error",
        "status": "ok" if (db_ok and redis_ok) else "error"
    }

if __name__ == "__main__":
    results = asyncio.run(test_all_connections())
    print(f"Database connection: {results['database']}")
    print(f"Redis connection: {results['redis']}")
    print(f"Overall status: {results['status']}")
EOF

# Add execution permission to this script
chmod +x "$(dirname "$0")/setup-env.sh"

echo "Environment setup completed. Use 'python -m app.services.connection_test' to verify connections."