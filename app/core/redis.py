import redis.asyncio as redis
from app.core.config import settings

async def get_redis_pool():
    """Get a Redis connection pool."""
    return redis.from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
