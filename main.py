from re import template
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles 
from fastapi.responses import HTMLResponse  # Fixed typo here (HIML -> HTML)
from fastapi.templating import Jinja2Templates

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

@app.get("/", include_in_schema=False, name = "home")
@app.get("/posts", include_in_schema=False, name = "posts")

# using {"posts": posts} via jinja 2 to access posts from home.html

def home(request: Request):
    return templates.TemplateResponse(request, "home.html", {"posts": posts, "title": "Home"},)

@app.get("/api/post")
def get_posts():  
    return posts