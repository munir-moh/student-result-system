from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.models import User, Student, ClassEnrollment, Role
from app.schemas.schemas import StudentIn, StudentOut, StudentListOut, Msg
from app.services.auth import only_admin, get_current_user
from app.services.student import create_student

router = APIRouter(prefix="/students", tags=["Students"])


@router.post("", response_model=StudentOut, status_code=201)
async def register_student(data: StudentIn, db: AsyncSession = Depends(get_db),
                            _: User = Depends(only_admin)):
    student, user, enrollment = await create_student(db, data)
    return StudentOut(
        id=student.id, student_id=student.student_id, email=user.email,
        first_name=student.first_name, last_name=student.last_name,
        middle_name=student.middle_name, gender=student.gender,
        date_of_birth=student.date_of_birth, date_admitted=student.date_admitted,
        is_active=student.is_active,
        current_class=f"{enrollment.class_level.value} {enrollment.arm or ''}".strip(),
    )


@router.get("", response_model=list[StudentListOut])
async def list_students(
    academic_year_id: int | None = None,
    class_level: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(only_admin),
):
    offset = (page - 1) * per_page
    q = (select(Student, ClassEnrollment)
         .outerjoin(ClassEnrollment, ClassEnrollment.student_id == Student.id)
         .where(Student.is_active == True))
    if academic_year_id: q = q.where(ClassEnrollment.academic_year_id == academic_year_id)
    if class_level:      q = q.where(ClassEnrollment.class_level == class_level)
    rows = (await db.execute(q.offset(offset).limit(per_page))).all()
    return [StudentListOut(
        id=s.id, student_id=s.student_id,
        first_name=s.first_name, last_name=s.last_name, gender=s.gender,
        class_level=e.class_level.value if e else None,
        arm=e.arm if e else None, is_active=s.is_active,
    ) for s, e in rows]


@router.get("/{student_id}", response_model=StudentOut)
async def get_student(student_id: int, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    if current_user.role == Role.STUDENT:
        my = (await db.execute(select(Student).where(Student.user_id == current_user.id))).scalar_one_or_none()
        if not my or my.id != student_id:
            raise HTTPException(403, "Access denied")

    row = (await db.execute(
        select(Student, User, ClassEnrollment)
        .join(User, User.id == Student.user_id)
        .outerjoin(ClassEnrollment, ClassEnrollment.student_id == Student.id)
        .where(Student.id == student_id)
    )).first()
    if not row: raise HTTPException(404, "Student not found")
    s, u, e = row
    return StudentOut(
        id=s.id, student_id=s.student_id, email=u.email,
        first_name=s.first_name, last_name=s.last_name,
        middle_name=s.middle_name, gender=s.gender,
        date_of_birth=s.date_of_birth, date_admitted=s.date_admitted,
        is_active=s.is_active,
        current_class=f"{e.class_level.value} {e.arm or ''}".strip() if e else None,
    )


@router.delete("/{student_id}", response_model=Msg)
async def deactivate_student(student_id: int, db: AsyncSession = Depends(get_db),
                              _: User = Depends(only_admin)):
    s = (await db.execute(select(Student).where(Student.id == student_id))).scalar_one_or_none()
    if not s: raise HTTPException(404, "Student not found")
    s.is_active = False
    u = (await db.execute(select(User).where(User.id == s.user_id))).scalar_one_or_none()
    if u: u.is_active = False
    return Msg(message="Student deactivated")
