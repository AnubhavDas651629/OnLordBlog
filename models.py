from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base

class User(Base):
    __tablename__ = "users"
    #nullable means that this field is compulsory to fill
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique = True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    #either string or none
    image_file: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
        default = None,
    )
    #creates a one to many relationship, if one user creates many posts it links all the posts to the author via the relationship command to author
    # forward referecning, till now Post is not defined, will define later in this code base 
    posts: Mapped[list[Post]] = relationship(back_populates="author")

    @property
    def image_path(self) -> str:
        if self.image_file:
            return f"/media/profile_pics/{self.image_file}"
        return "/static/profile_pics/default.jpg"

class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable = False, 
        index=True
    )

    date_posted: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC), # lamba called so that after envery entry datetime gets reset and current date and time would be shown
    )

    author: Mapped[User] = relationship(back_populates="posts")


     


