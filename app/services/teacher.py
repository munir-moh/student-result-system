from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException
from app.models.models import User, Teacher, Subject, SubjectAssignment, Role
from app.schemas.schemas import TeacherIn
from app.core.security import hash_password
from app.utils import gen_staff_id


async def create_teacher(db: AsyncSession, data: TeacherIn) -> tuple:
    exists = await db.execute(select(User).where(User.email == data.email))
    if exists.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")

    count = (await db.execute(select(func.count()).select_from(Teacher))).scalar() + 1
    staff_id_str = gen_staff_id(date.today().year, count)

    user = User(email=data.email, hashed_password=hash_password("teacher123"),
                role=Role.TEACHER, must_change_password=True)
    db.add(user)
    await db.flush()

    teacher = Teacher(
        user_id=user.id, staff_id=staff_id_str,
        first_name=data.first_name, last_name=data.last_name,
        phone=data.phone, gender=data.gender,
    )
    db.add(teacher)
    await db.flush()
    return teacher, user


async def assign_subject(db: AsyncSession, teacher_id: int, subject_id: int):
    t = (await db.execute(select(Teacher).where(Teacher.id == teacher_id))).scalar_one_or_none()
    if not t: raise HTTPException(404, "Teacher not found")

    s = (await db.execute(select(Subject).where(Subject.id == subject_id))).scalar_one_or_none()
    if not s: raise HTTPException(404, "Subject not found")

    dup = (await db.execute(select(SubjectAssignment).where(
        SubjectAssignment.teacher_id == teacher_id,
        SubjectAssignment.subject_id == subject_id,
    ))).scalar_one_or_none()
    if dup: raise HTTPException(400, "Subject already assigned to this teacher")

    a = SubjectAssignment(teacher_id=teacher_id, subject_id=subject_id)
    db.add(a)
    await db.flush()
