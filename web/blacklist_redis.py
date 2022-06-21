import redis
import os


""" Setup our redis connection for storing the blocklisted tokens. You will probably
want your redis instance configured to persist data to disk, so that a restart
does not cause your application to forget that a JWT was revoked. """
jwt_redis_blocklist = redis.StrictRedis(
    host=os.environ["REDIS_HOST"], port=int(os.environ["REDIS_PORT"]), db=0, password=os.environ["REDIS_PASSWORD"], decode_responses=True
)