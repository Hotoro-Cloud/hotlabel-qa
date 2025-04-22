import redis.asyncio as redis
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)

async def get_redis_pool():
    """Get a Redis connection pool."""
    try:
        logger.info(f"Connecting to Redis at {settings.REDIS_URL}")
        pool = redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
        logger.info("Redis connection pool created successfully")
        return pool
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise
