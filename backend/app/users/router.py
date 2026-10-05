from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlmodel import select

from app.auth.dependencies import AdminUser, ManagerUser
from app.core.security import hash_password
from app.db.session import DbSession
from app.users.models import Role, User
from app.users.schemas import UserCreate, UserRead

router = APIRouter(prefix="/users", tags=["Users"])


@router.post("", response_model=UserRead, status_code=201)
def create_user(body: UserCreate, admin: AdminUser, db: DbSession):
    """The company admin adds a colleague to their own company."""
    user = User(
        company_id=admin.company_id,
        email=body.email,
        full_name=body.full_name,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as error:  # the unique index on users.email
        db.rollback()
        raise HTTPException(409, "This email is already registered") from error
    return user


@router.get("", response_model=list[UserRead])
def list_users(manager: ManagerUser, db: DbSession, role: Role | None = None):
    """Admins and hiring managers list company users, for example to pick an interviewer."""
    query = select(User).where(User.company_id == manager.company_id)
    if role is not None:
        query = query.where(User.role == role)
    return db.exec(query.order_by(User.full_name)).all()
