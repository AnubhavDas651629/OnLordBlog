# FastAPI Blog Platform

A modern, full-featured blogging platform built from the ground up with **FastAPI**, **SQLAlchemy 2.0 (Async)**, **PostgreSQL / SQLite**, **AWS S3**, and **Jinja2**. 

This project demonstrates production-ready backend architecture, bridging robust JSON REST APIs with dynamic server-side rendered HTML templates. It incorporates comprehensive security practices, asynchronous image processing pipelines, background email dispatching, and clean dependency injection.

---

## System Architecture

The following diagram illustrates the request lifecycle, middleware layer, route routing, business services, and external persistence integrations:

```mermaid
graph TD
    Client["Client (Browser / API Consumer)"] -->|HTTP / REST Requests| App["FastAPI Application Core"]

    subgraph MiddlewareLayer ["Security & Middleware Layer"]
        App --> SecHeaders["Security Headers Middleware"]
        SecHeaders --> CORS["CORS Middleware"]
    end

    subgraph RouterLayer ["Routing & Presentation"]
        CORS --> SSR["Jinja2 SSR View Routes"]
        CORS --> APIRouters["REST API Routers (/api)"]
        APIRouters --> UsersRouter["Users Router (/api/users)"]
        APIRouters --> PostsRouter["Posts Router (/api/posts)"]
    end

    subgraph ServiceLayer ["Services & Core Logic"]
        UsersRouter --> Auth["OAuth2 & JWT Auth Service"]
        UsersRouter --> ImageProc["Pillow Image Processing"]
        UsersRouter --> BgTasks["Background Email Dispatcher"]
        PostsRouter --> Paginate["Pagination & Eager Loading Service"]
    end

    subgraph StorageLayer ["Persistence & External Infrastructure"]
        Auth --> DB[(Async SQLAlchemy Engine)]
        Paginate --> DB
        DB --> Postgres["PostgreSQL / Neon Pooler"]
        DB --> SQLite["SQLite (Local / Testing)"]
        
        ImageProc --> S3["AWS S3 Bucket (Avatars)"]
        BgTasks --> SMTP["SMTP Server / Mailtrap"]
    end
```

---

## Key Features

- **Hybrid Architecture**:
  - **JSON REST API** endpoints (`/api/users`, `/api/posts`) conforming to OpenAPI specifications with interactive Swagger UI and ReDoc documentation.
  - **Server-Side Rendering (SSR)** using **Jinja2** templates for dynamic web interfaces (Home, Posts Archive, User Dashboard, Authentication, and Password Recovery).
- **Security & Authentication**:
  - **OAuth2 with Password Flow**: Stateless Bearer JWT access tokens with structured payload claims signed via `PyJWT`.
  - **Argon2 Password Hashing**: Cryptographic password storage and verification powered by `pwdlib`.
  - **Security Headers Middleware**: Enforces defense-in-depth by injecting `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, and `Strict-Transport-Security` headers across all HTTP responses.
  - **Account Recovery Pipeline**: Cryptographically secure random token generation (URL-safe base64) with SHA-256 database hashing and strict 60-minute TTL expiration enforcement.
- **Asynchronous Database & ORM**:
  - Built on **SQLAlchemy 2.0** utilizing asynchronous drivers (`psycopg` and `aiosqlite`) via `AsyncSessionLocal`.
  - Query optimization utilizing explicit eager relationship loading (`selectinload`) to eliminate N+1 latency bottlenecks.
  - Schema versioning and migration tracking managed through **Alembic**.
- **Media Processing & Storage**:
  - Profile avatar uploads with strict size boundaries (maximum 5MB) and MIME type verification.
  - Asynchronous threadpool execution (`run_in_threadpool`) offloading CPU-bound **Pillow** operations: automatic EXIF orientation transposition, Lanczos resampling (300x300px), color mode normalization, and JPEG optimization.
  - External persistence mapping to AWS S3 (`boto3`) utilizing non-enumerable UUIDv4 object keys.
- **Background Task Execution**:
  - Asynchronous email dispatching powered by `aiosmtplib` and FastAPI `BackgroundTasks` for zero-latency HTTP responses during password resets.
- **DevOps & Containerization**:
  - Multi-stage **Dockerfile** powered by Astral's `uv` package manager, reducing container image footprint and running exclusively under a non-privileged system user (`appuser`).
  - Active `/health` probe endpoint for container orchestration readiness and liveness checks.
  - Comprehensive automated database seeding script (`populate_db.py`).

---

## Technology Stack

| Category | Technologies |
| :--- | :--- |
| **Framework** | [FastAPI](https://fastapi.tiangolo.com/) (Python >= 3.12) |
| **Database ORM** | [SQLAlchemy 2.0](https://www.sqlalchemy.org/) (AsyncIO Engine) |
| **Database Drivers** | `psycopg` (PostgreSQL), `aiosqlite` (SQLite) |
| **Migrations** | [Alembic](https://alembic.sqlalchemy.org/) |
| **Auth & Security** | `PyJWT`, `pwdlib[argon2]`, `passlib[argon2]` |
| **Storage & Media** | `boto3` (AWS S3), `Pillow` (PIL) |
| **Email & Templating** | `aiosmtplib`, `Jinja2` |
| **Validation & Config** | `Pydantic v2`, `pydantic-settings` |
| **Package Manager** | [uv](https://docs.astral.sh/uv/) |
| **Containerization** | Docker (Multi-stage slim-bookworm build) |

---

## Repository Structure

```text
fastapi_blog/
├── alembic/                # Database migration scripts
├── media/                  # Local media fallback storage
├── populate_images/        # Sample avatar assets for database seeding
├── routers/                # Application API and View Route handlers
│   ├── posts.py            # Blog post CRUD & pagination endpoints
│   └── users.py            # User registration, auth, avatars & password reset
├── static/                 # Static assets (CSS, default avatars, JS)
├── templates/              # Jinja2 HTML templates (Home, Post, Account, Auth)
│   └── email/              # Email HTML notification templates
├── tests/                  # Asynchronous Pytest test suite
├── alembic.ini             # Alembic configuration
├── auth.py                 # JWT token generation, OAuth2 scheme & password hashing
├── config.py               # Environment variables & Pydantic settings schema
├── database.py             # Async SQLAlchemy engine & session factory
├── email_utils.py          # SMTP client & background email dispatchers
├── image_utils.py          # Pillow image processing & S3 upload/delete utilities
├── main.py                 # FastAPI app instantiation, middleware & health probes
├── models.py               # SQLAlchemy declarative database models (User, Post, Token)
├── populate_db.py          # Automated test data seeding script
├── pyproject.toml          # Project metadata & uv dependency definitions
├── schemas.py              # Pydantic validation & serialization schemas
└── Dockerfile              # Multi-stage production container definition
```

---

## Getting Started

### 1. Prerequisites
- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (Recommended package manager) or standard `pip`
- An **AWS S3 Bucket** (for profile picture storage)
- A **PostgreSQL** database (or SQLite for local development)
- An **SMTP Server** (e.g., [Mailtrap](https://mailtrap.io/) for development testing)

### 2. Clone & Install Dependencies

```bash
git clone <repository_url>
cd fastapi_blog

# Using uv (High-speed dependency resolution)
uv sync

# OR using standard pip & virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Environment Variables Configuration

Create a `.env` file in the project root directory. Reference the required parameters below:

```ini
# Application Security
# Generate a secure secret key via: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY="your_64_character_hex_secret_key"

# Database Connection (PostgreSQL or SQLite)
# Example PostgreSQL (Neon DB):
DATABASE_URL="postgresql+psycopg://user:password@hostname.region.aws.neon.tech/dbname?sslmode=require"
# Example SQLite:
# DATABASE_URL="sqlite+aiosqlite:///./blog.db"

# Frontend Host
FRONTEND_URL="http://localhost:8000"

# AWS S3 Storage
S3_BUCKET_NAME="your-s3-bucket-name"
S3_REGION="us-east-1"
S3_ACCESS_KEY_ID="your_aws_access_key"
S3_SECRET_ACCESS_KEY="your_aws_secret_key"
# Optional endpoint URL (e.g. for S3-compatible providers):
# S3_ENDPOINT_URL=""

# SMTP Email Dispatcher
MAIL_SERVER="sandbox.smtp.mailtrap.io"
MAIL_PORT=2525
MAIL_USERNAME="your_smtp_username"
MAIL_PASSWORD="your_smtp_password"
MAIL_FROM="noreply@fastapiblog.com"
MAIL_USE_TLS=true
```

### 4. Run Database Migrations

Apply existing Alembic migration scripts to initialize the database schema:

```bash
uv run alembic upgrade head
```

### 5. Seed Database (Optional)

Populate the database with test accounts, mock posts, and profile avatars:

```bash
uv run python populate_db.py
```

### 6. Launch Development Server

Start the application server with hot reload enabled:

```bash
uv run fastapi dev main.py
# OR directly via uvicorn
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Access the application interface at: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## API Documentation & Endpoints

When running locally, FastAPI generates interactive API specifications automatically.
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### REST API Summary (`/api`)

| Method | Endpoint | Description | Authentication |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/users` | Register a new user account | None |
| `POST` | `/api/users/token` | Obtain OAuth2 Bearer JWT access token | None |
| `GET` | `/api/users/me` | Retrieve authenticated user details | Required |
| `GET` | `/api/users/{id}` | Retrieve public profile of a user | None |
| `PATCH` | `/api/users/{id}` | Update username or email address | Required |
| `DELETE`| `/api/users/{id}` | Delete user account and associated posts | Required |
| `PATCH` | `/api/users/{id}/picture` | Upload & process new profile avatar | Required |
| `DELETE`| `/api/users/{id}/picture` | Remove avatar and revert to default | Required |
| `POST` | `/api/users/forgot-password` | Request password reset token & email | None |
| `POST` | `/api/users/reset-password` | Submit password reset token & new password | None |
| `PATCH` | `/api/users/me/password` | Change password for logged-in user | Required |
| `GET` | `/api/posts` | List paginated blog posts (`skip`, `limit`) | None |
| `POST` | `/api/posts` | Create a new blog post | Required |
| `GET` | `/api/posts/{id}` | Fetch a specific blog post | None |
| `PUT` | `/api/posts/{id}` | Fully update a blog post | Required |
| `PATCH` | `/api/posts/{id}` | Partially update a blog post | Required |
| `DELETE`| `/api/posts/{id}` | Delete a blog post | Required |

### Frontend View Routes (SSR)

| Route | Description |
| :--- | :--- |
| `/` or `/posts` | Main homepage listing latest blog posts with pagination |
| `/posts/{id}` | Individual blog post reader page |
| `/users/{id}/posts` | Author-specific blog post archive page |
| `/login` | User authentication interface |
| `/register` | Account registration interface |
| `/account` | User profile & settings dashboard |
| `/forgot-password` | Password reset request form |
| `/reset-password` | Token verification & password update form |
| `/health` | Service liveness probe (`{"status": "healthy"}`) |

---

## Container Deployment

The multi-stage `Dockerfile` leverages `uv` bytecode compilation and dependency isolation to construct lightweight production containers.

```bash
# Build the production Docker image
docker build -t fastapi-blog:latest .

# Launch containerized service
docker run -d -p 8080:8080 --env-file .env fastapi-blog:latest
```

---

## Testing

The test suite executes asynchronously using `pytest`, `pytest-asyncio`, and `httpx.AsyncClient`.

```bash
# Run automated test suite
uv run pytest -v
```

---

## License

This project is open-source and distributed under standard licensing terms.
