from __future__ import annotations
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field
from app.models.models import Role, Term, ClassLevel, Gender


class Msg(BaseModel):
    message: str

# ── Auth ──────────────────────────────────────────────────────────────────────

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    role: Role
    must_change_password: bool

class ChangePasswordIn(BaseModel):
    old_password: str
    new_password: str = Field(min_length=6)

# ── Admin ─────────────────────────────────────────────────────────────────────

class AdminIn(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None

class AdminOut(BaseModel):
    id: int
    admin_id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    is_active: bool
    class Config:
        from_attributes = True

# ── Teacher ───────────────────────────────────────────────────────────────────

class TeacherIn(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    gender: Optional[Gender] = None

class TeacherOut(BaseModel):
    id: int
    staff_id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str]
    gender: Optional[Gender]
    date_joined: date
    is_active: bool
    class Config:
        from_attributes = True

class AssignSubjectIn(BaseModel):
    teacher_id: int
    subject_id: int

# ── Subject ───────────────────────────────────────────────────────────────────

class SubjectIn(BaseModel):
    name: str
    code: str

class SubjectOut(BaseModel):
    id: int
    name: str
    code: str
    is_active: bool
    class Config:
        from_attributes = True

# ── Academic Year ─────────────────────────────────────────────────────────────

class AcademicYearIn(BaseModel):
    name: str = Field(pattern=r"^\d{4}/\d{4}$", examples=["2024/2025"])
    is_current: bool = False

class AcademicYearOut(BaseModel):
    id: int
    name: str
    is_current: bool
    class Config:
        from_attributes = True

# ── Term ──────────────────────────────────────────────────────────────────────

class TermIn(BaseModel):
    academic_year_id: int
    name: Term
    is_current: bool = False

class TermOut(BaseModel):
    id: int
    academic_year_id: int
    academic_year_name: str
    name: Term
    is_current: bool
    result_published: bool
    published_at: Optional[datetime]
    class Config:
        from_attributes = True

# ── Student ───────────────────────────────────────────────────────────────────

class StudentIn(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    gender: Gender
    date_of_birth: date
    class_level: ClassLevel
    academic_year_id: int
    arm: Optional[str] = Field(None, max_length=5)

class StudentOut(BaseModel):
    id: int
    student_id: str
    email: str
    first_name: str
    last_name: str
    middle_name: Optional[str]
    gender: Gender
    date_of_birth: date
    date_admitted: date
    is_active: bool
    current_class: Optional[str] = None
    class Config:
        from_attributes = True

class StudentListOut(BaseModel):
    id: int
    student_id: str
    first_name: str
    last_name: str
    gender: Gender
    class_level: Optional[str] = None
    arm: Optional[str] = None
    is_active: bool
    class Config:
        from_attributes = True

# ── Result ────────────────────────────────────────────────────────────────────

class ResultIn(BaseModel):
    student_id: int
    subject_id: int
    term_id: int
    ca1:  float = Field(ge=0, le=20)
    ca2:  float = Field(ge=0, le=20)
    exam: float = Field(ge=0, le=60)

class BulkResultIn(BaseModel):
    results: List[ResultIn]

class ResultOut(BaseModel):
    id: int
    student_id: int
    student_name: str
    subject_id: int
    subject_name: str
    term_id: int
    ca1:  Optional[float]
    ca2:  Optional[float]
    exam: Optional[float]
    total:  Optional[float]
    grade:  Optional[str]
    remark: Optional[str]
    is_pass:Optional[bool]
    class Config:
        from_attributes = True

# ── Affective Domain ──────────────────────────────────────────────────────────

class AffectiveIn(BaseModel):
    student_id: int
    term_id: int
    punctuality:      Optional[int] = Field(None, ge=1, le=5)
    neatness:         Optional[int] = Field(None, ge=1, le=5)
    honesty:          Optional[int] = Field(None, ge=1, le=5)
    leadership:       Optional[int] = Field(None, ge=1, le=5)
    sports:           Optional[int] = Field(None, ge=1, le=5)
    arts:             Optional[int] = Field(None, ge=1, le=5)
    verbal_fluency:   Optional[int] = Field(None, ge=1, le=5)
    handling_of_tools:Optional[int] = Field(None, ge=1, le=5)

class AffectiveOut(BaseModel):
    id: int
    student_id: int
    term_id: int
    punctuality:      Optional[int]
    neatness:         Optional[int]
    honesty:          Optional[int]
    leadership:       Optional[int]
    sports:           Optional[int]
    arts:             Optional[int]
    verbal_fluency:   Optional[int]
    handling_of_tools:Optional[int]
    class Config:
        from_attributes = True

# ── Report Card ───────────────────────────────────────────────────────────────

class SubjectRow(BaseModel):
    subject_name: str
    ca1:  Optional[float]
    ca2:  Optional[float]
    exam: Optional[float]
    total:  Optional[float]
    grade:  Optional[str]
    remark: Optional[str]
    is_pass:Optional[bool]

class ReportCardOut(BaseModel):
    student_id:   str
    student_name: str
    class_level:  str
    arm:          Optional[str]
    academic_year:str
    term:         str
    gender:       str
    date_of_birth:date
    total_score:  float
    average:      float
    position:     str
    class_size:   int
    subjects:     List[SubjectRow]
    affective:    Optional[AffectiveOut]
    comment:      str
