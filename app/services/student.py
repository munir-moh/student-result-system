from datetime import date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException
from app.models.models import User, Student, ClassEnrollment, AcademicYear, Role
from app.schemas.schemas import StudentIn
from app.core.security import hash_password
from app.utils import gen_student_id


async def create_student(db: AsyncSession, data: StudentIn) -> tuple:
    # email must be unique
    exists = await db.execute(select(User).where(User.email == data.email))
    if exists.scalar_one_or_none():
        raise HTTPException(400, "Email already registered")

    # academic year must exist
    yr = await db.execute(select(AcademicYear).where(AcademicYear.id == data.academic_year_id))
    academic_year = yr.scalar_one_or_none()
    if not academic_year:
        raise HTTPException(404, "Academic year not found")

    # generate student ID
    count = (await db.execute(select(func.count()).select_from(Student))).scalar() + 1
    student_id_str = gen_student_id(date.today().year, count)

    # default password = date of birth e.g. 2008-05-14
    default_pw = data.date_of_birth.strftime("%Y-%m-%d")

    user = User(email=data.email, hashed_password=hash_password(default_pw),
                role=Role.STUDENT, must_change_password=True)
    db.add(user)
    await db.flush()

    student = Student(
        user_id=user.id, student_id=student_id_str,
        first_name=data.first_name, last_name=data.last_name,
        middle_name=data.middle_name, gender=data.gender,
        date_of_birth=data.date_of_birth,
    )
    db.add(student)
    await db.flush()

    enrollment = ClassEnrollment(
        student_id=student.id,
        academic_year_id=data.academic_year_id,
        class_level=data.class_level,
        arm=data.arm,
    )
    db.add(enrollment)
    await db.flush()

    return student, user, enrollment
