import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from model.user_model import User
from sessions.session_manager import SessionManager

session_manager = SessionManager()


class UserRepository:
    def __init__(self, filepath: str | Path = "data/users.json"):
        self.filepath = Path(filepath)
        self._users = self._load_users()
        self.session_manager = session_manager

    def _load_users(self) -> list[User]:
        with open(self.filepath) as f:
            users = json.load(f)
        return [User(**user) for user in users]

    def _save_users(self) -> None:
        with open(self.filepath, "w") as f:
            json.dump([asdict(user) for user in self._users], f, indent=2)

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

    def create_user(self, user: User, tier: str = "free") -> User:
        if self.find_by_email(user.email):
            raise ValueError(f"User with email {user.email} already exists.")
        new_user = User(
            user_id=user.user_id or f"u{len(self._users)+1}",
            name=user.name,
            email=user.email,
            password=user.password,  # ← for creation only, not stored
            password_hash=user.password_hash,
            tier=tier,
            is_active=user.is_active,
            is_superuser=user.is_superuser,
        )
        self._users.append(new_user)
        self._save_users()
        return new_user

    def read_by_options(self, schema: Any) -> list[User]:
        if schema is None:
            return self._users
        filters = schema if isinstance(schema, dict) else vars(schema)
        return [
            user for user in self._users
            if all(getattr(user, key, None) == value for key, value in filters.items() if value is not None)
        ]

    def read_by_id(self, id: str) -> User | None:
        return self.find_by_id(id)

    def create(self, schema: User) -> User:
        return self.create_user(schema)

    def update(self, id: str, schema: Any) -> User | None:
        user = self.find_by_id(id)
        if not user:
            return None
        updates = schema if isinstance(schema, dict) else vars(schema)
        for key, value in updates.items():
            if hasattr(user, key) and value is not None:
                setattr(user, key, value)
        self._save_users()
        return user

    def update_attr(self, id: str, attr: str, value: Any) -> User | None:
        user = self.find_by_id(id)
        if not user or not hasattr(user, attr):
            return None
        setattr(user, attr, value)
        self._save_users()
        return user

    def whole_update(self, id: str, schema: User) -> User | None:
        existing_user = self.find_by_id(id)
        if not existing_user:
            return None
        index = self._users.index(existing_user)
        self._users[index] = schema
        self._save_users()
        return schema

    def delete_by_id(self, id: str) -> User | None:
        user = self.find_by_id(id)
        if not user:
            return None
        self._users.remove(user)
        self._save_users()
        return user

    def close_scoped_session(self) -> None:
        pass
    
    def _build_whatsapp_user(self, phone_number: str):
        """
        Build a guest User object for WhatsApp users.
        Phone number is used as user_id since they're not in DB.
        """
        from model.user_model import User

        # clean phone number → use as ID
        # e.g. "21698765432" or "whatsapp:+21698765432"
        clean_number = (
            phone_number
            .replace("whatsapp:", "")
            .replace("+", "")
            .strip()
        )

        return User(
            user_id=clean_number,
            name=f"WhatsApp User",          # ← no name available yet
            email=f"{clean_number}@whatsapp.com",
            tier="standard",                # ← default tier
            is_active=True,
            is_superuser=False,
            password="",
            password_hash=""
        )