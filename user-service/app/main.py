import json

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import User
from .schemas import (
    UserCreate,
    UserResponse,
    LoginRequest,
    TokenResponse
)
from .messaging import connect_nats
from .auth import (
    hash_password,
    verify_password,
    create_access_token
)


app = FastAPI(title="User Service")

Base.metadata.create_all(bind=engine)

nc = None
js = None


@app.on_event("startup")
async def startup_event():
    global nc, js
    nc, js = await connect_nats()


@app.on_event("shutdown")
async def shutdown_event():
    if nc:
        await nc.close()


@app.get("/")
def root():
    return {
        "message": "User Service is running"
    }


@app.post("/users", response_model=UserResponse)
async def create_user(
    user: UserCreate,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=409,
            detail="User already exists"
        )

    new_user = User(
        name=user.name,
        email=user.email,
        password_hash=hash_password(user.password)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    event = {
        "event": "user.created",
        "user_id": new_user.id,
        "name": new_user.name,
        "email": new_user.email
    }

    await js.publish(
        "user.created",
        json.dumps(event).encode()
    )

    return new_user


@app.post("/auth/login", response_model=TokenResponse)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.email == login_data.email
    ).first()

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if not verify_password(
        login_data.password,
        user.password_hash
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token(user.id)

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.id == user_id
    ).first()

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    return user