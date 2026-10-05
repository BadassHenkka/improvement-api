from datetime import timedelta

from fastapi import APIRouter
from fastapi import Depends
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.api.utils import authenticate
from app.api.utils import user_token_sub
from app.core.config import settings
from app.core.security import create_access_token
from app.crud.user import create_user
from app.crud.user import get_user_by_username
from app.models.token import Token

auth_router = APIRouter()


@auth_router.post("/register", response_model=Token)
async def register(form_data: OAuth2PasswordRequestForm = Depends()):
    user_exists = await get_user_by_username(form_data.username)

    if user_exists:
        raise HTTPException(status_code=400, detail="This username is already taken.")

    if len(form_data.username) < 3:
        raise HTTPException(status_code=400, detail="The username needs to be at least 3 characters.")

    if len(form_data.password) < 6:
        raise HTTPException(status_code=400, detail="The password length needs to be at least 6 characters.")

    new_user = await create_user(form_data)

    access_token = create_access_token(
        data={"sub": user_token_sub(new_user)}, expires_delta=timedelta(settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )

    return {"access_token": access_token, "token_type": "bearer"}


@auth_router.post("/access-token", response_model=Token)
async def access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    user = await authenticate(form_data.username, form_data.password)

    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    elif not user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")

    access_token = create_access_token(
        data={"sub": user_token_sub(user)},
        expires_delta=timedelta(settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )

    return {"access_token": access_token, "token_type": "bearer"}
