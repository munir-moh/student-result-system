from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.models import User, Teacher, Subject, SubjectAssignment
from app.schemas.schemas import TeacherIn, TeacherOut, AssignSubjectIn, Msg
from app.services.auth import only_admin, get_current_user
from app.services.teacher import create_teacher, assign_subject

router = APIRouter(prefix="/teachers", tags=["Teachers"])


@router.post("", response_model=TeacherOut, status_code=201)
async def register_teacher(data: TeacherIn, db: AsyncSession = Depends(get_db),
                            _: User = Depends(only_admin)):
    teacher, user = await create_teacher(db, data)
    return TeacherOut(id=teacher.id, staff_id=teacher.staff_id, email=user.email,
                      first_name=teacher.first_name, last_name=teacher.last_name,
                      phone=teacher.phone, gender=teacher.gender,
                      date_joined=teacher.date_joined, is_active=teacher.is_active)


@router.get("", response_model=list[TeacherOut])
async def list_teachers(db: AsyncSession = Depends(get_db), _: User = Depends(only_admin)):
    rows = (await db.execute(
        select(Teacher, User).join(User, User.id == Teacher.user_id).where(Teacher.is_active == True)
    )).all()
    return [TeacherOut(id=t.id, staff_id=t.staff_id, email=u.email,
                       first_name=t.first_name, last_name=t.last_name,
                       phone=t.phone, gender=t.gender,
                       date_joined=t.date_joined, is_active=t.is_active) for t, u in rows]


@router.get("/{teacher_id}", response_model=TeacherOut)
async def get_teacher(teacher_id: int, db: AsyncSession = Depends(get_db),
                      _: User = Depends(only_admin)):
    row = (await db.execute(
        select(Teacher, User).join(User, User.id == Teacher.user_id).where(Teacher.id == teacher_id)
    )).one_or_none()
    if not row: raise HTTPException(404, "Teacher not found")
    t, u = row
    return TeacherOut(id=t.id, staff_id=t.staff_id, email=u.email,
                      first_name=t.first_name, last_name=t.last_name,
                      phone=t.phone, gender=t.gender,
                      date_joined=t.date_joined, is_active=t.is_active)


@router.post("/assign-subject", response_model=Msg, status_code=201)
async def assign(data: AssignSubjectIn, db: AsyncSession = Depends(get_db),
                 _: User = Depends(only_admin)):
    await assign_subject(db, data.teacher_id, data.subject_id)
    return Msg(message="Subject assigned successfully")


@router.delete("/unassign-subject", response_model=Msg)
async def unassign(data: AssignSubjectIn, db: AsyncSession = Depends(get_db),
                   _: User = Depends(only_admin)):
    row = (await db.execute(select(SubjectAssignment).where(
        SubjectAssignment.teacher_id == data.teacher_id,
        SubjectAssignment.subject_id == data.subject_id,
    ))).scalar_one_or_none()
    if not row: raise HTTPException(404, "Assignment not found")
    await db.delete(row)
    return Msg(message="Subject unassigned successfully")


@router.get("/{teacher_id}/subjects")
async def my_subjects(teacher_id: int, db: AsyncSession = Depends(get_db),
                      _: User = Depends(get_current_user)):
    rows = (await db.execute(
        select(Subject).join(SubjectAssignment, SubjectAssignment.subject_id == Subject.id)
        .where(SubjectAssignment.teacher_id == teacher_id)
    )).scalars().all()
    return [{"id": s.id, "name": s.name, "code": s.code} for s in rows]
