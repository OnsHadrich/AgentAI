from dependency_injector.wiring import Provide, inject
from fastapi import Depends
from jose import jwt
from pydantic import ValidationError

from config import Configs
from core.container import Container
from core.exceptions import AuthError
from core.security import  JWTBearer
from model.user_model import User
from schema.auth_schema import Payload
from services.user_service import UserService
from jose import JWTError

configs = Configs()

@inject
def get_current_user(
    token: str = Depends(JWTBearer()),
    service: UserService = Depends(Provide[Container.user_service]),
) -> User:
    try:
        payload = jwt.decode(token, configs.JWT_SECRET, algorithms=[configs.JWT_ALGORITHM])
        token_data = Payload(**payload)
    except (JWTError, ValidationError):
        raise AuthError(detail="Could not validate credentials")
    current_user: User = service.get_by_id(token_data.id)
    if not current_user:
        raise AuthError(detail="User not found")
    return current_user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise AuthError("Inactive user")
    return current_user


def get_current_user_with_no_exception(
    token: str = Depends(JWTBearer()),
    service: UserService = Depends(Provide[Container.user_service]),
) -> User | None:
    try:
        payload = jwt.decode(token, configs.JWT_SECRET, algorithms=[configs.JWT_ALGORITHM])
        token_data = Payload(**payload)
    except (JWTError, ValidationError):
        return None
    current_user: User | None = service.get_by_id(token_data.id)
    if not current_user:
        return None
    return current_user


def get_current_super_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise AuthError("Inactive user")
    if not current_user.is_superuser:
        raise AuthError("It's not a super user")
    return current_user
