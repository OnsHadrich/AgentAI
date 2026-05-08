from dataclasses import dataclass

@dataclass
class User:
    user_id: str
    name: str
    email: str
    password_hash: str      # ← matches JSON key
    tier: str
    is_active: bool = True
    is_superuser: bool = False