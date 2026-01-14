import redis
import json
import os

r = redis.from_url(
    f"rediss://:{os.getenv('REDIS_PASSWORD')}@{os.getenv('REDIS_HOST')}:{os.getenv('REDIS_PORT')}",
    decode_responses=True
)

def set_cache(key, value, expiry=600):
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    r.setex(key, expiry, str(value))

def get_cache(key, is_json=False):
    data = r.get(key)
    if data and is_json:
        return json.loads(data)
    return data

def delete_cache(key):
    r.delete(key)