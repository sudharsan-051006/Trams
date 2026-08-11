import os
import jwt

from pwdlib import PasswordHash


password_hash = PasswordHash.recommended()

JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "development-secret-change-me"
)

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    password: str,
    hashed_password: str
) -> bool:
    return password_hash.verify(
        password,
        hashed_password
    )


def create_access_token(user_id: int) -> str:
    payload = {
        "sub": str(user_id)
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=ALGORITHM
    )