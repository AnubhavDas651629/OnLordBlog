from re import template
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles 
from fastapi.responses import HTMLResponse  # Fixed typo here (HIML -> HTML)
from fastapi.templating import Jinja2Templates
from starlette.exceptions import HTTPException as StarletteHTTPException

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

templates = Jinja2Templates(directory="templates")

posts: list[dict] = [
    {
        "id": 1,
        "author": "Corey Schafer",
        "title": "FastAPI is Awesome",
        "content": "This framework is really easy to use and super fast.",
        "date_posted": "April 20, 2025",
    },
    {
        "id": 2,
        "author": "Jane Doe",
        "title": "Python is Great for Web Development",
        "content": "Python is a great language for web development, and FastAPI makes it even better.",
        "date_posted": "April 21, 2025",
    },
]

# include_in_schema=False -> donnot add documentions in http://127.0.0.1:8000/docs
# response_class=HTMLResponse -> helps responses get in HTML format

@app.get("/", include_in_schema=False , name = "home")
@app.get("/posts", include_in_schema=False, name = "posts")

# using {"posts": posts} via jinja 2 to access posts from home.html


# request: Request -> needed to use the jijga 2 templates
def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Home"},)


@app.get("/posts/{post_id}", include_in_schema=False)
def post_page(request: Request,post_id: int):  
    for post in posts:
        if post.get("id") == post_id:
            title = post['title'][:50]
            return templates.TemplateResponse(request, "post.html", {"post": post, "title": title} )
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "post not found")

@app.get("/api/posts")
def get_posts():  
    return posts

# in this for examples an user enters api/posts/12002 in the url, then 12002 gets posted as post_id in the the function
# anything else apart from integer returns an validation error
@app.get("/api/posts/{post_id}")
def get_post(post_id: int):  
    for post in posts:
        if post.get("id") == post_id:
            return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "post not found")
