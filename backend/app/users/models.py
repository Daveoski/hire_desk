import uuid
from enum import StrEnum

from sqlmodel import Field, SQLModel

from app.db.common import enum_column


class Role(StrEnum):
    company_admin = "company_admin"
    hiring_manager = "hiring_manager"
    interviewer = "interviewer"


class User(SQLModel, table=True):
    __tablename__ = "users"

    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    company_id: uuid.UUID = Field(foreign_key="companies.id")
    # The unique index on email is also what makes the login lookup fast.
    email: str = Field(unique=True, index=True)
    full_name: str
    hashed_password: str
    role: Role = Field(sa_type=enum_column(Role))
