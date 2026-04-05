# Finance Dashboard API

A backend for a **finance dashboard system** built with FastAPI and Supabase.
Implements role-based access control, financial records management, and aggregated dashboard analytics.

> Built as part of a Backend Developer Intern assessment.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Quick Start](#quick-start)
- [Environment Variables](#environment-variables)
- [Database Setup](#database-setup)
- [API Reference](#api-reference)
- [Role and Permission Model](#role-and-permission-model)
- [Access Control Design](#access-control-design)
- [Error Handling](#error-handling)
- [Running Tests](#running-tests)
- [Design Decisions and Assumptions](#design-decisions-and-assumptions)

---

## Overview

This backend powers a multi-role finance dashboard where:

- **Admins** manage users, create and modify financial records
- **Analysts** view records and access aggregated dashboard insights
- **Viewers** can browse financial records in read-only mode

Every request is authenticated via JWT and role-checked before reaching business logic.
All access control is enforced server-side in FastAPI middleware — the database layer is never relied upon for security.

---

## Tech Stack

| Layer | Choice | Reason |
|---|---|---|
| Language | Python 3.11+ | Readable, widely adopted for backend services |
| Framework | FastAPI | Async-ready, auto Swagger docs, Pydantic validation built-in |
| Database | Supabase (PostgreSQL) | Managed cloud DB, zero infrastructure overhead |
| DB Client | supabase-py | Official Python client, clean query API |
| Auth | JWT via python-jose | Industry-standard token auth, HS256 signing |
| Password Hashing | passlib + bcrypt | Secure, well-established hashing standard |
| Validation | Pydantic v2 | Native to FastAPI, zero-config schema validation |
| API Docs | Swagger UI | Auto-generated, available at `/docs` |

---

## Project Structure

```
finance-backend/
│
├── app/
│   ├── main.py                        # App entry point, router registration, CORS, global error handler
│   │
│   ├── config/
│   │   ├── settings.py                # Env vars loaded via pydantic BaseSettings
│   │   └── supabase.py                # Supabase client singleton (service role)
│   │
│   ├── core/
│   │   ├── db_queries.py              # All Supabase queries centralised here
│   │   ├── dependencies.py            # get_current_user(), require_role() — FastAPI Depends
│   │   ├── exceptions.py              # Typed HTTP exceptions (400, 401, 403, 404, 409)
│   │   ├── responses.py               # Standard success/error response wrapper
│   │   └── security.py                # JWT encode/decode, bcrypt hash/verify
│   │
│   ├── models/
│   │   └── enums.py                   # Role, RecordType, UserStatus enums
│   │
│   └── modules/
│       ├── auth/                      # Register, login, /me
│       │   ├── router.py
│       │   ├── service.py
│       │   └── schemas.py
│       ├── users/                     # User management — Admin only
│       │   ├── router.py
│       │   ├── service.py
│       │   └── schemas.py
│       ├── records/                   # Financial records CRUD + filters
│       │   ├── router.py
│       │   ├── service.py
│       │   └── schemas.py
│       └── dashboard/                 # Analytics and aggregations
│           ├── router.py
│           ├── service.py
│           └── schemas.py
│
├── scripts/
│   ├── create_tables.sql              # Run once in Supabase SQL Editor
│   ├── seed.py                        # Populates demo users and records
│   └── test_api.py                    # Automated end-to-end test suite (68 cases)
│
├── .env
├── requirements.txt
└── README.md
```

**Separation of concerns across every module:**

| File | Responsibility |
|---|---|
| `router.py` | HTTP layer only — path, method, status code, auth guard |
| `service.py` | Business logic — validation rules, state checks, orchestration |
| `schemas.py` | Pydantic models for request/response shape |
| `db_queries.py` | All database calls in one place — services never call Supabase directly |

---

## Quick Start

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd finance-backend
```

### 2. Create virtual environment

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
cp .env.example .env
# Fill in your Supabase and JWT values
```

### 5. Create database tables

- Open your [Supabase Dashboard](https://supabase.com/dashboard)
- Navigate to **SQL Editor → New Query**
- Paste and run the full contents of `scripts/create_tables.sql`

### 6. Seed demo data

```bash
python -m scripts.seed
```

This creates 3 demo users ready to test with:

| Role | Email | Password |
|---|---|---|
| Admin | admin@finance.com | admin123 |
| Analyst | analyst@finance.com | analyst123 |
| Viewer | viewer@finance.com | viewer123 |

### 7. Start the server

```bash
uvicorn app.main:app --reload --port 8000
```

Open **http://localhost:8000/docs** for the interactive Swagger UI.

---

## Environment Variables

```env
# Supabase — Project Settings → API
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# JWT — generate a strong secret: openssl rand -hex 32
JWT_SECRET=your-random-secret
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# App
APP_ENV=development
APP_PORT=8000
```

| Variable | Description |
|---|---|
| `SUPABASE_URL` | Your Supabase project URL |
| `SUPABASE_ANON_KEY` | Supabase anon/public key |
| `SUPABASE_SERVICE_ROLE_KEY` | Service role key — used server-side to bypass RLS |
| `JWT_SECRET` | Secret for signing JWTs. Use a long random string. |
| `JWT_ALGORITHM` | Signing algorithm — `HS256` |
| `JWT_EXPIRE_MINUTES` | Token lifetime in minutes — default `60` |

> We use the service role key server-side so that Supabase RLS never interferes. All access control is enforced in FastAPI middleware.

---

## Database Setup

Run `scripts/create_tables.sql` in the Supabase SQL Editor.

### users

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Primary key, auto-generated |
| `name` | text | Required |
| `email` | text | Unique, required |
| `password` | text | bcrypt hashed, never returned in responses |
| `role` | text | `viewer` / `analyst` / `admin` |
| `status` | text | `active` / `inactive` |
| `created_at` | timestamptz | Auto-set on insert |
| `updated_at` | timestamptz | Auto-updated via trigger |

### financial_records

| Column | Type | Notes |
|---|---|---|
| `id` | uuid | Primary key, auto-generated |
| `amount` | numeric(12,2) | Must be > 0, validated at schema level |
| `type` | text | `income` / `expense` |
| `category` | text | e.g. Salary, Rent, Food |
| `date` | date | The date the transaction occurred |
| `notes` | text | Optional description |
| `created_by` | uuid | FK → users.id — which admin created this |
| `created_at` | timestamptz | Auto-set on insert |
| `updated_at` | timestamptz | Auto-updated via trigger |
| `deleted_at` | timestamptz | `NULL` = active, set = soft deleted |

---

## API Reference

All endpoints are prefixed with `/api`. Full interactive docs at `/docs`.

### Auth

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/auth/register` | Public | Create account (default role: viewer) |
| `POST` | `/api/auth/login` | Public | Login and receive JWT token |
| `GET` | `/api/auth/me` | Any role | Get currently authenticated user |

**Register:**
```json
{ "name": "Alice", "email": "alice@example.com", "password": "mypassword" }
```

**Login response:**
```json
{ "access_token": "eyJ...", "token_type": "bearer" }
```

Use the token in all protected requests:
```
Authorization: Bearer <token>
```

---

### Users

> All endpoints require **Admin** role.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/users` | List all users |
| `GET` | `/api/users/{id}` | Get user by ID |
| `PATCH` | `/api/users/{id}` | Update role or status |
| `DELETE` | `/api/users/{id}` | Deactivate a user |

**PATCH body** (all fields optional):
```json
{ "role": "analyst", "status": "inactive" }
```

---

### Records

| Method | Endpoint | Auth | Description |
|---|---|---|---|
| `POST` | `/api/records` | Admin | Create a financial record |
| `GET` | `/api/records` | All roles | List records with optional filters |
| `GET` | `/api/records/{id}` | All roles | Get a single record |
| `PATCH` | `/api/records/{id}` | Admin | Update a record |
| `DELETE` | `/api/records/{id}` | Admin | Soft delete a record |

**Create body:**
```json
{
  "amount": 85000,
  "type": "income",
  "category": "Salary",
  "date": "2024-06-01",
  "notes": "Monthly salary"
}
```

**Filter params for `GET /api/records`:**

| Param | Type | Description |
|---|---|---|
| `type` | string | `income` or `expense` |
| `category` | string | Exact category name |
| `start_date` | date | `YYYY-MM-DD` |
| `end_date` | date | `YYYY-MM-DD` |
| `page` | int | Page number, default `1` |
| `limit` | int | Per page, default `10`, max `100` |

Example:
```
GET /api/records?type=income&category=Salary&start_date=2024-01-01&page=1&limit=10
```

---

### Dashboard

> Requires **Analyst** or **Admin** role.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/dashboard/summary` | Total income, expenses, net balance |
| `GET` | `/api/dashboard/by-category` | Totals grouped by category and type |
| `GET` | `/api/dashboard/trends` | Monthly breakdown — last 6 months |
| `GET` | `/api/dashboard/recent` | Most recent 10 records |

**Summary response:**
```json
{
  "success": true,
  "message": "Dashboard summary",
  "data": {
    "total_income": 495000.0,
    "total_expense": 63600.0,
    "net_balance": 431400.0
  }
}
```

**Trends response:**
```json
{
  "success": true,
  "message": "Monthly trends (last 6 months)",
  "data": [
    { "month": "2024-03", "income": 105000.0, "expense": 22500.0 },
    { "month": "2024-02", "income": 100000.0, "expense": 20000.0 }
  ]
}
```

---

## Role and Permission Model

| Action | Viewer | Analyst | Admin |
|---|:---:|:---:|:---:|
| Register / Login | ✅ | ✅ | ✅ |
| View own profile | ✅ | ✅ | ✅ |
| View financial records | ✅ | ✅ | ✅ |
| Filter records | ✅ | ✅ | ✅ |
| View dashboard analytics | ❌ | ✅ | ✅ |
| Create financial records | ❌ | ❌ | ✅ |
| Update financial records | ❌ | ❌ | ✅ |
| Delete financial records | ❌ | ❌ | ✅ |
| List / manage users | ❌ | ❌ | ✅ |
| Change user roles | ❌ | ❌ | ✅ |
| Deactivate users | ❌ | ❌ | ✅ |

New users who self-register get the `viewer` role by default. An admin must promote them.

---

## Access Control Design

Access control uses **FastAPI dependency injection** in `app/core/dependencies.py`.

```python
# get_current_user — verifies JWT and loads user from DB
async def get_current_user(credentials=Depends(HTTPBearer())) -> dict:
    payload = decode_access_token(credentials.credentials)
    return db_get_user_by_id(payload["sub"])

# require_role — wraps get_current_user and checks the role
def require_role(*roles: Role):
    async def checker(credentials=Depends(HTTPBearer())) -> dict:
        user = await get_current_user(credentials)
        if user["role"] not in [r.value for r in roles]:
            raise ForbiddenException()
        return user
    return checker
```

Every protected endpoint declares its requirement directly in its signature:

```python
@router.get("/api/records")
def list_records(user=Depends(get_current_user)):          # any authenticated user
    ...

@router.post("/api/records")
def create_record(admin=Depends(require_role(Role.ADMIN))): # admin only
    ...

@router.get("/api/dashboard/summary")
def summary(user=Depends(require_role(Role.ANALYST, Role.ADMIN))): # analyst or admin
    ...
```

This makes access requirements auditable at a glance — you can read what any endpoint requires without looking at its business logic.

---

## Error Handling

All errors return a consistent JSON shape:

```json
{ "detail": "Human-readable error message" }
```

| Status | Meaning | When |
|---|---|---|
| `400` | Bad Request | Invalid input, business rule violations, bad UUID format |
| `401` | Unauthorized | Missing, invalid, or expired token |
| `403` | Forbidden | Valid token but insufficient role |
| `404` | Not Found | Resource does not exist or was soft-deleted |
| `409` | Conflict | Duplicate resource (e.g. email already registered) |
| `422` | Unprocessable Entity | Request body fails Pydantic schema validation |
| `500` | Internal Server Error | Unexpected errors, caught by global exception handler |

**UUID validation:** Path parameters like `{id}` are validated using Python's built-in `uuid.UUID` before any database call. An invalid UUID format returns `400` with a clear message — never a `500`.

---

## Running Tests

The automated test suite covers 68 scenarios end-to-end. Start the server first, then:

```bash
python -m scripts.test_api
```

| Module | Cases |
|---|---|
| Auth | 12 |
| Users | 12 |
| Records | 24 |
| Dashboard | 12 |
| Data integrity | 1 |
| **Total** | **61** |

All happy paths, validation failures, and access control checks are covered.

---

## Design Decisions and Assumptions

### Authentication
- JWT tokens use HS256 signing with configurable expiry (default 60 minutes).
- No refresh token — kept simple for this assessment scope.
- Passwords are hashed with bcrypt via `passlib` before storing.

### Access Control
- Supabase Row Level Security (RLS) is **disabled**. Access control is enforced entirely in FastAPI middleware using `require_role()`. This gives full control over error messages and keeps all security logic in one place in application code.
- The `SUPABASE_SERVICE_ROLE_KEY` is used server-side to interact with the database directly.

### Soft Delete
- Financial records are never physically deleted. Setting `deleted_at` preserves audit history and enables potential data recovery. All read queries filter `deleted_at IS NULL`.

### Centralised DB Queries
- All Supabase calls live in `app/core/db_queries.py`. No module ever imports the Supabase client directly. This makes the database layer easy to mock in tests and easy to swap out entirely.
- `maybe_single()` is used instead of `single()` for lookups that may return 0 rows, wrapped in `try/except APIError` to handle malformed inputs gracefully and always return `None` instead of crashing.

### What Was Not Implemented
- **Refresh tokens** — the current JWT flow is sufficient to demonstrate the auth architecture.
- **Rate limiting** — would be added via `slowapi` middleware in production.
- **Full-text search** — category and type filters cover the required use cases.
- **Multi-tenancy** — single-organisation system as described in the scenario.