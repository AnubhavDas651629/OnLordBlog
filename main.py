from turtle import title, update
from typing import Annotated
from unittest import result
from fastapi import FastAPI, HTTPException, Request, status, Depends
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.sql.functions import user
from starlette.exceptions import HTTPException as StarletteHTTPException
from schemas import PostCreate, PostResponse, UserCreate, UserResponse, PostUpdate, UserUpdate
from sqlalchemy import select
from sqlalchemy.orm import Session
import models
from database import Base, engine, get_db


Base.metadata.create_all(bind=engine)
app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

app.mount("/media", StaticFiles(directory="media"), name = "media")

templates = Jinja2Templates(directory="templates")


# include_in_schema=False -> donnot add documentions in http://127.0.0.1:8000/docs
# response_class=HTMLResponse -> helps responses get in HTML format

@app.get("/", include_in_schema=False, name="home")
@app.get("/posts", include_in_schema=False, name="posts")
def home(request: Request, db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "home.html",
        {"posts": posts, "title": "Home"},
    )
# using {"posts": posts} via jinja 2 to access posts from home.html


# request: Request -> needed to use the jijga 2 templates
# @app.get("/", include_in_schema=False, name="home")
# @app.get("/posts", include_in_schema=False, name="posts")
# def home(request: Request, db: Annotated[Session, Depends(get_db)]):
#     result= db.execute(select(models.Post))
#     posts = result.scalars().all()
#     return templates.TemplateResponse(
#         request,
#         "home.html",
#         {"posts":posts, "title":"Home"},
#     )


@app.get("/posts/{post_id}", include_in_schema=False)
def post_page(request: Request,post_id: int, db: Annotated[Session, Depends(get_db)]):  
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
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
def user_posts_page(
    request: Request,
    user_id: int, 
    db: Annotated[Session, Depends(get_db),]
):  
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found", 
        )

    result = db.execute(select(models.Post).where(models.Post.user_id==user_id))
    posts = result.scalars().all()
    return templates.TemplateResponse(
        request,
        "user_posts.html",
        {"posts": posts, "user": user, "title": f"{user.username}'s Posts"},
    )

@app.post("/api/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED,)
def create_user(user: UserCreate, db: Annotated[Session, Depends(get_db)]): #get_db each database request gets its own session and clears up after that
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
    db.commit() # commits the user to the database
    db.refresh(new_user) # refreshes the database

    return new_user

@app.get("/api/users/{user_id}", response_model=UserResponse)
def get_user(user_id: int, db: Annotated[Session, Depends(get_db)]): 
    result = db.execute(
        select(models.User).where(models.User.id == user_id),
        )
    user = result.scalars().first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "user not found")

@app.get("/api/users/{user_id}/posts", response_model=list[PostResponse])
def get_user_post(user_id: int, db = Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )    
    result = db.execute(select(models.Post).where(models.Post.user_id == user_id))
    posts = result.scalars().all()
    return posts

# PostResponse is from schmemas.py
@app.get("/api/post", response_model=list[PostResponse])
def get_posts(db: Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post))
    posts = result.scalars().all()
    return posts


@app.post("/api/posts", response_model=PostResponse, status_code=status.HTTP_201_CREATED,)
def create_post(post: PostCreate, db:Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.User).where(models.User.id == post.user_id))
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
    db.commit()
    db.refresh(new_post)
    return new_post
# in this for examples an user enters api/posts/12002 in the url, then 12002 gets posted as post_id in the the function
# anything else apart from integer returns an validation error
@app.get("/api/posts/{post_id}", response_model=PostResponse)
def get_post(post_id: int, db:Annotated[Session,Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found")
    
@app.put("/api/posts/{post_id}", response_model=PostResponse)
def update_post_full(
    post_id: int, 
    post_data: PostCreate,
    db: Annotated[Session, Depends(get_db)],
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

    db.commit()
    db.refresh(post)
    return post

@app.patch("/api/post/{post_id}", response_model=PostResponse)
def update_post_partial(
    post_id: int,
    post_data: PostUpdate,
    db: Annotated[Session,Depends(get_db)],
):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
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

    db.commit()
    db.refresh(post)
    return post

@app.delete("/api/posts/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_post(post_id: int, db:Annotated[Session, Depends(get_db)]):
    result = db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= "Post not found"
        )
    db.delete(post)
    db.commit()
    
    
    

@app.exception_handler(StarletteHTTPException)
def general_http_exception_handler(request: Request, exception: StarletteHTTPException):
    message = (
        exception.detail
        if exception.detail
        else "An error occurred. Please check your request and try again."
    )
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=exception.status_code,
            content={"detail": message},
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
def validation_exception_handler(request: Request, exception: RequestValidationError):
    if request.url.path.startswith("/api"):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content={"detail": exception.errors()},
        )
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

