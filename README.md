# FastAPI Blog 🚀

A modern, full-featured blogging platform built from the ground up with **FastAPI**, **SQLAlchemy 2.0 (Async)**, **PostgreSQL / SQLite**, **AWS S3**, and **Jinja2**. 

This project demonstrates production-ready backend architecture, bridging robust JSON REST APIs with dynamic server-side rendered HTML templates. It incorporates comprehensive security practices, asynchronous image processing pipelines, background email dispatching, and clean dependency injection.

---

## ✨ Features & Highlights

- **🏛️ Hybrid Architecture**:
  - **JSON REST API** endpoints (`/api/users`, `/api/posts`) with automatic interactive OpenAPI documentation.
  - **Server-Side Rendering (SSR)** using **Jinja2** templates for responsive, rich user interfaces (Home, Posts, Account, Login, Register, Forgot/Reset Password).
- **🔐 Robust Security & Authentication**:
  - **OAuth2 with Password Flow**: Stateless Bearer **JWT** access tokens signed via `PyJWT`.
  - **Argon2 Password Hashing**: State-of-the-art password verification using `pwdlib`.
  - **Security Headers Middleware**: Automatically injects `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`, `Referrer-Policy`, and `Strict-Transport-Security` headers to safeguard against clickjacking, MIME-sniffing, and XSS.
  - **Secure Password Reset Flow**: Generates URL-safe base64 reset tokens, stores only SHA-256 hashes in the database, and enforces 1-hour expiration tracking.
- **🗄️ Asynchronous Database & ORM**:
  - Built on **SQLAlchemy 2.0** utilizing `AsyncSession` and `async_sessionmaker`.
  - Prevents N+1 query performance bottlenecks using explicit eager loading (`selectinload`).
  - Supports **PostgreSQL** (e.g., Neon Serverless Postgres pooled runtime) and **SQLite** (`aiosqlite`).
  - Managed schema evolutions via **Alembic** migrations.
- **🖼️ AWS S3 & Image Processing Pipeline**:
  - Profile picture uploads with strict file size constraints (max 5MB) and type validation.
  - Asynchronous threadpool processing via **Pillow**: automatic EXIF orientation transposition, Lanczos high-quality cropping/resampling to 300x300px, RGB conversion, and JPEG compression.
  - Seamless AWS S3 storage integration (`boto3`) with UUIDv4 randomized filenames.
- **📧 Async Email Dispatching & Background Tasks**:
  - Non-blocking email sending powered by `aiosmtplib` and FastAPI `BackgroundTasks`.
  - Multi-part HTML and plain-text password reset templates.
- **🩺 DevOps & Production Readiness**:
  - Multi-stage **Dockerfile** powered by Astral's `uv` package manager, optimized for minimal layer size and running under a non-root security user (`appuser`).
  - Dedicated `/health` probe verifying live database connectivity.
  - Automated database seed script (`populate_db.py`) generating realistic test accounts, profile pictures, and paginated blog posts.

---

## 🛠️ Tech Stack

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

## 📁 Repository Structure

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

## 🚀 Getting Started

### 1. Prerequisites
- **Python 3.12+**
- **[uv](https://docs.astral.sh/uv/)** (Recommended package manager) or standard `pip`
- An **AWS S3 Bucket** (for profile picture storage)
- A **PostgreSQL** database (or SQLite for quick local trials)
- An **SMTP Server** (e.g., [Mailtrap](https://mailtrap.io/) for development testing)

### 2. Clone & Install Dependencies

```bash
git clone <repository_url>
cd fastapi_blog

# Using uv (Superfast dependency resolution)
uv sync

# OR using standard pip & virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

### 3. Environment Variables Configuration

Create a `.env` file in the root directory. You can reference the required parameters below:

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
# Optional endpoint URL (e.g. for S3-compatible providers like MinIO / Cloudflare R2):
# S3_ENDPOINT_URL=""

# SMTP Email Dispatcher (e.g., Mailtrap Sandbox)
MAIL_SERVER="sandbox.smtp.mailtrap.io"
MAIL_PORT=2525
MAIL_USERNAME="your_smtp_username"
MAIL_PASSWORD="your_smtp_password"
MAIL_FROM="noreply@fastapiblog.com"
MAIL_USE_TLS=true
```

### 4. Run Database Migrations

Apply the existing Alembic migration scripts to generate your database tables:

```bash
uv run alembic upgrade head
```

### 5. Seed Database (Optional)

Populate your database with sample users, mock blog posts, and avatar pictures:

```bash
uv run python populate_db.py
```

### 6. Launch Development Server

Start the FastAPI application server with live reload enabled:

```bash
uv run fastapi dev main.py
# OR directly via uvicorn
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Visit the web application at: **[http://127.0.0.1:8000](http://127.0.0.1:8000)**

---

## 🔌 API Documentation & Endpoints

When the server is running, FastAPI automatically generates interactive API documentation.
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

### 📡 REST API Summary (`/api`)

| Method | Endpoint | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/users` | Register a new user account | ❌ |
| `POST` | `/api/users/token` | Obtain OAuth2 Bearer JWT access token | ❌ |
| `GET` | `/api/users/me` | Retrieve authenticated user details | ✅ |
| `GET` | `/api/users/{id}` | Retrieve public profile of a user | ❌ |
| `PATCH` | `/api/users/{id}` | Update username or email address | ✅ |
| `DELETE`| `/api/users/{id}` | Delete user account and associated posts | ✅ |
| `PATCH` | `/api/users/{id}/picture` | Upload & process new profile avatar | ✅ |
| `DELETE`| `/api/users/{id}/picture` | Remove avatar and revert to default | ✅ |
| `POST` | `/api/users/forgot-password` | Request password reset token & email | ❌ |
| `POST` | `/api/users/reset-password` | Submit password reset token & new password | ❌ |
| `PATCH` | `/api/users/me/password` | Change password for logged-in user | ✅ |
| `GET` | `/api/posts` | List paginated blog posts (`skip`, `limit`) | ❌ |
| `POST` | `/api/posts` | Create a new blog post | ✅ |
| `GET` | `/api/posts/{id}` | Fetch a specific blog post | ❌ |
| `PUT` | `/api/posts/{id}` | Fully update a blog post | ✅ |
| `PATCH` | `/api/posts/{id}` | Partially update a blog post | ✅ |
| `DELETE`| `/api/posts/{id}` | Delete a blog post | ✅ |

### 🖥️ Frontend View Routes (SSR)

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
| `/health` | Kubernetes / Docker health check probe (`{"status": "healthy"}`) |

---

## 🐳 Docker Deployment

The included multi-stage `Dockerfile` leverages `uv` bytecode compilation and link optimizations for lightweight container builds.

```bash
# Build the production Docker image
docker build -t fastapi-blog:latest .

# Run the container
docker run -d -p 8080:8080 --env-file .env fastapi-blog:latest
```

---

## 🧪 Testing

The test suite runs asynchronously using `pytest`, `pytest-asyncio`, and `httpx.AsyncClient`.

```bash
# Execute unit and integration tests
uv run pytest -v
```

---

## 📄 License

This project is open-source and available for educational and commercial use.
