from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from fastapi import HTTPException
from app.models.models import (
    Result, TermRecord, Student, Subject,
    SubjectAssignment, Teacher, ClassEnrollment, AffectiveDomain, AcademicYear
)
from app.schemas.schemas import ResultIn, AffectiveIn
from app.core.grading import get_grade, validate_scores, get_comment, AFFECTIVE_LABELS
from typing import List


def ordinal(n: int) -> str:
    suffix = {1:"st",2:"nd",3:"rd"}.get(n if n < 20 else n % 10, "th")
    return f"{n}{suffix}"


async def save_result(db: AsyncSession, data: ResultIn, teacher: Teacher) -> Result:
    # teacher must be assigned to this subject
    assigned = (await db.execute(select(SubjectAssignment).where(
        SubjectAssignment.teacher_id == teacher.id,
        SubjectAssignment.subject_id == data.subject_id,
    ))).scalar_one_or_none()
    if not assigned:
        raise HTTPException(403, "You are not assigned to this subject")

    # term must exist and not be published
    term = (await db.execute(select(TermRecord).where(TermRecord.id == data.term_id))).scalar_one_or_none()
    if not term: raise HTTPException(404, "Term not found")
    if term.result_published:
        raise HTTPException(400, "Results already published. Ask admin to unpublish first.")

    errors = validate_scores(data.ca1, data.ca2, data.exam)
    if errors: raise HTTPException(422, "; ".join(errors))

    total = round(data.ca1 + data.ca2 + data.exam, 2)
    grade, remark, is_pass = get_grade(total)

    # upsert
    existing = (await db.execute(select(Result).where(
        Result.student_id == data.student_id,
        Result.subject_id == data.subject_id,
        Result.term_id    == data.term_id,
    ))).scalar_one_or_none()

    if existing:
        existing.ca1=data.ca1; existing.ca2=data.ca2; existing.exam=data.exam
        existing.total=total; existing.grade=grade; existing.remark=remark
        existing.is_pass=is_pass; existing.entered_by=teacher.id
        return existing

    r = Result(
        student_id=data.student_id, subject_id=data.subject_id,
        term_id=data.term_id, entered_by=teacher.id,
        ca1=data.ca1, ca2=data.ca2, exam=data.exam,
        total=total, grade=grade, remark=remark, is_pass=is_pass,
    )
    db.add(r)
    await db.flush()
    return r


async def save_bulk(db: AsyncSession, items: List[ResultIn], teacher: Teacher) -> int:
    for item in items:
        await save_result(db, item, teacher)
    return len(items)


async def publish(db: AsyncSession, term_id: int):
    term = (await db.execute(select(TermRecord).where(TermRecord.id == term_id))).scalar_one_or_none()
    if not term: raise HTTPException(404, "Term not found")
    if term.result_published: raise HTTPException(400, "Already published")
    term.result_published = True
    term.published_at = datetime.now(timezone.utc)


async def unpublish(db: AsyncSession, term_id: int):
    term = (await db.execute(select(TermRecord).where(TermRecord.id == term_id))).scalar_one_or_none()
    if not term: raise HTTPException(404, "Term not found")
    term.result_published = False
    term.published_at = None


async def get_report_data(db: AsyncSession, student_id: int, term_id: int, check_published: bool = False) -> dict:
    term = (await db.execute(select(TermRecord).where(TermRecord.id == term_id))).scalar_one_or_none()
    if not term: raise HTTPException(404, "Term not found")
    if check_published and not term.result_published:
        raise HTTPException(403, "Results not yet published")

    student = (await db.execute(select(Student).where(Student.id == student_id))).scalar_one_or_none()
    if not student: raise HTTPException(404, "Student not found")

    enrollment = (await db.execute(select(ClassEnrollment).where(
        ClassEnrollment.student_id == student_id,
        ClassEnrollment.academic_year_id == term.academic_year_id,
    ))).scalar_one_or_none()

    year_obj = (await db.execute(select(AcademicYear).where(AcademicYear.id == term.academic_year_id))).scalar_one_or_none()

    # results for this student/term
    rows = (await db.execute(
        select(Result, Subject)
        .join(Subject, Subject.id == Result.subject_id)
        .where(Result.student_id == student_id, Result.term_id == term_id)
    )).all()

    subjects = []
    grand_total = 0.0
    for r, s in rows:
        subjects.append({"subject_name": s.name, "ca1": r.ca1, "ca2": r.ca2,
                         "exam": r.exam, "total": r.total, "grade": r.grade,
                         "remark": r.remark, "is_pass": r.is_pass})
        grand_total += r.total or 0

    average = round(grand_total / len(subjects), 2) if subjects else 0

    # class position
    class_level = enrollment.class_level if enrollment else None
    position_str = "N/A"
    class_size = 0
    if class_level:
        classmate_ids = [row[0] for row in (await db.execute(
            select(ClassEnrollment.student_id).where(
                ClassEnrollment.academic_year_id == term.academic_year_id,
                ClassEnrollment.class_level == class_level,
            )
        )).all()]
        class_size = len(classmate_ids)

        averages = []
        for cid in classmate_ids:
            avg = (await db.execute(
                select(func.avg(Result.total)).where(
                    Result.student_id == cid, Result.term_id == term_id, Result.total.isnot(None)
                )
            )).scalar() or 0
            averages.append((cid, float(avg)))

        averages.sort(key=lambda x: x[1], reverse=True)
        for pos, (cid, _) in enumerate(averages, 1):
            if cid == student_id:
                position_str = ordinal(pos)
                break

    affective = (await db.execute(select(AffectiveDomain).where(
        AffectiveDomain.student_id == student_id, AffectiveDomain.term_id == term_id
    ))).scalar_one_or_none()

    return {
        "student_id":    student.student_id,
        "student_name":  f"{student.last_name} {student.first_name} {student.middle_name or ''}".strip(),
        "class_level":   class_level.value if class_level else "N/A",
        "arm":           enrollment.arm if enrollment else None,
        "academic_year": year_obj.name if year_obj else "N/A",
        "term":          term.name.value,
        "gender":        student.gender.value,
        "date_of_birth": student.date_of_birth,
        "total_score":   round(grand_total, 2),
        "average":       average,
        "position":      position_str,
        "class_size":    class_size,
        "subjects":      subjects,
        "affective":     affective,
        "comment":       get_comment(average),
    }


async def save_affective(db: AsyncSession, data: AffectiveIn) -> AffectiveDomain:
    existing = (await db.execute(select(AffectiveDomain).where(
        AffectiveDomain.student_id == data.student_id,
        AffectiveDomain.term_id    == data.term_id,
    ))).scalar_one_or_none()

    fields = data.model_dump(exclude={"student_id", "term_id"})
    if existing:
        for k, v in fields.items():
            if v is not None: setattr(existing, k, v)
        return existing

    record = AffectiveDomain(student_id=data.student_id, term_id=data.term_id, **fields)
    db.add(record)
    await db.flush()
    return record
