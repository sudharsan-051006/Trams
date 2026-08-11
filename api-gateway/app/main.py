import os

import httpx
import jwt

from fastapi import (
    FastAPI,
    HTTPException,
    Request
)
from fastapi.security import HTTPBearer
from pydantic import BaseModel, EmailStr


app = FastAPI(title="API Gateway")


USER_SERVICE_URL = os.getenv(
    "USER_SERVICE_URL",
    "http://127.0.0.1:8001"
)

JWT_SECRET = os.getenv(
    "JWT_SECRET",
    "development-secret-change-me"
)

ALGORITHM = "HS256"

security = HTTPBearer()


class UserCreate(BaseModel):
    name: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


def verify_token(request: Request):
    authorization = request.headers.get("Authorization")

    if not authorization:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required"
        )

    try:
        scheme, token = authorization.split(" ", 1)

        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication scheme"
            )

        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[ALGORITHM]
        )

        return payload

    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )


@app.get("/")
async def root():
    return {
        "message": "API Gateway is running"
    }


@app.post("/auth/login")
async def login(login_data: LoginRequest):

    try:
        async with httpx.AsyncClient() as client:

            response = await client.post(
                f"{USER_SERVICE_URL}/auth/login",
                json=login_data.model_dump()
            )

        return response.json()

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="User Service is unavailable"
        )


@app.post("/users")
async def create_user(
    user: UserCreate
):
    try:
        async with httpx.AsyncClient() as client:

            response = await client.post(
                f"{USER_SERVICE_URL}/users",
                json=user.model_dump()
            )

        return response.json()

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="User Service is unavailable"
        )


@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    request: Request
):
    verify_token(request)

    try:
        async with httpx.AsyncClient() as client:

            response = await client.get(
                f"{USER_SERVICE_URL}/users/{user_id}"
            )

        return response.json()

    except httpx.RequestError:
        raise HTTPException(
            status_code=503,
            detail="User Service is unavailable"
        )