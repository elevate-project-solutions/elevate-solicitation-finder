from sqlalchemy.orm import DeclarativeBase


#Creates common parent class for SQLAlchemy models
class Base(DeclarativeBase):
    pass