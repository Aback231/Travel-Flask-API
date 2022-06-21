import redis


jwt_redis_blocklist = redis.StrictRedis(
    host="redis", port=6379, db=0, decode_responses=True
)