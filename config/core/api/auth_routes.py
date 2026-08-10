"""
KisanAI OS
Auth API Routes
Version: 1.0.0

POST /api/auth/register  - create a new user
POST /api/auth/token     - OAuth2 form login, returns JWT
GET  /api/auth/me        - current user details (bearer token required)
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from config.core.api.auth import create_access_token, get_current_user
from config.core.database import get_db
from config.core.models.user import User
from config.core.schemas import Token, UserCreate, UserOut
from config.core.services.user_service import UserService


router = APIRouter(prefix="/api/auth", tags=["auth"])

user_service = UserService()


@router.post("/register", response_model=UserOut)
def register_user(data: UserCreate, db: Session = Depends(get_db)):
    result = UserService(db).register_user(data.model_dump())

    if not result["success"]:
        raise HTTPException(
            status_code=409,
            detail={"success": False, "message": result["message"]},
        )

    return result["data"]


@router.post("/token", response_model=Token)
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    result = UserService(db).authenticate_user(
        form_data.username,
        form_data.password,
    )

    if not result["success"]:
        raise HTTPException(
            status_code=401,
            detail={"success": False, "message": result["message"]},
        )

    user = result["data"]

    access_token = create_access_token(user.username)

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/me", response_model=UserOut)
def read_users_me(
    current_user: User = Depends(get_current_user),
):
    return current_user.to_dict()
