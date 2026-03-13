---
name: azure-redis
description: >
  Azure Cache for Redis with Python using redis-py and aioredis. Use for caching,
  session storage, pub/sub, rate limiting, and leaderboards. Triggers on:
  "azure redis", "redis cache", "redis-py azure", "aioredis", "ConnectionPool redis",
  "Redis.from_url", "azure cache for redis". CRITICAL: Port is 6380 (SSL), NOT 6379.
  ssl_cert_reqs must be 'none' not 'required'. Always use connection pooling.
  decode_responses=True to get strings not bytes.
---

# Azure Cache for Redis with Python

## Packages
```bash
pip install redis    # sync + async (redis>=4.2 includes async)
# or
pip install aioredis  # older async library
```

## Client setup

```python
import redis

# Direct connection
r = redis.Redis(
    host="mycache.redis.cache.windows.net",
    port=6380,                    # 6380 for SSL, NOT 6379
    password="your-access-key",
    ssl=True,
    ssl_cert_reqs="none",         # "none" not "required" for Azure
    decode_responses=True,        # returns str, not bytes
    socket_timeout=10,
    socket_connect_timeout=10,
)

# Connection pool (production — reuse connections)
pool = redis.ConnectionPool(
    host="mycache.redis.cache.windows.net",
    port=6380,
    password="your-access-key",
    ssl=True,
    ssl_cert_reqs="none",
    decode_responses=True,
    max_connections=20,
)
r = redis.Redis(connection_pool=pool)

# From URL
r = redis.from_url(
    "rediss://:password@mycache.redis.cache.windows.net:6380",  # rediss:// = SSL
    decode_responses=True,
    ssl_cert_reqs="none",
)
```

## String operations

```python
# SET with TTL (seconds)
r.set("session:abc123", "user-data", ex=3600)     # expires in 1h
r.setex("key", 3600, "value")                     # equivalent

# GET — returns None if missing
value = r.get("session:abc123")
if value is None:
    print("cache miss")

# Atomic increment/decrement
r.incr("rate_limit:user123")
r.incrby("counter", 5)

# Delete
r.delete("key1", "key2")

# Check existence and TTL
r.exists("session:abc123")    # 0 or 1
r.ttl("session:abc123")       # seconds remaining, -2 if expired/missing
```

## Hash operations

```python
# Store object as hash
r.hset("user:42", mapping={"name": "Alice", "email": "alice@example.com", "age": "30"})

# Get single field
name = r.hget("user:42", "name")

# Get all fields
user = r.hgetall("user:42")    # returns dict

# Update single field
r.hset("user:42", "age", "31")

# Delete field
r.hdel("user:42", "email")
```

## List operations (queues, stacks)

```python
# Push to left/right
r.lpush("queue", "item1", "item2")   # left push
r.rpush("queue", "item3")            # right push

# Pop (returns None if empty)
item = r.lpop("queue")               # left pop
item = r.rpop("queue")               # right pop

# Blocking pop (waits up to 5s)
result = r.blpop("queue", timeout=5)   # returns (key, value) tuple or None

# Length
length = r.llen("queue")
```

## Set and Sorted Set

```python
# Set
r.sadd("tags:post1", "python", "azure", "redis")
r.srem("tags:post1", "azure")
members = r.smembers("tags:post1")

# Sorted set (leaderboard)
r.zadd("leaderboard", {"alice": 1000, "bob": 850, "carol": 1200})
top3 = r.zrevrange("leaderboard", 0, 2, withscores=True)
rank = r.zrevrank("leaderboard", "alice")
```

## Pipeline (batch commands)

```python
# Execute multiple commands atomically
pipe = r.pipeline(transaction=True)
pipe.set("key1", "val1")
pipe.set("key2", "val2")
pipe.incr("counter")
results = pipe.execute()   # list of results
```

## Async (redis-py async)

```python
import redis.asyncio as aioredis

async def main():
    r = aioredis.Redis(
        host="mycache.redis.cache.windows.net",
        port=6380,
        password="your-access-key",
        ssl=True,
        ssl_cert_reqs="none",
        decode_responses=True,
    )
    await r.set("key", "value", ex=3600)
    value = await r.get("key")
    await r.aclose()
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `port=6379` | `port=6380` — Azure uses SSL port |
| `ssl_cert_reqs="required"` | `ssl_cert_reqs="none"` for Azure |
| No `decode_responses=True` | Set it; otherwise `get()` returns `bytes` not `str` |
| `redis.Redis()` per request | Use `ConnectionPool` — reuse connections |
| `r.keys("*")` in production | Use `r.scan_iter("pattern*")` — KEYS blocks server |
| Storing secrets in Redis | Use Azure Key Vault for secrets |
| Not checking `None` from `get()` | Always check `if value is None:` for cache miss |
| `rediss://` omitted for SSL URL | Use `rediss://` (double-s) not `redis://` |
