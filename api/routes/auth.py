import json
from fastapi import APIRouter, HTTPException, Depends
from core.container import Container
from core.exceptions import AuthError
from api.auth_handler import blacklist_token, get_current_user
from services.auth_service import AuthService
from sessions.session_manager import SessionManager
from repositories.user_repository import UserRepository
from core.middleware import inject
from dependency_injector.wiring import inject, Provide
from fastapi import APIRouter, Depends, HTTPException
from schema.auth_schema import SignIn, SignInResponse, SignUp, SignOutResponse, SessionInfo
from schema.user_schema import RegisterResponse

router = APIRouter(prefix="/auth", tags=["Auth"])
session_manager = SessionManager()
user_repo = UserRepository()




router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/signin", response_model=SignInResponse)
@inject
def sign_in(
    body: SignIn,
    auth_service: AuthService = Depends(Provide[Container.auth_service]),       # ← Provide not Provider
    session_manager: SessionManager = Depends(Provide[Container.session_manager])  # ← provide the dependency
):
    """Login with email and password — returns JWT token."""
    try:
        result = auth_service.sign_in(body)    # ← auth logic stays in service
    except AuthError as e:
        raise HTTPException(status_code=401, detail=e.detail)

    # create or resume session
    session = session_manager.get_session(result.user_id)
    if session:
        msg = f"Welcome back! Session resumed."
    else:
        session_manager.create_session(
            user_id=result.user_id,
            user_name=result.user_name,
            tier=result.tier
        )
        msg = f"Welcome, {result.user_name}!"

    return SignInResponse(
        access_token=result.access_token,
        token_type="bearer",
        expiration=result.expiration,
        user_id=result.user_id,
        user_name=result.user_name,
        tier=result.tier,  
        message=msg
    )


@router.post("/signup", response_model=RegisterResponse, status_code=201)
@inject
def sign_up(
    body: SignUp,
    auth_service: AuthService = Depends(Provide[Container.auth_service])
):
    """Register a new user."""
    try:
        return auth_service.sign_up(body)
    except AuthError as e:
        raise HTTPException(status_code=400, detail=e.detail)
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))


@router.post("/signout")
@inject
def sign_out(
    current_user: dict = Depends(get_current_user),
    session_manager: SessionManager = Depends(Provide[Container.session_manager])
):
    """Logout — blacklist token and end session."""
    blacklist_token(current_user["token"])
    session_manager.end_session(current_user["user_id"])
    return {"message": f"Logged out successfully."}


@router.get("/me")
@inject
def get_me(
    current_user: dict = Depends(get_current_user),
    session_manager: SessionManager = Depends(Provide[Container.session_manager])
):
    """Get current logged-in user info."""
    session = session_manager.get_session(current_user["user_id"])
    if not session:
        raise HTTPException(status_code=401, detail="Session expired. Please login again.")
    return {
        "user_id": current_user["user_id"],
        "user_name": current_user["user_name"],
        "tier": current_user["tier"],
        "session": {
            "created_at": session.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "last_active": session.last_active.strftime("%Y-%m-%d %H:%M:%S"),
        }
    }