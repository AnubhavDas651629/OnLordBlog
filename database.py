from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./blog.db"

#engine is the connection to the database, 
#connect_args={"check_same_thread": False} this is specifc for sql lite only, and not needed to postgress or mysql
engine = create_engine(SQLALCHEMY_DATABASE_URL  , connect_args={"check_same_thread": False},)

sessionLocal = sessionmaker(autocommit = False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    with sessionLocal() as db:
        yield db

