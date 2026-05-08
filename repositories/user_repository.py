import json
from typing import cast
from model.user_model import User
from sessions.session_manager import SessionManager
from fastapi import APIRouter, HTTPException, Depends

with open("data/users.json") as f:
    USERS = json.load(f)
session_manager = SessionManager()

class UserRepository:
    def __init__(self):
        self._users = USERS
        self.session_manager = session_manager
    

    def find_by_email(self, email: str) -> User | None:
        return next(
            (u for u in self._users if u.email.lower() == email.lower()),
            None
        )

    
    def find_by_id(self, user_id: str) -> User | None:
        return next(
            (u for u in self._users if u.user_id == user_id),
            None
        )
        
    def create_user(self, name: str, email: str, password: str, tier: str="free") -> User:
        if self.find_by_email(email):
            raise ValueError(f"User with email {email} already exists.")
        user_id = f"u{len(self._users)+1}"
        password_hash = self.session_manager.hash_password(password)
        new_user = User(
            user_id=user_id,
            name=name,
            email=email,
            password_hash=password_hash.decode(),  # store as string
            tier=tier
        )
        self._users.append(new_user)
        with open("data/users.json", "w") as f:
            json.dump(self._users, f, indent=2)
        return new_user