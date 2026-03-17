from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import create_token, verify_password, hash_password, decode_token
from app.models.models import User
from app.schemas.schemas import LoginIn, TokenOut, ChangePasswordIn, Msg
from app.services.auth import login_user, get_current_user

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/login", response_model=TokenOut)
async def login(data: LoginIn, db: AsyncSession = Depends(get_db)):
    user = await login_user(data.email, data.password, db)
    return TokenOut(
        access_token=create_token(user.id, "access"),
        refresh_token=create_token(user.id, "refresh"),
        role=user.role,
        must_change_password=user.must_change_password,
    )


@router.post("/refresh", response_model=TokenOut)
async def refresh(refresh_token: str, db: AsyncSession = Depends(get_db)):
    from fastapi import HTTPException
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(401, "Invalid refresh token")
    result = await db.execute(select(User).where(User.id == int(payload["sub"])))
    user = result.scalar_one_or_none()
    if not user: raise HTTPException(401, "User not found")
    return TokenOut(
        access_token=create_token(user.id, "access"),
        refresh_token=create_token(user.id, "refresh"),
        role=user.role,
        must_change_password=user.must_change_password,
    )


@router.post("/change-password", response_model=Msg)
async def change_password(data: ChangePasswordIn, db: AsyncSession = Depends(get_db),
                          user: User = Depends(get_current_user)):
    from fastapi import HTTPException
    if not verify_password(data.old_password, user.hashed_password):
        raise HTTPException(400, "Old password is incorrect")
    user.hashed_password = hash_password(data.new_password)
    user.must_change_password = False
    return Msg(message="Password changed successfully")


@router.get("/me")
async def me(user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    profile = None
    if user.role.value == "student":
        await db.refresh(user, ["student"])
        p = user.student
        if p: profile = {"student_id": p.student_id, "name": f"{p.first_name} {p.last_name}"}
    elif user.role.value == "teacher":
        await db.refresh(user, ["teacher"])
        p = user.teacher
        if p: profile = {"staff_id": p.staff_id, "name": f"{p.first_name} {p.last_name}"}
    elif user.role.value == "admin":
        await db.refresh(user, ["admin"])
        p = user.admin
        if p: profile = {"admin_id": p.admin_id, "name": f"{p.first_name} {p.last_name}"}
    return {"id": user.id, "email": user.email, "role": user.role,
            "must_change_password": user.must_change_password, "profile": profile}
