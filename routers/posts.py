
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import desc, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import query, selectinload
from sqlalchemy.sql.functions import current_user
from config import settings
import models
from database import get_db
from schemas import PostCreate, PostResponse, PostUpdate, PaginatedPostsResponse
from auth import CurrentUser

router = APIRouter()
@router.get("", response_model=PaginatedPostsResponse)
async def get_posts(
    db: Annotated[AsyncSession, Depends(get_db)],
    # skip 20 and limit 10 will give you posts from 21 to 30
    skip: Annotated[int, Query(ge=0)] = 0, # skip a particular post
    limit: Annotated[int, Query(ge=1, le=100)] = settings.posts_per_page, # sets the limit bewteen 1 and 100, betweeen the number of posts someone could ask for and default is set to 10
):
    count_result = await db.execute(select(func.count()).select_from(models.Post)) # from func.count()).select_from(models.Post) -> we are counting the total number of posts and adding a count
    total = count_result.scalar() or 0 # this returns the total count of post, if no post then 0

    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .order_by(models.Post.date_posted.desc()) # models.Post.date_posted.desc() -> this shows all the post in the website latest uploaded to last uploaded
        .offset(skip)
        .limit(limit),
        )
    posts = result.scalars().all()

    has_more = skip + len(posts) < total # if the number of posts is less than the total then there are more posts to fetch

    return PaginatedPostsResponse(
        posts= [PostResponse.model_validate(post) for post in posts], # over here the posts is the posts that is defined in line 31
        total=total,
        skip=skip,
        limit=limit,
        has_more=has_more,
    ) 


@router.post("", response_model=PostResponse, status_code=status.HTTP_201_CREATED,)
async def create_post(
    post: PostCreate, 
    current_user: CurrentUser, 
    db:Annotated[AsyncSession, Depends(get_db)]):
    
    new_post = models.Post(
        title = post.title,
        content = post.content,
        user_id = current_user.id,
    )
    db.add(new_post)
    await db.commit()
    await db.refresh(new_post, attribute_names=["author"])
    return new_post

# in this for examples an user enters api/posts/12002 in the url, then 12002 gets posted as post_id in the the function
# anything else apart from integer returns an validation error
@router.get("/{post_id}", response_model=PostResponse)
async def get_post(post_id: int, db:Annotated[AsyncSession,Depends(get_db)]):
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.id == post_id))
    post = result.scalars().first()
    if post:
        return post
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="Post not found")
    
@router.put("/{post_id}", response_model=PostResponse)
async def update_post_full(
    post_id: int, 
    post_data: PostCreate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail = "Post not found",
        )    
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this post"
        )

    post.title = post_data.title
    post.content = post_data.content

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post

@router.patch("/{post_id}", response_model=PostResponse)
async def update_post_partial(
    post_id: int,
    post_data: PostUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession,Depends(get_db)],
):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail= "Post not found"
        )
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this post"
        )
    #exclude_unset = True -> if someone only changed the title from A to B then other fields donnot gets changed into none but stays the same as it was
    # update_data is then basically a dictionary that is key title and new value
    update_data = post_data.model_dump(exclude_unset=True)  
    for field, value in update_data.items():  # example if we only update the title, then 'field' is title and the new title value is 'value'
        setattr(post, field, value)

    await db.commit()
    await db.refresh(post, attribute_names=["author"])
    return post

@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(post_id: int, current_user: CurrentUser, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.Post).where(models.Post.id == post_id))
    post = result.scalars().first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail= "Post not found"
        )
    if post.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this post"
        )
    await db.delete(post)
    await db.commit()