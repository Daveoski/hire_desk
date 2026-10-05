from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.auth.dependencies import CurrentUser
from app.auth.schemas import RegisterRequest, Token
from app.companies.models import Company
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import DbSession
from app.users.models import Role, User
from app.users.schemas import UserRead

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserRead, status_code=201)
def register(body: RegisterRequest, db: DbSession):
    company = Company(name=body.company_name)
    db.add(company)
    db.flush()  # insert the company first, because the user row points to it

    user = User(
        company_id=company.id,
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        role=Role.company_admin,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:  # the unique index on users.email
        db.rollback()
        raise HTTPException(409, "This email is already registered") from error
    return user


@router.post("/login", response_model=Token)
def login(form: Annotated[OAuth2PasswordRequestForm, Depends()], db: DbSession):
    # OAuth2PasswordRequestForm names the email field "username".
    user = db.exec(select(User).where(User.email == form.username.lower())).first()
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(401, "Incorrect email or password", headers={"WWW-Authenticate": "Bearer"})
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserRead)
def read_current_user(user: CurrentUser):
    return user
