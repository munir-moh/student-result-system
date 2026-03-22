from datetime import date
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.core.security import hash_password
from app.models.models import User, Admin, Role, Subject, SubjectAssignment, AcademicYear, TermRecord
from app.schemas.schemas import (AdminIn, AdminOut, SubjectIn, SubjectOut,
                                  AcademicYearIn, AcademicYearOut, TermIn, TermOut, Msg)
from app.services.auth import only_admin

router = APIRouter(prefix="/admin", tags=["Admin"])


def gen_admin_id(year: int, count: int) -> str:
    return f"ADM/{year}/{count:04d}"


@router.post("/admins", response_model=AdminOut, status_code=201)
async def create_admin(data: AdminIn, db: AsyncSession = Depends(get_db),
                       _: User = Depends(only_admin)):
    if (await db.execute(select(User).where(User.email == data.email))).scalar_one_or_none():
        raise HTTPException(400, "Email already registered")
    count = (await db.execute(select(func.count()).select_from(Admin))).scalar() + 1
    user  = User(email=data.email, hashed_password=hash_password("Admin@12345"),
                 role=Role.ADMIN, must_change_password=True)
    db.add(user); await db.flush()
    admin = Admin(user_id=user.id, admin_id=gen_admin_id(date.today().year, count),
                  first_name=data.first_name, last_name=data.last_name, phone=data.phone)
    db.add(admin); await db.flush()
    return AdminOut(id=admin.id, admin_id=admin.admin_id, email=user.email,
                    first_name=admin.first_name, last_name=admin.last_name,
                    phone=admin.phone, is_active=user.is_active)


@router.get("/admins", response_model=list[AdminOut])
async def list_admins(db: AsyncSession = Depends(get_db), _: User = Depends(only_admin)):
    rows = (await db.execute(select(Admin, User).join(User, User.id == Admin.user_id))).all()
    return [AdminOut(id=a.id, admin_id=a.admin_id, email=u.email,
                     first_name=a.first_name, last_name=a.last_name,
                     phone=a.phone, is_active=u.is_active) for a, u in rows]


@router.post("/subjects", response_model=SubjectOut, status_code=201)
async def create_subject(data: SubjectIn, db: AsyncSession = Depends(get_db),
                         _: User = Depends(only_admin)):
    if (await db.execute(select(Subject).where(Subject.code == data.code.upper()))).scalar_one_or_none():
        raise HTTPException(400, "Subject code already exists")
    s = Subject(name=data.name, code=data.code.upper())
    db.add(s); await db.flush()
    return s


@router.get("/subjects", response_model=list[SubjectOut])
async def list_subjects(db: AsyncSession = Depends(get_db), _: User = Depends(only_admin)):
    return (await db.execute(select(Subject).where(Subject.is_active == True))).scalars().all()


@router.delete("/subjects/{subject_id}", response_model=Msg)
async def delete_subject(subject_id: int, db: AsyncSession = Depends(get_db),
                         _: User = Depends(only_admin)):
    s = (await db.execute(select(Subject).where(Subject.id == subject_id))).scalar_one_or_none()
    if not s: raise HTTPException(404, "Subject not found")
    s.is_active = False
    return Msg(message="Subject deactivated")


@router.post("/academic-years", response_model=AcademicYearOut, status_code=201)
async def create_year(data: AcademicYearIn, db: AsyncSession = Depends(get_db),
                      _: User = Depends(only_admin)):
    if (await db.execute(select(AcademicYear).where(AcademicYear.name == data.name))).scalar_one_or_none():
        raise HTTPException(400, "Academic year already exists")
    if data.is_current:
        from sqlalchemy import update
        await db.execute(update(AcademicYear).values(is_current=False))
    y = AcademicYear(name=data.name, is_current=data.is_current)
    db.add(y); await db.flush()
    return y


@router.get("/academic-years", response_model=list[AcademicYearOut])
async def list_years(db: AsyncSession = Depends(get_db), _: User = Depends(only_admin)):
    return (await db.execute(select(AcademicYear).order_by(AcademicYear.id.desc()))).scalars().all()


@router.patch("/academic-years/{year_id}/set-current", response_model=AcademicYearOut)
async def set_current_year(year_id: int, db: AsyncSession = Depends(get_db),
                           _: User = Depends(only_admin)):
    from sqlalchemy import update
    await db.execute(update(AcademicYear).values(is_current=False))
    y = (await db.execute(select(AcademicYear).where(AcademicYear.id == year_id))).scalar_one_or_none()
    if not y: raise HTTPException(404, "Academic year not found")
    y.is_current = True
    return y



@router.post("/terms", response_model=TermOut, status_code=201)
async def create_term(data: TermIn, db: AsyncSession = Depends(get_db),
                      _: User = Depends(only_admin)):
    yr = (await db.execute(select(AcademicYear).where(AcademicYear.id == data.academic_year_id))).scalar_one_or_none()
    if not yr: raise HTTPException(404, "Academic year not found")
    dup = (await db.execute(select(TermRecord).where(
        TermRecord.academic_year_id == data.academic_year_id, TermRecord.name == data.name
    ))).scalar_one_or_none()
    if dup: raise HTTPException(400, "Term already exists for this year")
    if data.is_current:
        from sqlalchemy import update
        await db.execute(update(TermRecord).values(is_current=False))
    t = TermRecord(academic_year_id=data.academic_year_id, name=data.name, is_current=data.is_current)
    db.add(t); await db.flush()
    return TermOut(id=t.id, academic_year_id=t.academic_year_id, academic_year_name=yr.name,
                   name=t.name, is_current=t.is_current, result_published=t.result_published,
                   published_at=t.published_at)


@router.get("/terms", response_model=list[TermOut])
async def list_terms(academic_year_id: int | None = None, db: AsyncSession = Depends(get_db),
                     _: User = Depends(only_admin)):
    q = select(TermRecord, AcademicYear).join(AcademicYear)
    if academic_year_id: q = q.where(TermRecord.academic_year_id == academic_year_id)
    rows = (await db.execute(q.order_by(TermRecord.id.desc()))).all()
    return [TermOut(id=t.id, academic_year_id=t.academic_year_id, academic_year_name=yr.name,
                    name=t.name, is_current=t.is_current, result_published=t.result_published,
                    published_at=t.published_at) for t, yr in rows]


@router.patch("/terms/{term_id}/set-current", response_model=Msg)
async def set_current_term(term_id: int, db: AsyncSession = Depends(get_db),
                           _: User = Depends(only_admin)):
    from sqlalchemy import update
    await db.execute(update(TermRecord).values(is_current=False))
    t = (await db.execute(select(TermRecord).where(TermRecord.id == term_id))).scalar_one_or_none()
    if not t: raise HTTPException(404, "Term not found")
    t.is_current = True
    return Msg(message="Current term updated")
