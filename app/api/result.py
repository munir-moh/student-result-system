from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models.models import User, Teacher, Student, Role, Result, Subject, ClassEnrollment, TermRecord
from app.schemas.schemas import ResultIn, BulkResultIn, AffectiveIn, AffectiveOut, ResultOut, ReportCardOut, Msg
from app.services.auth import only_admin, only_teacher, get_current_user
from app.services.result import save_result, save_bulk, publish, unpublish, get_report_data, save_affective
from app.services.pdf import build_pdf

router = APIRouter(tags=["Results"])


# ── Enter Results (Teacher) ───────────────────────────────────────────────────

@router.post("/results", response_model=ResultOut, status_code=201)
async def enter_result(data: ResultIn, db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(only_teacher)):
    teacher = (await db.execute(select(Teacher).where(Teacher.user_id == current_user.id))).scalar_one_or_none()
    if not teacher: raise HTTPException(404, "Teacher profile not found")

    r = await save_result(db, data, teacher)

    subj = (await db.execute(select(Subject).where(Subject.id == r.subject_id))).scalar_one()
    stu  = (await db.execute(select(Student).where(Student.id == r.student_id))).scalar_one()

    return ResultOut(
        id=r.id, student_id=r.student_id,
        student_name=f"{stu.last_name} {stu.first_name}",
        subject_id=r.subject_id, subject_name=subj.name,
        term_id=r.term_id, ca1=r.ca1, ca2=r.ca2, exam=r.exam,
        total=r.total, grade=r.grade, remark=r.remark, is_pass=r.is_pass,
    )


@router.post("/results/bulk", response_model=Msg, status_code=201)
async def enter_bulk(data: BulkResultIn, db: AsyncSession = Depends(get_db),
                     current_user: User = Depends(only_teacher)):
    teacher = (await db.execute(select(Teacher).where(Teacher.user_id == current_user.id))).scalar_one_or_none()
    if not teacher: raise HTTPException(404, "Teacher profile not found")

    count = await save_bulk(db, data.results, teacher)
    return Msg(message=f"{count} result(s) saved successfully")


# ── Publish / Unpublish (Admin only) ─────────────────────────────────────────

@router.post("/terms/{term_id}/publish", response_model=Msg)
async def publish_results(term_id: int, db: AsyncSession = Depends(get_db),
                          _: User = Depends(only_admin)):
    await publish(db, term_id)
    return Msg(message="Results published. Students can now view their results.")


@router.post("/terms/{term_id}/unpublish", response_model=Msg)
async def unpublish_results(term_id: int, db: AsyncSession = Depends(get_db),
                             _: User = Depends(only_admin)):
    await unpublish(db, term_id)
    return Msg(message="Results unpublished.")


# ── View Results ──────────────────────────────────────────────────────────────

@router.get("/students/{student_id}/results/{term_id}")
async def view_results(student_id: int, term_id: int,
                       db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    # students can only see their own results
    if current_user.role == Role.STUDENT:
        my = (await db.execute(select(Student).where(Student.user_id == current_user.id))).scalar_one_or_none()
        if not my or my.id != student_id:
            raise HTTPException(403, "Access denied")

    check = current_user.role == Role.STUDENT
    rows = await db.execute(
        select(Result, Subject)
        .join(Subject, Subject.id == Result.subject_id)
        .where(Result.student_id == student_id, Result.term_id == term_id)
    )

    if check:
        term = (await db.execute(select(TermRecord).where(TermRecord.id == term_id))).scalar_one_or_none()
        if not term or not term.result_published:
            raise HTTPException(403, "Results not yet published")

    return [
        {"subject": s.name, "ca1": r.ca1, "ca2": r.ca2, "exam": r.exam,
         "total": r.total, "grade": r.grade, "remark": r.remark, "is_pass": r.is_pass}
        for r, s in rows.all()
    ]


# ── Report Card (JSON) ────────────────────────────────────────────────────────

@router.get("/students/{student_id}/report-card/{term_id}", response_model=ReportCardOut)
async def report_card(student_id: int, term_id: int,
                      db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    if current_user.role == Role.STUDENT:
        my = (await db.execute(select(Student).where(Student.user_id == current_user.id))).scalar_one_or_none()
        if not my or my.id != student_id:
            raise HTTPException(403, "Access denied")

    check = current_user.role == Role.STUDENT
    data  = await get_report_data(db, student_id, term_id, check_published=check)
    return data


# ── Report Card PDF Download ──────────────────────────────────────────────────

@router.get("/students/{student_id}/report-card/{term_id}/pdf")
async def report_card_pdf(student_id: int, term_id: int,
                          db: AsyncSession = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    if current_user.role == Role.STUDENT:
        my = (await db.execute(select(Student).where(Student.user_id == current_user.id))).scalar_one_or_none()
        if not my or my.id != student_id:
            raise HTTPException(403, "Access denied")

    check = current_user.role == Role.STUDENT
    data  = await get_report_data(db, student_id, term_id, check_published=check)
    pdf   = build_pdf(data)

    filename = f"report_{data['student_id']}_{data['term']}_{data['academic_year'].replace('/', '-')}.pdf"
    return Response(content=pdf, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename={filename}"})


# ── Affective Domain ──────────────────────────────────────────────────────────

@router.post("/affective", response_model=AffectiveOut, status_code=201)
async def enter_affective(data: AffectiveIn, db: AsyncSession = Depends(get_db),
                          _: User = Depends(only_teacher)):
    record = await save_affective(db, data)
    return record


# ── Analytics ─────────────────────────────────────────────────────────────────

@router.get("/analytics")
async def analytics(academic_year_id: int, class_level: str, term_id: int,
                    db: AsyncSession = Depends(get_db),
                    _: User = Depends(only_teacher)):
    # students in this class/year
    enrollment_rows = (await db.execute(
        select(ClassEnrollment.student_id).where(
            ClassEnrollment.academic_year_id == academic_year_id,
            ClassEnrollment.class_level == class_level,
        )
    )).all()
    student_ids = [r[0] for r in enrollment_rows]
    if not student_ids:
        return {"message": "No students found", "total_students": 0}

    # unique subjects for this term + class
    subject_rows = (await db.execute(
        select(Subject).join(Result, Result.subject_id == Subject.id)
        .where(Result.term_id == term_id, Result.student_id.in_(student_ids))
        .distinct()
    )).scalars().all()

    subject_stats = []
    for subj in subject_rows:
        stats = (await db.execute(
            select(
                func.count(Result.id),
                func.sum(Result.is_pass.cast("int")),
                func.avg(Result.total),
                func.max(Result.total),
                func.min(Result.total),
            ).where(
                Result.subject_id == subj.id,
                Result.term_id == term_id,
                Result.student_id.in_(student_ids),
                Result.total.isnot(None),
            )
        )).one()
        count, passed, avg, highest, lowest = stats
        passed = passed or 0
        subject_stats.append({
            "subject":       subj.name,
            "total_students":count or 0,
            "passed":        passed,
            "failed":        (count or 0) - passed,
            "pass_rate":     round(passed / count * 100, 1) if count else 0,
            "average":       round(float(avg or 0), 2),
            "highest":       float(highest or 0),
            "lowest":        float(lowest or 0),
        })

    # overall class average
    all_avgs = [s["average"] for s in subject_stats]
    class_avg = round(sum(all_avgs) / len(all_avgs), 2) if all_avgs else 0

    return {
        "class_level":    class_level,
        "term_id":        term_id,
        "total_students": len(student_ids),
        "class_average":  class_avg,
        "subjects":       subject_stats,
    }
