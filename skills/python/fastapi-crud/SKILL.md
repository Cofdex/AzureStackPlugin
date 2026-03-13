---
name: fastapi-crud
description: >
  Build FastAPI REST API routers with CRUD operations, authentication dependencies,
  and Pydantic response models. Use this skill whenever building or extending a FastAPI
  application — creating new routes, implementing Create/Read/Update/Delete endpoints,
  adding JWT or OAuth2 authentication, writing Pydantic v2 request/response schemas,
  or structuring routers across multiple files. Triggers on: "FastAPI", "APIRouter",
  "CRUD endpoints", "REST API", "response_model", "Depends", "OAuth2", "JWT auth",
  "Pydantic model", "FastAPI route", "add endpoint", "add authentication", "HTTP router".
  Always use this skill when the user is working with FastAPI, even for small additions
  like "add a DELETE endpoint" or "protect this route with auth".
---

# FastAPI CRUD with Auth and Response Models

## Router setup

```python
# routers/users.py
from fastapi import APIRouter, Depends, HTTPException, status

router = APIRouter(
    prefix="/users",
    tags=["users"],
    # Optional: apply a dependency to every route in this router
    # dependencies=[Depends(verify_token)],
)
```

```python
# main.py
from fastapi import FastAPI
from app.routers import users, items

app = FastAPI(title="My API", version="1.0.0")
app.include_router(users.router)
app.include_router(items.router, prefix="/api/v1")  # prefix can be added here too
```

---

## Pydantic schemas (v2)

Use separate models for create, update, and response — they have different field requirements.

```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class UserBase(BaseModel):
    email: str
    full_name: str

class UserCreate(UserBase):
    password: str = Field(min_length=8)

# PATCH schema: all fields optional so partial updates work
class UserUpdate(BaseModel):
    email: Optional[str] = None
    full_name: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=8)

class UserResponse(UserBase):
    id: int
    created_at: datetime
    # Never include: password, password_hash, tokens, secrets

    model_config = ConfigDict(from_attributes=True)  # enables ORM → Pydantic conversion
```

**Pydantic v2 changes** (easy to get wrong):
- `model_dump()` replaces the deprecated `.dict()`
- `model_validate(data)` replaces deprecated `.parse_obj(data)`
- `from_attributes=True` replaces `orm_mode = True` (v1)
- Use `ConfigDict` class, not `class Config:` dict

---

## CRUD routes

```python
from typing import Annotated

@router.post("/", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # POST → 201 Created
    ...

@router.get("/", response_model=list[UserResponse])
async def list_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # GET list → 200 OK (default)
    ...

@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, user_in: UserCreate, db: Session = Depends(get_db)):
    # PUT = full replacement
    ...

@router.patch("/{user_id}", response_model=UserResponse)
async def patch_user(user_id: int, user_in: UserUpdate, db: Session = Depends(get_db)):
    # PATCH = partial update — only apply fields that were actually sent
    data = user_in.model_dump(exclude_unset=True)  # only fields included in request
    for field, value in data.items():
        setattr(db_user, field, value)
    ...

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    # DELETE → 204 No Content (no response body)
    # If you want to return a message, use status_code=200 + response_model
    ...
```

### response_model explained

`response_model` controls what gets serialized and sent back. It's how you strip sensitive
fields (like `password_hash`) that exist on your ORM model but shouldn't reach the client:

```python
# db_user has password_hash — response_model=UserResponse drops it automatically
@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    return db_user  # safe: response_model filters password_hash out
```

Useful options:
```python
@router.patch("/{user_id}", response_model=UserResponse,
              response_model_exclude_unset=True)  # omit fields not explicitly set
```

---

## Dependency injection

Dependencies are functions — FastAPI calls them and injects their return value.

```python
from fastapi import Depends
from sqlalchemy.orm import Session

# DB session dependency (common pattern)
def get_db():
    db = SessionLocal()
    try:
        yield db          # yield makes it a context manager
    finally:
        db.close()

# Using it
async def get_user(user_id: int, db: Session = Depends(get_db)):
    ...
```

### Auth dependency pattern

```python
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exc
    except JWTError:
        raise credentials_exc

    user = db.get(User, user_id)
    if user is None:
        raise credentials_exc
    return user

# Protecting a route
@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

### Role-based auth

```python
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

@router.delete("/{user_id}", status_code=204)
async def delete_user(user_id: int, admin: User = Depends(require_admin)):
    ...
```

---

## HTTPException

```python
# 404 Not Found
raise HTTPException(status_code=404, detail="Item not found")

# 400 Bad Request
raise HTTPException(status_code=400, detail="Email already registered")

# 401 Unauthorized (always include WWW-Authenticate for auth failures)
raise HTTPException(
    status_code=401,
    detail="Not authenticated",
    headers={"WWW-Authenticate": "Bearer"},
)

# 403 Forbidden
raise HTTPException(status_code=403, detail="Not enough permissions")

# 422 is raised automatically by FastAPI for validation errors — don't raise it manually
```

---

## Path and Query parameter validation

Use `Annotated` (modern style) to separate type from validation metadata:

```python
from fastapi import Path, Query
from typing import Annotated

@router.get("/{user_id}")
async def get_user(
    user_id: Annotated[int, Path(gt=0, description="Must be positive")],
    include_deleted: Annotated[bool, Query()] = False,
):
    ...
```

---

## File/project structure

```
app/
├── main.py              # FastAPI() app + include_router calls
├── dependencies.py      # get_db, get_current_user, etc.
├── models.py            # SQLAlchemy ORM models
├── schemas.py           # Pydantic BaseModel schemas
└── routers/
    ├── users.py         # APIRouter for /users
    ├── items.py         # APIRouter for /items
    └── auth.py          # APIRouter for /auth/token
```

Keep schemas (Pydantic) separate from ORM models (SQLAlchemy). They serve different purposes:
ORM models map to DB tables; Pydantic schemas define API contract.

---

## Common mistakes

| Wrong | Correct |
|-------|---------|
| `user.dict()` | `user.model_dump()` (Pydantic v2) |
| `User.parse_obj(data)` | `User.model_validate(data)` |
| `class Config: orm_mode = True` | `model_config = ConfigDict(from_attributes=True)` |
| PATCH schema with required fields | All PATCH fields should be `Optional[T] = None` |
| `status_code=200` on POST create | Use `status_code=201` for resource creation |
| DELETE returning body with `status_code=204` | 204 = no body; use 200 if returning JSON |
| No `response_model` on endpoints with ORM returns | Always set `response_model` to filter sensitive fields |
| `model_dump()` on PATCH without `exclude_unset=True` | Use `model_dump(exclude_unset=True)` to get only provided fields |
