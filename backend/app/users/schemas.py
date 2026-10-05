import uuid
from typing import Annotated

from pydantic import AfterValidator, BaseModel, ConfigDict, EmailStr, Field

from app.users.models import Role

# Emails are stored in lowercase so "Ann@x.com" and "ann@x.com" are the same person.
LowerEmail = Annotated[EmailStr, AfterValidator(lambda email: email.lower())]


class UserCreate(BaseModel):
    email: LowerEmail
    full_name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)
    role: Role


class UserRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    company_id: uuid.UUID
    email: str
    full_name: str
    role: Role
