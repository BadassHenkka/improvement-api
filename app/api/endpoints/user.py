from fastapi import APIRouter
from fastapi import Depends

from app.api.dependancies import get_current_active_user
from app.models.user import User

user_router = APIRouter()


@user_router.get("/me", response_model=User)
def current_user(current_user: User = Depends(get_current_active_user)):
    return current_user
