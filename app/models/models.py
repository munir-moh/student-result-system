from __future__ import annotations
import enum
from datetime import datetime, date
from typing import Optional, List
from sqlalchemy import (
    String, Integer, Float, Boolean, Text, Date, DateTime,
    ForeignKey, UniqueConstraint, Enum as SAEnum, Index, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship, DeclarativeBase


class Base(DeclarativeBase):
    pass


# ── Enums ─────────────────────────────────────────────────────────────────────

class Role(str, enum.Enum):
    ADMIN   = "admin"
    TEACHER = "teacher"
    STUDENT = "student"

class Term(str, enum.Enum):
    FIRST  = "First"
    SECOND = "Second"
    THIRD  = "Third"

class ClassLevel(str, enum.Enum):
    JSS1 = "JSS1"
    JSS2 = "JSS2"
    JSS3 = "JSS3"
    SS1  = "SS1"
    SS2  = "SS2"
    SS3  = "SS3"

class Gender(str, enum.Enum):
    MALE   = "Male"
    FEMALE = "Female"


# ── User ──────────────────────────────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id:                Mapped[int]      = mapped_column(Integer, primary_key=True)
    email:             Mapped[str]      = mapped_column(String(255), unique=True, index=True)
    hashed_password:   Mapped[str]      = mapped_column(String(255))
    role:              Mapped[Role]     = mapped_column(SAEnum(Role))
    is_active:         Mapped[bool]     = mapped_column(Boolean, default=True)
    must_change_password: Mapped[bool]  = mapped_column(Boolean, default=True)
    created_at:        Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    admin:   Mapped[Optional["Admin"]]   = relationship(back_populates="user", uselist=False)
    teacher: Mapped[Optional["Teacher"]] = relationship(back_populates="user", uselist=False)
    student: Mapped[Optional["Student"]] = relationship(back_populates="user", uselist=False)


# ── Admin ─────────────────────────────────────────────────────────────────────

class Admin(Base):
    __tablename__ = "admins"

    id:         Mapped[int]           = mapped_column(Integer, primary_key=True)
    user_id:    Mapped[int]           = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    admin_id:   Mapped[str]           = mapped_column(String(20), unique=True, index=True)
    first_name: Mapped[str]           = mapped_column(String(100))
    last_name:  Mapped[str]           = mapped_column(String(100))
    phone:      Mapped[Optional[str]] = mapped_column(String(20))

    user: Mapped["User"] = relationship(back_populates="admin")


# ── Teacher ───────────────────────────────────────────────────────────────────

class Teacher(Base):
    __tablename__ = "teachers"

    id:          Mapped[int]             = mapped_column(Integer, primary_key=True)
    user_id:     Mapped[int]             = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    staff_id:    Mapped[str]             = mapped_column(String(20), unique=True, index=True)
    first_name:  Mapped[str]             = mapped_column(String(100))
    last_name:   Mapped[str]             = mapped_column(String(100))
    phone:       Mapped[Optional[str]]   = mapped_column(String(20))
    gender:      Mapped[Optional[Gender]]= mapped_column(SAEnum(Gender))
    is_active:   Mapped[bool]            = mapped_column(Boolean, default=True)
    date_joined: Mapped[date]            = mapped_column(Date, default=date.today)

    user:        Mapped["User"]                   = relationship(back_populates="teacher")
    assignments: Mapped[List["SubjectAssignment"]] = relationship(back_populates="teacher")


# ── Subject ───────────────────────────────────────────────────────────────────

class Subject(Base):
    __tablename__ = "subjects"

    id:        Mapped[int]  = mapped_column(Integer, primary_key=True)
    name:      Mapped[str]  = mapped_column(String(150))
    code:      Mapped[str]  = mapped_column(String(20), unique=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    assignments: Mapped[List["SubjectAssignment"]] = relationship(back_populates="subject")
    results:     Mapped[List["Result"]]             = relationship(back_populates="subject")


# ── Subject Assignment ────────────────────────────────────────────────────────

class SubjectAssignment(Base):
    __tablename__ = "subject_assignments"
    __table_args__ = (UniqueConstraint("teacher_id", "subject_id"),)

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True)
    teacher_id: Mapped[int]      = mapped_column(ForeignKey("teachers.id", ondelete="CASCADE"))
    subject_id: Mapped[int]      = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"))
    assigned_at:Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    teacher: Mapped["Teacher"] = relationship(back_populates="assignments")
    subject: Mapped["Subject"] = relationship(back_populates="assignments")


# ── Academic Year ─────────────────────────────────────────────────────────────

class AcademicYear(Base):
    __tablename__ = "academic_years"

    id:         Mapped[int]      = mapped_column(Integer, primary_key=True)
    name:       Mapped[str]      = mapped_column(String(20), unique=True)  # e.g. 2024/2025
    is_current: Mapped[bool]     = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    terms:       Mapped[List["TermRecord"]]      = relationship(back_populates="academic_year")
    enrollments: Mapped[List["ClassEnrollment"]] = relationship(back_populates="academic_year")


# ── Term Record ───────────────────────────────────────────────────────────────

class TermRecord(Base):
    __tablename__ = "terms"
    __table_args__ = (UniqueConstraint("academic_year_id", "name"),)

    id:               Mapped[int]             = mapped_column(Integer, primary_key=True)
    academic_year_id: Mapped[int]             = mapped_column(ForeignKey("academic_years.id", ondelete="CASCADE"))
    name:             Mapped[Term]            = mapped_column(SAEnum(Term))
    is_current:       Mapped[bool]            = mapped_column(Boolean, default=False)
    result_published: Mapped[bool]            = mapped_column(Boolean, default=False)
    published_at:     Mapped[Optional[datetime]] = mapped_column(DateTime)

    academic_year: Mapped["AcademicYear"]  = relationship(back_populates="terms")
    results:       Mapped[List["Result"]]  = relationship(back_populates="term")


# ── Student ───────────────────────────────────────────────────────────────────

class Student(Base):
    __tablename__ = "students"

    id:            Mapped[int]           = mapped_column(Integer, primary_key=True)
    user_id:       Mapped[int]           = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    student_id:    Mapped[str]           = mapped_column(String(20), unique=True, index=True)
    first_name:    Mapped[str]           = mapped_column(String(100))
    last_name:     Mapped[str]           = mapped_column(String(100))
    middle_name:   Mapped[Optional[str]] = mapped_column(String(100))
    gender:        Mapped[Gender]        = mapped_column(SAEnum(Gender))
    date_of_birth: Mapped[date]          = mapped_column(Date)
    date_admitted: Mapped[date]          = mapped_column(Date, default=date.today)
    is_active:     Mapped[bool]          = mapped_column(Boolean, default=True)

    user:        Mapped["User"]                  = relationship(back_populates="student")
    enrollments: Mapped[List["ClassEnrollment"]] = relationship(back_populates="student")
    results:     Mapped[List["Result"]]          = relationship(back_populates="student")
    affective:   Mapped[List["AffectiveDomain"]] = relationship(back_populates="student")


# ── Class Enrollment ──────────────────────────────────────────────────────────

class ClassEnrollment(Base):
    __tablename__ = "class_enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "academic_year_id"),
        Index("ix_enrollment_year_class", "academic_year_id", "class_level"),
    )

    id:               Mapped[int]        = mapped_column(Integer, primary_key=True)
    student_id:       Mapped[int]        = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    academic_year_id: Mapped[int]        = mapped_column(ForeignKey("academic_years.id", ondelete="CASCADE"))
    class_level:      Mapped[ClassLevel] = mapped_column(SAEnum(ClassLevel))
    arm:              Mapped[Optional[str]] = mapped_column(String(5))

    student:       Mapped["Student"]      = relationship(back_populates="enrollments")
    academic_year: Mapped["AcademicYear"] = relationship(back_populates="enrollments")


# ── Result ────────────────────────────────────────────────────────────────────

class Result(Base):
    __tablename__ = "results"
    __table_args__ = (
        UniqueConstraint("student_id", "subject_id", "term_id"),
        Index("ix_result_student_term", "student_id", "term_id"),
    )

    id:         Mapped[int]            = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int]            = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    subject_id: Mapped[int]            = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"))
    term_id:    Mapped[int]            = mapped_column(ForeignKey("terms.id", ondelete="CASCADE"))
    entered_by: Mapped[int]            = mapped_column(ForeignKey("teachers.id"))
    ca1:        Mapped[Optional[float]]= mapped_column(Float)
    ca2:        Mapped[Optional[float]]= mapped_column(Float)
    exam:       Mapped[Optional[float]]= mapped_column(Float)
    total:      Mapped[Optional[float]]= mapped_column(Float)
    grade:      Mapped[Optional[str]]  = mapped_column(String(2))
    remark:     Mapped[Optional[str]]  = mapped_column(String(20))
    is_pass:    Mapped[Optional[bool]] = mapped_column(Boolean)
    created_at: Mapped[datetime]       = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime]       = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    student: Mapped["Student"]    = relationship(back_populates="results")
    subject: Mapped["Subject"]    = relationship(back_populates="results")
    term:    Mapped["TermRecord"] = relationship(back_populates="results")


# ── Affective Domain ──────────────────────────────────────────────────────────

class AffectiveDomain(Base):
    __tablename__ = "affective_domains"
    __table_args__ = (UniqueConstraint("student_id", "term_id"),)

    id:              Mapped[int]          = mapped_column(Integer, primary_key=True)
    student_id:      Mapped[int]          = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))
    term_id:         Mapped[int]          = mapped_column(ForeignKey("terms.id", ondelete="CASCADE"))
    punctuality:     Mapped[Optional[int]]= mapped_column(Integer)
    neatness:        Mapped[Optional[int]]= mapped_column(Integer)
    honesty:         Mapped[Optional[int]]= mapped_column(Integer)
    leadership:      Mapped[Optional[int]]= mapped_column(Integer)
    sports:          Mapped[Optional[int]]= mapped_column(Integer)
    arts:            Mapped[Optional[int]]= mapped_column(Integer)
    verbal_fluency:  Mapped[Optional[int]]= mapped_column(Integer)
    handling_of_tools:Mapped[Optional[int]]= mapped_column(Integer)
    updated_at:      Mapped[datetime]     = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())

    student: Mapped["Student"] = relationship(back_populates="affective")
