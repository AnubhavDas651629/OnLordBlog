from http import client
import pytest
from httpx import AsyncClient
from urllib3 import response

from tests.conftest import auth_header, create_test_user, login_user

@pytest.mark.anyio
async def test_get_posts_empty(client: AsyncClient):
    response = await client.get("/api/posts")

    assert response.status_code == 200
    data = response.json()
    assert data["posts"] == []
    assert data["total"] == 0
    assert data["has_more"] is False

@pytest.mark.anyio
async def test_get_posts_not_found(client: AsyncClient):
    response = await client.get("/api/posts/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Post not found"


# Test Create Post Success
@pytest.mark.anyio
async def test_create_post_successs(Client:AsyncClient):
    user = await create_test_user(client)
    token = await login_user(client)
    headers = auth_header(token)

    response = await client.post(
        "/api/posts",
        json={"title":"My first post", "content": "This is the content"},
        headers = headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "My first Post"
    assert data["content"] == "This is the content"
    assert data["user_id"] == user["id"]
    assert "id" in data
    assert "date_posted" in data
    assert data["author"]["username"] == "testuser"

@pytest.mark.anyio
async def test_create_post_unauthorized(client: AsyncClient):
    response = await client.post(
        "/api/posts",
        json={"title": "Test Post", "content": "Test content"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Not Authenticated"

# Test update Post success


