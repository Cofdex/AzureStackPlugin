---
name: azure-sql
description: >
  Azure SQL Database with Python using pyodbc and SQLAlchemy. Use for connecting to
  Azure SQL, running queries with proper parameterization, AAD token auth, and
  connection pooling. Triggers on: "azure sql", "pyodbc", "SQLAlchemy azure sql",
  "SQL Server", "ODBC Driver", "azure-sql", "mssql", "parameterized query SQL".
  CRITICAL: Use ? placeholders (NOT %s). ODBC Driver 18 required. Refresh AAD tokens
  hourly. Never use f-strings for SQL.
---

# Azure SQL Database with Python

## Packages
```bash
pip install pyodbc sqlalchemy azure-identity
# Also install ODBC Driver 18: https://learn.microsoft.com/sql/connect/odbc/download-odbc-driver-for-sql-server
```

## Connection string

```python
import pyodbc

# SQL auth (dev/test only)
conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"   # Driver 18, NOT 13 or 17
    "SERVER=myserver.database.windows.net;"
    "DATABASE=mydb;"
    "UID=myuser;PWD=mypassword;"
    "Encrypt=yes;TrustServerCertificate=no;"
)
conn = pyodbc.connect(conn_str)
```

## AAD token auth (production)

```python
import struct
import pyodbc
from azure.identity import DefaultAzureCredential

def get_azure_sql_connection(server: str, database: str) -> pyodbc.Connection:
    credential = DefaultAzureCredential()
    token = credential.get_token("https://database.windows.net/.default")
    
    # Convert token to bytes for pyodbc
    token_bytes = token.token.encode("utf-16-le")
    token_struct = struct.pack(f"<I{len(token_bytes)}s", len(token_bytes), token_bytes)
    
    conn_str = (
        f"DRIVER={{ODBC Driver 18 for SQL Server}};"
        f"SERVER={server}.database.windows.net;"
        f"DATABASE={database};"
        "Authentication=ActiveDirectoryMsi;"
        "Encrypt=yes;"
    )
    # Pass token via SQL_COPT_SS_ACCESS_TOKEN attribute
    conn = pyodbc.connect(conn_str, attrs_before={1256: token_struct})
    return conn

# Token expires in ~1h — refresh before it expires in long-running apps
```

## Queries — use ? placeholders (NOT %s)

```python
cursor = conn.cursor()

# SELECT — positional ? placeholders
cursor.execute(
    "SELECT id, name, email FROM users WHERE status = ? AND age > ?",
    ("active", 18),           # tuple of params
)
rows = cursor.fetchall()
for row in rows:
    print(row.id, row.name)   # access by column name

# Single row
row = cursor.fetchone()
if row:
    print(row.name)

# INSERT
cursor.execute(
    "INSERT INTO users (name, email) VALUES (?, ?)",
    ("Alice", "alice@example.com"),
)
conn.commit()                 # explicit commit required

# UPDATE
cursor.execute(
    "UPDATE users SET status = ? WHERE id = ?",
    ("inactive", user_id),
)
conn.commit()

# DELETE
cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))
conn.commit()
```

## SQLAlchemy with Azure SQL

```python
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import urllib

params = urllib.parse.quote_plus(
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=myserver.database.windows.net;"
    "DATABASE=mydb;"
    "UID=myuser;PWD=mypassword;"
    "Encrypt=yes;"
)
engine = create_engine(f"mssql+pyodbc:///?odbc_connect={params}")

# Use :param style in SQLAlchemy (not ? or %s)
with engine.connect() as conn:
    result = conn.execute(
        text("SELECT * FROM users WHERE status = :status"),
        {"status": "active"},
    )
    for row in result:
        print(row.name)
```

## Connection pooling

```python
# pyodbc — reuse connections, don't open/close per query
conn = pyodbc.connect(conn_str, autocommit=False)

# SQLAlchemy — built-in pool
engine = create_engine(
    connection_url,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
    pool_recycle=3600,   # recycle connections after 1h (matches AAD token expiry)
)
```

## Common mistakes

| ❌ Wrong | ✅ Correct |
|---|---|
| `%s` placeholders (PostgreSQL style) | `?` placeholders for SQL Server/pyodbc |
| `ODBC Driver 13 for SQL Server` | `ODBC Driver 18 for SQL Server` |
| f-string: `f"WHERE id = {user_id}"` | `"WHERE id = ?"` with param tuple |
| `cursor.execute(sql, param1, param2)` | `cursor.execute(sql, (param1, param2))` — tuple |
| Forgetting `conn.commit()` after INSERT/UPDATE | Always commit after writes |
| AAD token never refreshed | Refresh token every ~50 min (expires in 1h) |
| SQLAlchemy `text()` with `?` | Use `:param` style with `text()` in SQLAlchemy |
