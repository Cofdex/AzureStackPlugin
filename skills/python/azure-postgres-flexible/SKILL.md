---
name: azure-postgres-flexible
description: >
  Azure Database for PostgreSQL Flexible Server with Python using psycopg2 and asyncpg.
  Use for connecting to Azure PostgreSQL, running parameterized queries, connection
  pooling, and async operations. Triggers on: "postgresql flexible", "psycopg2 azure",
  "asyncpg azure", "postgres flexible server", "azure postgres", "PostgreSQL azure".
  CRITICAL: sslmode=require is mandatory. Username format is user@server.
  psycopg2 uses %s placeholders; asyncpg uses $1 $2. Always use connection pooling.
---

# Azure PostgreSQL Flexible Server with Python

## Packages
```bash
pip install psycopg2-binary asyncpg azure-identity
```

## Synchronous (psycopg2)

```python
import psycopg2
from psycopg2 import pool as pg_pool

# Connection — SSL is MANDATORY for Azure PostgreSQL
conn = psycopg2.connect(
    host="myserver.postgres.database.azure.com",
    database="mydb",
    user="myuser@myserver",      # username must include @servername
    password="mypassword",
    sslmode="require",           # REQUIRED — not optional
    port=5432,
)

# Connection pool (production pattern)
pool = pg_pool.ThreadedConnectionPool(
    minconn=2,
    maxconn=10,
    host="myserver.postgres.database.azure.com",
    database="mydb",
    user="myuser@myserver",
    password="mypassword",
    sslmode="require",
)
conn = pool.getconn()
try:
    with conn.cursor() as cur:
        cur.execute("SELECT 1")
finally:
    pool.putconn(conn)   # always return to pool
```

## Parameterized queries with psycopg2 (%s placeholders)

```python
conn = psycopg2.connect(...)

with conn.cursor() as cur:
    # SELECT — use %s for ALL types (int, str, etc.)
    cur.execute(
        "SELECT id, name FROM users WHERE status = %s AND age > %s",
        ("active", 18),    # tuple of params
    )
    rows = cur.fetchall()
    for row in rows:
        print(row[0], row[1])   # access by index

    # fetchone
    cur.execute("SELECT name FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    if row:
        print(row[0])

    # INSERT
    cur.execute(
        "INSERT INTO users (name, email) VALUES (%s, %s) RETURNING id",
        ("Alice", "alice@example.com"),
    )
    new_id = cur.fetchone()[0]
    conn.commit()              # explicit commit

    # UPDATE / DELETE
    cur.execute("UPDATE users SET status = %s WHERE id = %s", ("inactive", user_id))
    conn.commit()
```

## Async (asyncpg) — $1 $2 placeholders

```python
import asyncpg

async def main():
    # asyncpg connection string
    conn = await asyncpg.connect(
        "postgresql://myuser%40myserver:password@myserver.postgres.database.azure.com:5432/mydb?sslmode=require"
    )
    # or keyword args
    conn = await asyncpg.connect(
        host="myserver.postgres.database.azure.com",
        user="myuser@myserver",       # @ must be included
        password="mypassword",
        database="mydb",
        ssl="require",
    )

    # asyncpg uses $1, $2 positional placeholders (NOT %s)
    rows = await conn.fetch(
        "SELECT id, name FROM users WHERE status = $1 AND age > $2",
        "active", 18,
    )
    for row in rows:
        print(row["id"], row["name"])   # dict-like access by name

    row = await conn.fetchrow("SELECT name FROM users WHERE id = $1", user_id)
    await conn.execute(
        "INSERT INTO users (name, email) VALUES ($1, $2)",
        "Alice", "alice@example.com",
    )
    await conn.close()

# Async connection pool
async def create_pool():
    return await asyncpg.create_pool(
        host="myserver.postgres.database.azure.com",
        user="myuser@myserver",
        password="mypassword",
        database="mydb",
        ssl="require",
        min_size=2,
        max_size=10,
    )
```

## AAD token auth (production)

```python
import asyncpg
from azure.identity import DefaultAzureCredential

async def connect_with_aad():
    credential = DefaultAzureCredential()
    token = credential.get_token("https://ossrdbms-aad.database.windows.net/.default")
    
    conn = await asyncpg.connect(
        host="myserver.postgres.database.azure.com",
        user="myaaduser@myserver",    # AAD username
        password=token.token,         # token as password
        database="mydb",
        ssl="require",
    )
    # Token expires in ~1h — refresh every 50 min for long-running apps
    return conn
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `sslmode="disable"` | `sslmode="require"` — mandatory for Azure |
| `user="myuser"` | `user="myuser@myserver"` — must include @servername |
| asyncpg `%s` placeholder | asyncpg uses `$1, $2, ...` positional params |
| `cur.execute(sql, param1, param2)` | `cur.execute(sql, (param1, param2))` — tuple |
| `psycopg2.connect()` per request | Use `ThreadedConnectionPool` or `asyncpg.create_pool()` |
| `%d` for integers in psycopg2 | `%s` for ALL types in psycopg2 |
| Not committing after write | `conn.commit()` after INSERT/UPDATE/DELETE |
