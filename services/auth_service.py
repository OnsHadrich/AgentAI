import bcrypt
from model.user_model import User
from repositories.user_repository import UserRepository
from schema.auth_schema import SignIn, SignUp, SignInResponse, Payload
from core.security import create_access_token
from core.exceptions import AuthError
from core.config import Configs
from datetime import timedelta
from utils.hash import get_rand_hash
from typing import Tuple

from schema.user_schema import RegisterResponse

configs = Configs()

class AuthService:
    def __init__(self, user_repository: UserRepository | None = None):
        self.user_repository = user_repository or UserRepository()

    def sign_in(self, sign_in_info: SignIn) -> Tuple[SignInResponse, User]:
        user = self.user_repository.find_by_email(sign_in_info.email)

        if not user:
            raise AuthError(detail="Incorrect email or password")
        if not user.is_active:
            raise AuthError(detail="Account is not active")
        if not bcrypt.checkpw(
            sign_in_info.password.encode(),
            user.password_hash.encode()     # ← password_hash, not password
        ):
            raise AuthError(detail="Incorrect email or password")

        payload = Payload(
            id=user.user_id,               
            email=user.email,
            name=user.name,
            tier=user.tier,
            is_superuser=user.is_superuser,
        )
        token_lifespan = timedelta(minutes=configs.JWT_EXPIRE_MINUTES)
        access_token, expiration = create_access_token(payload.model_dump(), token_lifespan)

        return SignInResponse(
            access_token=access_token,
            token_type="bearer",
            expiration=expiration,
            user_id=user.user_id,
            user_name=user.name,
            tier=user.tier,
            message="Login successful",
        ), user
        
    def sign_up(self, sign_up_info: SignUp) -> RegisterResponse:
        try:
            existing_user = self.user_repository.find_by_email(sign_up_info.email)
            if existing_user:
                raise AuthError(detail=f"User with email {sign_up_info.email} already exists.")
            
            new_user = User(
                user_id=get_rand_hash(),
                name=sign_up_info.name,
                email=sign_up_info.email,
                password_hash=bcrypt.hashpw(sign_up_info.password.encode(), bcrypt.gensalt()).decode(),
                tier=sign_up_info.tier,
                is_active=True,
                is_superuser=False
            
            )
            
            created_user = self.user_repository.create_user(new_user)
            
            return RegisterResponse(
                user_id=created_user.user_id,
                user_name=created_user.name,
                email=created_user.email,
                tier=created_user.tier,
                message="User registered successfully."
            )
        except ValueError as e:
            raise AuthError(detail=str(e))
