from pyexpat import model
from turtle import title, update
from contextlib import asynccontextmanager
from typing import Annotated
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from unittest import result
from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.sql.functions import user
from starlette.exceptions import HTTPException as StarletteHTTPException
from schemas import PostCreate, PostResponse, UserCreate, UserResponse, PostUpdate, UserUpdate
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import models
from database import Base, engine, get_db

@asynccontextmanager
async def lifespan(_app: FastAPI):
    #startup, basically turning on the async engine on
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose

app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount("/media", StaticFiles(directory="media"), name = "media")

templates = Jinja2Templates(directory="templates")


# include_in_schema=False -> donnot add documentions in http://127.0.0.1:8000/docs
# response_class=HTMLResponse -> helps responses get in HTML format
# request: Request -> needed to use the jijga 2 template
@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
async def home(request: Request, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).options(selectinload(models.Post.author)),)
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home"},
    )
# using {"posts": posts} via jinja 2 to access posts from home.html





@app.get("/posts/{post_id}", include_in_schema=False)
async def post_page(request: Request,post_id: int, db: Annotated[AsyncSession, Depends(get_db)]):  
    result = db.execute(
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
    db: Annotated[AsyncSession, Depends(get_db),]
):  
    result = await db.execute(
        select(models.User)
        .where(models.User.id == user_id)
    )
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found", 
        )

    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id==user_id)
    )
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )

@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED,)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]): #get_db each database request gets its own session and clears up after that
    result = db.execute(select(models.User).where(models.User.username == user.username),
    )
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username already exists",
        )

    result = db.execute(select(models.User).where(models.User.email == user.email),
    )
    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email already exists",
        )
    new_user = models.User(
        username=user.username,
        email=user.email,
    )
    db.add(new_user) # adds new user to database
    await db.commit() # commits the user to the database
    await db.refresh(new_user) # refreshes the database
    return new_user

@app.get("/api/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]): 
    result = db.execute(
        select(models.User).where(models.User.id == user_id),
        )
    user = result.scalars().first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "user not found")

@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
async def get_user_post(user_id: int, db = Annotated[AsyncSession, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )    
    result = db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return posts

@app.patch("/api/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, 
    user_update: UserUpdate,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user_update.username is not None and user_update.username != user.username:
        result = db.execute(
            select(models.User).where(models.User.username == user_update.username),     
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )
    if user_update.email is not None and user_update.email != user.email:
        result = db.execute(
            select(models.User).where(models.User.email == user_update.email),     
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="email already exists",
            )
#this is the manual way if someone does not want to use the set attr way as implemented in the prev patch route 
    if user_update.username is not None:
        user.username = user_update.username
    if user_update.email is not None:
        user.email = user_update.email
    if user_update.image_file is not None:
        user.image_file = user_update.image_file

    await db.commit()
    await db.refresh(user)
    return user

@app.delete("/api/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "user not found",
        )
    await db.delete(user)
    await db.commit()
    

# PostResponse is from schmemas.py
@app.get("/api/post", response_model=list[PostResponse])
async def get_posts(db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Post).options(selectinload(models.Post.author))
        )
    posts = result.scalars().all()
    return posts


@app.post("/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED,)
async def create_post(post: PostCreate, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == post.user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    new_post = models.Post(
        title = post.title,
        content = post.content,
        user_id = post.user_id,
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post, attribute_names=["author"])
    return new_post

# in this for examples an user enters api/posts/12002 in the url, then 12002 gets posted as post_id in the the function
# anything else apart from integer returns an validation error
@app.get("/api/posts/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db:Annotated[AsyncSession,Depends(get_db)]):
    result = db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found")
    
@app.put("/api/posts/{post_id}", response_model=PostResponse)
async def update_post_full(
    post_id: int, 
    post_data: PostCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail = "Post not found",
        )    
    if post_data.user_id != post.user_id:
        result = db.execute(
            select(models.User).where(models.User.id == post_data.user_id),
        )
        user = result.scalars().first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail = "User not found",
            )
    post.title = post_data.title
    post.content = post_data.content
    post.user_id = post_data.user_id

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post

@app.patch("/api/post/{post_id}", response_model=PostResponse)
async def update_post_partial(
    post_id: int,
    post_data: PostUpdate,
    db: Annotated[AsyncSession,Depends(get_db)],
):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code= status.HTTP_404_BAD_REQUEST,
            detail= "Post not found"
        )
    #exclude_unset = True -> if someone only changed the title from A to B then other fields donnot gets changed into none but stays the same as it was
    # update_data is then basically a dictionary that is key title and new value
    update_data = post_data.model_dump(exclude_unset=True)  
    for field, value in update_data.items():  # example if we only update the title, then 'field' is title and the new title value is 'value'
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post

@app.delete("/api/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= "Post not found"
        )
    await db.delete(post)
    await db.commit()
    
    
    

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

