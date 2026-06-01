from ntpath import exists
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy.sql.functions import user
import models
from database import get_db
import routers
from schemas import PostResponse, Token, UserCreate, UserPrivate, UserPublic, UserUpdate
from datetime import timedelta
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import func, select
from auth import create_access_token, hash_password, verify_password, CurrentUser
from config import settings
from PIL import UnidentifiedImageError
from starlette.concurrency import run_in_threadpool
from image_utlis import delete_profile_image, process_profile_image


router = APIRouter()


# in here while defining the address in "", by default it is "/api/users", now "/{post_id}" in routers means "/api/users/{post_id}"
@router.post("", response_model=UserPrivate, status_code=status.HTTP_201_CREATED,)
async def create_user(user: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]): #get_db each database request gets its own session and clears up after that
    result = await db.execute(select(models.User).where(
        func.lower(models.User.username) == user.username.lower()
        ),
    )
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="username already exists",
        )

    result = await db.execute(select(models.User).where(
        func.lower(models.User.email) == user.email.lower()
        ),
    )
    existing_email = result.scalars().first()

    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="email already exists",
        )
    new_user = models.User(
        username=user.username,
        email=user.email.lower(),
        password_hash = hash_password(user.password),
    )
    db.add(new_user) # adds new user to database
    await db.commit() # commits the user to the database
    await db.refresh(new_user) # refreshes the database
    return new_user


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    # look up user by email(case insensitive)
    # Note: OAuthpasOAuth2PasswordRequestForm uses "username" field, but we treat it as email
    result = await db.execute(
        select(models.User).where(
            func.lower(models.User.email) == form_data.username.lower(), # form_data is in OAuthpasOAuth2PasswordRequestForm and it supports only 2 arguments, .username and .password hence we aare comapring email wiht username
        )
    )
    user = result.scalars().first()

    #Verify user exixts and password is correct
    # Don't reveal which one failed
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate":"Bearer"}
        )

    # Create access token with user id as subject, first line is creating the expiration date for create_access_token fn which we defined in auth.py
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )

    return Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=UserPrivate)
async def get_current_user(current_user: CurrentUser):
    return current_user
   

@router.get("/{user_id}", response_model=UserPublic)
async def get_user(user_id: int, db: Annotated[AsyncSession, Depends(get_db)]): 
    result = await db.execute(
        select(models.User).where(models.User.id == user_id),
        )
    user = result.scalars().first()
    if user:
        return user
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail = "user not found")

@router.get("/{user_id}/posts", response_model=list[PostResponse])
async def get_user_post(user_id: int, db = Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )    
    result = await db.execute(
        select(models.Post)
        .options(selectinload(models.Post.author))
        .where(models.Post.user_id == user_id)
        .order_by(models.Post.date_posted.desc()),
        )
    posts = result.scalars().all()
    return posts

@router.patch("/{user_id}", response_model=UserPrivate)
async def update_user(
    user_id: int, 
    user_update: UserUpdate,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this post"
        )

    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code= status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )
    
    if user_update.username is not None and user_update.username.lower() != user.username.lower():
        result = await db.execute(
            select(models.User).where(func.lower(models.User.username) == user_update.username.lower()),     
        )
        existing_user = result.scalars().first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists",
            )
    if user_update.email is not None and user_update.email.lower() != user.email.lower():
        result = await db.execute(
            select(models.User).where(func.lower(models.User.email) == user_update.email.lower()),     
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
        user.email = user_update.email.lower()

    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    if user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this post"
        )
    result = await db.execute(select(models.User).where(models.User.id == user_id))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail = "user not found",
        )

    old_filename = user.image_file # doing this in order to delete the file path of the user's profile picture
    await db.delete(user)
    await db.commit()

    if old_filename:
        delete_profile_image(old_filename)

@router.patch("/{user_id}/picture", response_model=UserPrivate)
async def upload_profile_picture(
    user_id: int,
    file: UploadFile, 
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this user's picture",
        )

    content = await file.read()

    if len(content) > settings.max_upload_size_bytes:  # to get the size of the file 
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File too large. Maximum size is {settings.max_upload_size_bytes // (1024 * 1024)}MB",
        )

    try:
        new_filename = await run_in_threadpool(process_profile_image, content)
    except UnidentifiedImageError as err:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid image file. Please upload a valid image (JPEG, PNG, GIF, WebP).",
        ) from err

    old_filename = current_user.image_file

    current_user.image_file = new_filename
    await db.commit()
    await db.refresh(current_user)

    if old_filename:
        delete_profile_image(old_filename)

    return current_user
        

@router.delete("/{user_id}/picture", response_model=UserPrivate)
async def delete_user_picture(
    user_id: int,
    current_user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this user's picture"
        )

    old_filename = current_user.image_file

    if old_filename is None:
        raise HTTPException(
            status_code = status.HTTP_403_FORBIDDEN,
            detail= "No profile picture to delete",
        )

    current_user.image_file = None
    await db.commit()
    await db.refresh(current_user)

    delete_profile_image(old_filename)

    return current_user