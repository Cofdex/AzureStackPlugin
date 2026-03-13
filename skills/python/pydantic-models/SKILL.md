---
name: pydantic-models
description: >
  Create Pydantic v2 models following the multi-model pattern with Base, Create, Update,
  Response, and InDB variants. Use this skill whenever defining API request/response schemas,
  database models, or data validation in Python applications. Triggers on: "Pydantic schema",
  "Pydantic model", "request model", "response model", "BaseModel", "data validation",
  "InDB model", "schema inheritance", "multi-model pattern", "Base/Create/Update/Response",
  "field validator", "model validator", "ConfigDict", or "ORM model". Also use when the
  user is adding schemas to a FastAPI app, defining database entity models, or asking how
  to structure Pydantic classes for an API.
---

# Pydantic v2 Multi-Model Pattern

## Why the multi-model pattern exists

A single `User` class can't serve all purposes — the shape of data you accept from a client
(no `id` yet, password required), store in a DB (hashed password, timestamps added by DB),
and return in a response (no password, id included) are all different. The multi-model
pattern uses inheritance to share common fields while letting each variant carry only what
it needs.

## The five-model hierarchy

```python
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from typing import Optional, Annotated
from datetime import datetime

# 1. BASE — shared fields, no defaults that differ per use case
class ItemBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: float = Field(..., gt=0)

# 2. CREATE — what the client sends (POST body)
class ItemCreate(ItemBase):
    pass  # Base is already the create shape; extend if you need extra fields

# 3. UPDATE — PATCH body; every field is Optional so the client sends only what changes
class ItemUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    price: Optional[float] = Field(None, gt=0)

# 4. INDB — the DB row; adds DB-generated fields, reads from ORM objects
class ItemInDB(ItemBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)  # lets Pydantic read ORM attributes

# 5. RESPONSE — what the API returns (may omit sensitive fields from InDB)
class ItemResponse(ItemBase):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
```

**Why keep Update separate from Base?** Update schemas need ALL fields to be `Optional`
with `None` defaults, so clients can send partial payloads. A PATCH that only changes
`price` shouldn't require re-sending `name`. In your route, use `model_dump(exclude_unset=True)`
to get only the fields the client actually provided.

**Why InDB vs Response?** InDB may contain sensitive fields (e.g., `password_hash`,
internal flags). Response is the public shape — anything not declared in the response
schema is automatically excluded by FastAPI's `response_model`.

## Validators

### Field-level validation (`@field_validator`)

```python
from pydantic import field_validator

class UserCreate(BaseModel):
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def email_must_be_lowercase(cls, v: str) -> str:
        return v.lower().strip()

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v
```

`@field_validator` runs after type coercion by default (`mode="after"`). Use
`mode="before"` to intercept raw input before Pydantic casts the type.

### Cross-field validation (`@model_validator`)

```python
from pydantic import model_validator

class PasswordChange(BaseModel):
    password: str
    confirm_password: str

    @model_validator(mode="after")
    def passwords_must_match(self) -> "PasswordChange":
        if self.password != self.confirm_password:
            raise ValueError("Passwords do not match")
        return self
```

Use `@model_validator(mode="after")` when you need access to multiple fields at once.
Use `mode="before"` to inspect the raw dict before any field parsing.

## Computed fields (derived values in responses)

```python
from pydantic import computed_field

class ProductResponse(BaseModel):
    price: float
    tax_rate: float = 0.1
    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def price_with_tax(self) -> float:
        return round(self.price * (1 + self.tax_rate), 2)
```

`@computed_field` appears in `model_dump()` and the JSON schema. It's the v2 replacement
for v1's `@property` + manual inclusion tricks.

## ConfigDict options

```python
model_config = ConfigDict(
    from_attributes=True,      # read ORM object attributes (replaces orm_mode=True)
    populate_by_name=True,     # allow both alias and field name as input
    str_strip_whitespace=True, # auto-strip leading/trailing whitespace on strings
    frozen=True,               # make model instances immutable (like a dataclass frozen=True)
    validate_default=True,     # run validators on default values too
)
```

## Field aliases and serialization

```python
class ExternalPayload(BaseModel):
    user_id: int = Field(..., alias="userId")           # accept "userId" as input
    full_name: str = Field(..., serialization_alias="fullName")  # output as "fullName"

    model_config = ConfigDict(populate_by_name=True)   # also accept "user_id"
```

## Generic models for paginated responses

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar("T")

class Page(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int

# Usage: Page[ItemResponse]
```

## Using Update models in PATCH routes

```python
@router.patch("/{item_id}", response_model=ItemResponse)
def update_item(item_id: int, payload: ItemUpdate, db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    # Only update fields the client actually sent — exclude_unset drops None defaults
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return item
```

## Serialization

| Goal | Method |
|------|--------|
| Python dict | `model.model_dump()` |
| JSON-safe dict (datetimes as strings) | `model.model_dump(mode='json')` |
| JSON string | `model.model_dump_json()` |
| Only non-None fields | `model.model_dump(exclude_none=True)` |
| Only fields the user set | `model.model_dump(exclude_unset=True)` |
| From dict | `MyModel.model_validate(data)` |
| From JSON string | `MyModel.model_validate_json(json_str)` |
| From ORM object | `MyModel.model_validate(orm_obj)` (requires `from_attributes=True`) |

## Critical v1→v2 mistakes

| ❌ v1 (broken) | ✅ v2 (correct) |
|---|---|
| `class Config: orm_mode = True` | `model_config = ConfigDict(from_attributes=True)` |
| `.dict()` | `.model_dump()` |
| `.json()` | `.model_dump_json()` |
| `.parse_obj(data)` | `.model_validate(data)` |
| `.parse_raw(json_str)` | `.model_validate_json(json_str)` |
| `.copy(update={...})` | `.model_copy(update={...})` |
| `@validator("field")` | `@field_validator("field") @classmethod` |
| `@root_validator` | `@model_validator(mode="before"/"after")` |
| `Optional[str]` (no default) | `Optional[str] = None` |
| `class Config:` block | `model_config = ConfigDict(...)` class variable |

**The most common mistake:** `Optional[T]` in Pydantic v2 means `T | None` as a type
annotation — it does NOT make the field optional. You must also provide `= None` as a
default value, otherwise the field is still required (Pydantic will raise a `ValidationError`
if you omit it).
