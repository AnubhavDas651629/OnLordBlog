from contextlib import asynccontextmanager
from typing import Annotated
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi import FastAPI, HTTPException, Request, Response, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException
from sqlalchemy import select, func, select, text 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import models
from database import engine, get_db
from routers import posts, users
from config import settings

@asynccontextmanager
async def lifespan(_app: FastAPI):
    #startup, basically turning on the async engine on
    yield
    await engine.dispose()

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(posts.router, prefix="/api/posts", tags=["posts"])

# Security Header Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next): #call_next basically is a middleware which modifies(adds security feautures before sending/reviecing the response)
    response = await call_next(request)
    response.headers["X-Frame-Options"] = "SAMEORIGIN"  # X-Frame-Origin prevents other websites from embedding our site in an iframe, which prevents clickjacking attacks
    response.headers["X-Content-Type-Options"] = "nosniff" #X-content-type-options tells the brwoser to trust the content type that we sent and not guess what type of content it is
    if "Referrer-Policy" not in response.headers:
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    if request.url.hostname not in ("localhost", "127.0.0.1"):  # Strict-transport-Security tells browaser to always use https when visiting our site, but we skip this for local host and 127.0.0.1
        response.headers["Strict-Transport-Security"] = (
            "max-age=63072000; includeSubDomains"
        )

    return response

# Health Check endpoint, imp as it tells if everything is working fine if not then alerts, in our model our database is our heart if this is down everything else is down
@app.get("/health")
async def health_check(db: Annotated[AsyncSession, Depends(get_db)]):
    try:
        await db.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database unavailable",
        ) from exc 
    return {"status":"healthy"}


# include_in_schema=False -> donnot add documentions in http://127.0.0.1:8000/docs
# response_class=HTMLResponse -> helps responses get in HTML format
# request: Request -> needed to use the jijga 2 template
@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
async def home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    count_result = await db.execute(select(func.count()).select_from(models.Post))
    total = count_result.scalar() or 0

    result = await db.execute(
    select(models.Post)
    .options(selectinload(models.Post.author))
    .order_by(models.Post.date_posted.desc())
    .limit(settings.posts_per_page),
    )
    posts = result.scalars().all()

    has_more = len(posts) < total
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home", "limit": settings.posts_per_page, "has_more": has_more,}, # using {"posts": posts} via jinja 2 to access posts from home.html
    )


@app.get("/posts/{post_id}", include_in_schema=False)
async def post_page(request: Request,post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):  
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id == post_id),
        )
    post = result.scalars().first()
    if post:
        title = post.title[:50]
        return templates.TemplateResponse(
            request,
            "post.html",
            {"post":post, "title": title},
        )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "post not found")


@app.get("/users/{user_id}/posts", include_in_schema=False, name="user_posts")
async def user_posts_page(
    request: Request,
    user_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    count_result = await db.execute(
        select(func.count())
        .select_from(models.Post)
        .where(models.Post.user_id == user_id),
    )
    total = count_result.scalar() or 0

    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id)
        .order_by(models.Post.date_posted.desc())
        .limit(settings.posts_per_page),
    )
    posts = result.scalars().all()

    has_more = len(posts) < total

    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {
            "posts": posts,
            "user": user,
            "title": f"{user.username}'s Posts",
            "limit": settings.posts_per_page,
            "has_more": has_more,
        },
    )
    
    
@app.get("/login", include_in_schema=False)
async def login_page(request: Request):
    return templates.TemplateResponse(
        request,
        "login.html",
        {"title": "Login"},
    )


@app.get("/register", include_in_schema=False)
async def register_page(request: Request):
    return templates.TemplateResponse(
        request,
        "register.html",
        {"title": "Register"},
    )

@app.get("/account", include_in_schema=False)
async def account_page(request: Request):
    return templates.TemplateResponse(
        request,
        "account.html",
        {"title": "Account"},
    )

@app.get("/forgot-password", include_in_schema=False)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse(
        request,
        "forgot_password.html",
        {"title": "Forgot Password"},
    )

@app.get("/reset-password", include_in_schema=False)
async def reset_password_page(request:Request):
    response = templates.TemplateResponse(
        request,
        "reset_password.html",
        {"title":"Reset Password"},
    )
    response.headers["Referrer-Policy"] = "no-referrer"
    return response

@app.exception_handler(StarletteHTTPException)
async def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    
    if request.url.path.startswith("/api"):
        return await http_exception_handler(request, exception)

    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )

    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": exception.status_code,
            "title": exception.status_code,
            "message": message,
        },
        status_code=exception.status_code,
    )



# http://127.0.0.1:8000/posts/hello, handles this kind of error if someone enetered "hello", instead of int and helps ui from breaking
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return await request_validation_exception_handler(request, exception)
    
    return templates.TemplateResponse(
        request,
        "error.html",
        {
            "status_code": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "title": status.HTTP_422_UNPROCESSABLE_CONTENT,
            "message": "Invalid request. Please check your input and try again.",
        },
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
    )

