import redis

REDIS_HOST = 'quickbriefs-nyc3n7.serverless.use1.cache.amazonaws.com'
REDIS_PORT = 6379

try:
    print("HERE")
    redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)
    # print(redis_client.ping())
    print("HERE1")
    redis_client.set("test_key", "test_value")
    print("HERE2")
    print("Connection successful. Test key value:", redis_client.get("test_key"))
except Exception as e:
    print("Error connecting to Redis:", e)
