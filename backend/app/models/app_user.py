from sqlalchemy import BigInteger, Column, Table

from app.db.base import Base

app_users_table = Table(
    "app_users",
    Base.metadata,
    Column("id", BigInteger, primary_key=True),
)