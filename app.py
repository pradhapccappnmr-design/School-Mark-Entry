```python
import os
import hashlib
import secrets
from datetime import datetime

import gradio as gr
import pandas as pd

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    UniqueConstraint,
)

from sqlalchemy.orm import (
    declarative_base,
    sessionmaker,
)


# ==========================================================
# SCHOOL MARK ENTRY SYSTEM
# FINAL CLEAN VERSION
# ==========================================================


# ==========================================================
# DATABASE CONFIGURATION
# ==========================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "",
).strip()


if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = (
        "postgresql://"
        + DATABASE_URL[11:]
    )


if DATABASE_URL:

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )

else:

    engine = create_engine(
        "sqlite:///school_marks.db",
        connect_args={
            "check_same_thread": False
        },
    )


SessionLocal = sessionmaker(
    bind=engine,
)


Base = declarative_base()


# ==========================================================
# DATABASE TABLES
# ==========================================================


class AcademicYear(Base):

    __tablename__ = "academic_years"

    id = Column(
        Integer,
        primary_key=True,
    )

    name = Column(
        String(50),
        unique=True,
        nullable=False,
    )

    active = Column(
        Boolean,
        default=True,
    )


class ClassSection(Base):

    __tablename__ = "classes"

    id = Column(
        Integer,
        primary_key=True,
    )

    name = Column(
        String(50),
        unique=True,
        nullable=False,
    )


class Student(Base):

    __tablename__ = "students"

    id = Column(
        Integer,
        primary_key=True,
    )

    admission_no = Column(
        String(50),
        unique=True,
        nullable=False,
    )

    roll_no = Column(
        String(50),
    )

    name = Column(
        String(200),
        nullable=False,
    )

    class_id = Column(
        Integer,
        ForeignKey("classes.id"),
        nullable=False,
    )

    active = Column(
        Boolean,
        default=True,
    )


class Teacher(Base):

    __tablename__ = "teachers"

    id = Column(
        Integer,
        primary_key=True,
    )

    username = Column(
        String(100),
        unique=True,
        nullable=False,
    )

    name = Column(
        String(200),
        nullable=False,
    )

    password_hash = Column(
        String(500),
        nullable=False,
    )

    role = Column(
        String(20),
        default="teacher",
    )

    active = Column(
        Boolean,
        default=True,
    )


class Subject(Base):

    __tablename__ = "subjects"

    id = Column(
        Integer,
        primary_key=True,
    )

    name = Column(
        String(200),
        nullable=False,
    )

    code = Column(
        String(50),
        unique=True,
        nullable=False,
    )

    theory = Column(
        Boolean,
        default=True,
    )

    practical = Column(
        Boolean,
        default=False,
    )

    internal = Column(
        Boolean,
        default=True,
    )

    theory_max = Column(
        Integer,
        default=0,
    )

    practical_max = Column(
        Integer,
        default=0,
    )

    internal_max = Column(
        Integer,
        default=0,
    )

    active = Column(
        Boolean,
        default=True,
    )


class ClassSubject(Base):

    __tablename__ = "class_subjects"

    id = Column(
        Integer,
        primary_key=True,
    )

    class_id = Column(
        Integer,
        ForeignKey("classes.id"),
        nullable=False,
    )

    subject_id = Column(
        Integer,
        ForeignKey("subjects.id"),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "class_id",
            "subject_id",
            name="uq_class_subject",
        ),
    )


class Exam(Base):

    __tablename__ = "exams"

    id = Column(
        Integer,
        primary_key=True,
    )

    name = Column(
        String(100),
        unique=True,
        nullable=False,
    )

    active = Column(
        Boolean,
        default=True,
    )


class Mark(Base):

    __tablename__ = "marks"

    id = Column(
        Integer,
        primary_key=True,
    )

    academic_year_id = Column(
        Integer,
        ForeignKey("academic_years.id"),
        nullable=False,
    )

    exam_id = Column(
        Integer,
        ForeignKey("exams.id"),
        nullable=False,
    )

    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=False,
    )

    subject_id = Column(
        Integer,
        ForeignKey("subjects.id"),
        nullable=False,
    )

    theory = Column(
        Integer,
        default=0,
    )

    practical = Column(
        Integer,
        default=0,
    )

    internal = Column(
        Integer,
        default=0,
    )

    total = Column(
        Integer,
        default=0,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    __table_args__ = (
        UniqueConstraint(
            "academic_year_id",
            "exam_id",
            "student_id",
            "subject_id",
            name="uq_student_exam_subject",
        ),
    )


# ==========================================================
# CREATE TABLES
# ==========================================================

Base.metadata.create_all(
    engine
)


# ==========================================================
# PASSWORD FUNCTIONS
# ==========================================================


def hash_password(password):

    salt = secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        120000,
    ).hex()

    return (
        salt
        + "$"
        + digest
    )


def verify_password(
    password,
    stored,
):

    try:

        salt, digest = stored.split(
            "$",
            1,
        )

        check = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            120000,
        ).hex()

        return secrets.compare_digest(
            check,
            digest,
        )

    except Exception:

        return False


# ==========================================================
# BASIC HELPERS
# ==========================================================


def clean_name(value):

    return str(
        value or ""
    ).strip()


def parse_id(value):

    if not value:
        return None

    try:

        return int(
            str(value)
            .split("|", 1)[0]
            .strip()
        )

    except Exception:

        return None


def safe_int(
    value,
    default=0,
):

    try:

        if value in (
            None,
            "",
        ):

            return default

        return int(
            float(value)
        )

    except Exception:

        return default


# ==========================================================
# INITIAL DATABASE
# ==========================================================


def seed_database():

    db = SessionLocal()

    try:

        # --------------------------------------------------
        # Academic Year
        # --------------------------------------------------

        if not db.query(
            AcademicYear
        ).first():

            db.add(
                AcademicYear(
                    name="2026-27",
                    active=True,
                )
            )


        # --------------------------------------------------
        # Classes
        # --------------------------------------------------

        if not db.query(
            ClassSection
        ).first():

            db.add_all([

                ClassSection(
                    name="10-A"
                ),

                ClassSection(
                    name="10-B"
                ),

                ClassSection(
                    name="11-A"
                ),

                ClassSection(
                    name="11-B"
                ),

                ClassSection(
                    name="12-A"
                ),

                ClassSection(
                    name="12-B"
                ),

            ])


        # --------------------------------------------------
        # Exams
        # --------------------------------------------------

        if not db.query(
            Exam
        ).first():

            db.add_all([

                Exam(
                    name="Unit Test 1"
                ),

                Exam(
                    name="Quarterly"
                ),

                Exam(
                    name="Half-Yearly"
                ),

                Exam(
                    name="Annual"
                ),

            ])


        # --------------------------------------------------
        # Subjects
        # --------------------------------------------------

        if not db.query(
            Subject
        ).first():

            db.add_all([

                Subject(
                    name="Tamil",
                    code="TAM",
                    theory=True,
                    practical=False,
                    internal=True,
                    theory_max=80,
                    practical_max=0,
                    internal_max=20,
                ),

                Subject(
                    name="English",
                    code="ENG",
                    theory=True,
                    practical=False,
                    internal=True,
                    theory_max=80,
                    practical_max=0,
                    internal_max=20,
                ),

                Subject(
                    name="Mathematics",
                    code="MAT",
                    theory=True,
                    practical=False,
                    internal=True,
                    theory_max=80,
                    practical_max=0,
                    internal_max=20,
                ),

                Subject(
                    name="Physics",
                    code="PHY",
                    theory=True,
                    practical=True,
                    internal=True,
                    theory_max=70,
                    practical_max=20,
                    internal_max=10,
                ),

                Subject(
                    name="Chemistry",
                    code="CHE",
                    theory=True,
                    practical=True,
                    internal=True,
                    theory_max=70,
                    practical_max=20,
                    internal_max=10,
                ),

                Subject(
                    name="Computer Science",
                    code="CS",
                    theory=True,
                    practical=True,
                    internal=True,
                    theory_max=70,
                    practical_max=20,
                    internal_max=10,
                ),

            ])


        # --------------------------------------------------
        # Admin
        # --------------------------------------------------

        if not db.query(
            Teacher
        ).filter_by(
            username="admin"
        ).first():

            db.add(
                Teacher(
                    username="admin",
                    name="Administrator",
                    password_hash=hash_password(
                        "Admin@123"
                    ),
                    role="admin",
                    active=True,
                )
            )


        db.commit()


        # --------------------------------------------------
        # Connect active subjects to all classes
        # --------------------------------------------------

        all_classes = db.query(
            ClassSection
        ).all()

        all_subjects = (
            db.query(Subject)
            .filter(
                Subject.active == True
            )
            .all()
        )


        for cls in all_classes:

            for subject in all_subjects:

                exists = (
                    db.query(
                        ClassSubject
                    )
                    .filter_by(
                        class_id=cls.id,
                        subject_id=subject.id,
                    )
                    .first()
                )


                if not exists:

                    db.add(
                        ClassSubject(
                            class_id=cls.id,
                            subject_id=subject.id,
                        )
                    )


        db.commit()


    finally:

        db.close()


seed_database()


# ==========================================================
# CHOICE HELPERS
# ==========================================================


def get_classes():

    db = SessionLocal()

    try:

        rows = (
            db.query(ClassSection)
            .order_by(
                ClassSection.name
            )
            .all()
        )

        return [
            f"{row.id} | {row.name}"
            for row in rows
        ]

    finally:

        db.close()


def get_years():

    db = SessionLocal()

    try:

        rows = (
            db.query(AcademicYear)
            .filter(
                AcademicYear.active == True
            )
            .order_by(
                AcademicYear.name
            )
            .all()
        )

        return [
            f"{row.id} | {row.name}"
            for row in rows
        ]

    finally:

        db.close()


def get_exams():

    db = SessionLocal()

    try:

        rows = (
            db.query(Exam)
            .filter(
                Exam.active == True
            )
            .order_by(
                Exam.id
            )
            .all()
        )

        return [
            f"{row.id} | {row.name}"
            for row in rows
        ]

    finally:

        db.close()


def get_all_exams():

    db = SessionLocal()

    try:

        rows = (
            db.query(Exam)
            .filter(
                Exam.active == True
            )
            .order_by(
                Exam.id
            )
            .all()
        )

        return (
            ["ALL | All Exams"]
            + [
                f"{row.id} | {row.name}"
                for row in rows
            ]
        )

    finally:

        db.close()


def get_subject_choices():

    db = SessionLocal()

    try:

        rows = (
            db.query(Subject)
            .filter(
                Subject.active == True
            )
            .order_by(
                Subject.name
            )
            .all()
        )

        return [
            f"{row.id} | {row.name}"
            for row in rows
        ]

    finally:

        db.close()


def get_subjects_for_class(
    class_value
):

    class_id = parse_id(
        class_value
    )

    if not class_id:

        return gr.Dropdown(
            choices=[],
            value=None,
        )


    db = SessionLocal()

    try:

        subjects = (
            db.query(Subject)
            .join(
                ClassSubject,
                ClassSubject.subject_id
                == Subject.id,
            )
            .filter(
                ClassSubject.class_id
                == class_id,
                Subject.active == True,
            )
            .order_by(
                Subject.name
            )
            .all()
        )

        choices = [
            f"{subject.id} | {subject.name}"
            for subject in subjects
        ]

        return gr.Dropdown(
            choices=choices,
            value=None,
        )

    finally:

        db.close()


def get_student_delete_choices():

    db = SessionLocal()

    try:

        students = (
            db.query(Student)
            .filter(
                Student.active == True
            )
            .order_by(
                Student.roll_no,
                Student.name,
            )
            .all()
        )

        return [
            (
                f"{student.id} | "
                f"{student.roll_no or '-'} | "
                f"{student.name}"
            )
            for student in students
        ]

    finally:

        db.close()


# ==========================================================
# STUDENT LIST
# ==========================================================


def get_student_list():

    db = SessionLocal()

    try:

        rows = (
            db.query(
                Student,
                ClassSection,
            )
            .join(
                ClassSection,
                Student.class_id
                == ClassSection.id,
            )
            .filter(
                Student.active == True
            )
            .order_by(
                ClassSection.name,
                Student.roll_no,
                Student.name,
            )
            .all()
        )

        return [

            [
                student.id,
                student.admission_no,
                student.roll_no or "",
                student.name,
                cls.name,
            ]

            for student, cls in rows

        ]

    finally:

        db.close()


# ==========================================================
# ACADEMIC YEAR LIST
# ==========================================================


def get_year_list():

    db = SessionLocal()

    try:

        rows = (
            db.query(AcademicYear)
            .order_by(
                AcademicYear.name
            )
            .all()
        )

        return [

            [
                row.id,
                row.name,
                "Active"
                if row.active
                else "Deleted",
            ]

            for row in rows

        ]

    finally:

        db.close()


# ==========================================================
# CLASS LIST
# ==========================================================


def get_class_list():

    db = SessionLocal()

    try:

        rows = (
            db.query(ClassSection)
            .order_by(
                ClassSection.name
            )
            .all()
        )

        return [
            [
                row.id,
                row.name,
            ]
            for row in rows
        ]

    finally:

        db.close()


# ==========================================================
# SUBJECT LIST
# ==========================================================


def get_subject_list():

    db = SessionLocal()

    try:

        rows = (
            db.query(Subject)
            .order_by(
                Subject.name
            )
            .all()
        )

        result = []

        for subject in rows:

            components = []

            if subject.theory:

                components.append(
                    f"Theory ({subject.theory_max})"
                )

            if subject.practical:

                components.append(
                    f"Practical ({subject.practical_max})"
                )

            if subject.internal:

                components.append(
                    f"Internal ({subject.internal_max})"
                )

            result.append([

                subject.id,

                subject.name,

                subject.code,

                " + ".join(
                    components
                ),

                "Active"
                if subject.active
                else "Deleted",

            ])

        return result

    finally:

        db.close()


# ==========================================================
# EXAM LIST
# ==========================================================


def get_exam_list():

    db = SessionLocal()

    try:

        rows = (
            db.query(Exam)
            .order_by(
                Exam.id
            )
            .all()
        )

        return [

            [
                row.id,
                row.name,
                "Active"
                if row.active
                else "Deleted",
            ]

            for row in rows

        ]

    finally:

        db.close()


# ==========================================================
# ADD STUDENT
# ==========================================================


def add_student(
    admission_no,
    roll_no,
    student_name,
    class_value,
):

    admission_no = clean_name(
        admission_no
    )

    roll_no = clean_name(
        roll_no
    )

    student_name = clean_name(
        student_name
    )

    class_id = parse_id(
        class_value
    )


    if not admission_no:

        return (
            "❌ Admission No is required.",
            get_student_list(),
            gr.Dropdown(
                choices=get_student_delete_choices(),
                value=None,
            ),
        )


    if not student_name:

        return (
            "❌ Student Name is required.",
            get_student_list(),
            gr.Dropdown(
                choices=get_student_delete_choices(),
                value=None,
            ),
        )


    if not class_id:

        return (
            "❌ Please select Class.",
            get_student_list(),
            gr.Dropdown(
                choices=get_student_delete_choices(),
                value=None,
            ),
        )


    db = SessionLocal()

    try:

        existing = (
            db.query(Student)
            .filter(
                Student.admission_no
                == admission_no
            )
            .first()
        )


        if existing:

            if not existing.active:

                existing.active = True
                existing.roll_no = roll_no
                existing.name = student_name
                existing.class_id = class_id

                db.commit()

                return (
                    "✅ Student restored successfully.",
                    get_student_list(),
                    gr.Dropdown(
                        choices=get_student_delete_choices(),
                        value=None,
                    ),
                )


            return (
                "❌ This Admission No already exists.",
                get_student_list(),
                gr.Dropdown(
                    choices=get_student_delete_choices(),
                    value=None,
                ),
            )


        student = Student(

            admission_no=admission_no,

            roll_no=roll_no,

            name=student_name,

            class_id=class_id,

            active=True,

        )


        db.add(student)

        db.commit()


        return (
            "✅ Student added successfully.",
            get_student_list(),
            gr.Dropdown(
                choices=get_student_delete_choices(),
                value=None,
            ),
        )


    except Exception as e:

        db.rollback()

        return (
            "❌ Error: " + str(e),
            get_student_list(),
            gr.Dropdown(
                choices=get_student_delete_choices(),
                value=None,
            ),
        )

    finally:

        db.close()


# ==========================================================
# DELETE STUDENT
# ==========================================================


def delete_student(
    student_value
):

    student_id = parse_id(
        student_value
    )


    if not student_id:

        return (
            "❌ Please select a Student.",
            get_student_list(),
            gr.Dropdown(
                choices=get_student_delete_choices(),
                value=None,
            ),
        )


    db = SessionLocal()

    try:

        student = db.get(
            Student,
            student_id,
        )


        if student is None:

            return (
                "❌ Student not found.",
                get_student_list(),
                gr.Dropdown(
                    choices=get_student_delete_choices(),
                    value=None,
                ),
            )


        student.active = False

        db.commit()


        return (
            "✅ Student deleted successfully. "
            "Existing marks are preserved.",
            get_student_list(),
            gr.Dropdown(
                choices=get_student_delete_choices(),
                value=None,
            ),
        )


    except Exception as e:

        db.rollback()

        return (
            "❌ Error: " + str(e),
            get_student_list(),
            gr.Dropdown(
                choices=get_student_delete_choices(),
                value=None,
            ),
        )

    finally:

        db.close()


# ==========================================================
# ADD ACADEMIC YEAR
# ==========================================================


def add_academic_year(
    year_name
):

    year_name = clean_name(
        year_name
    )


    if not year_name:

        return (
            "❌ Academic Year is required.",
            get_year_list(),
            gr.Dropdown(
                choices=get_years(),
                value=None,
            ),
            gr.Dropdown(
                choices=get_years(),
                value=None,
            ),
            gr.Dropdown(
                choices=get_years(),
                value=None,
            ),
            gr.Dropdown(
                choices=get_years(),
                value=None,
            ),
        )


    db = SessionLocal()

    try:

        existing = (
            db.query(AcademicYear)
            .filter(
                AcademicYear.name
                == year_name
            )
            .first()
        )


        if existing:

            if not existing.active:

                existing.active = True

                db.commit()

                choices = get_years()

                return (
                    "✅ Academic Year restored.",
                    get_year_list(),
                    gr.Dropdown(
                        choices=choices,
                        value=None,
                    ),
                    gr.Dropdown(
                        choices=choices,
                        value=None,
                    ),
                    gr.Dropdown(
                        choices=choices,
                        value=None,
                    ),
                    gr.Dropdown(
                        choices=choices,
                        value=None,
                    ),
                )


            choices = get_years()

            return (
                "❌ Academic Year already exists.",
                get_year_list(),
                gr.Dropdown(
                    choices=choices,
                    value=None,
                ),
                gr.Dropdown(
                    choices=choices,
                    value=None,
                ),
                gr.Dropdown(
                    choices=choices,
                    value=None,
                ),
                gr.Dropdown(
                    choices=choices,
                    value=None,
                ),
            )


        db.add(
            AcademicYear(
                name=year_name,
                active=True,
            )
        )

        db.commit()

        choices = get_years()

        return (
            "✅ Academic Year added successfully.",
            get_year_list(),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
        )


    except Exception as e:

        db.rollback()

        choices = get_years()

        return (
            "❌ Error: " + str(e),
            get_year_list(),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
        )

    finally:

        db.close()


# ==========================================================
# DELETE ACADEMIC YEAR
# ==========================================================


def delete_academic_year(
    year_value
):

    year_id = parse_id(
        year_value
    )


    if not year_id:

        choices = get_years()

        return (
            "❌ Please select an Academic Year.",
            get_year_list(),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
        )


    db = SessionLocal()

    try:

        year = db.get(
            AcademicYear,
            year_id,
        )


        if year is None:

            choices = get_years()

            return (
                "❌ Academic Year not found.",
                get_year_list(),
                gr.Dropdown(
                    choices=choices,
                    value=None,
                ),
                gr.Dropdown(
                    choices=choices,
                    value=None,
                ),
                gr.Dropdown(
                    choices=choices,
                    value=None,
                ),
                gr.Dropdown(
                    choices=choices,
                    value=None,
                ),
            )


        year.active = False

        db.commit()

        choices = get_years()

        return (
            "✅ Academic Year deleted. "
            "Existing marks are preserved.",
            get_year_list(),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
        )


    except Exception as e:

        db.rollback()

        choices = get_years()

        return (
            "❌ Error: " + str(e),
            get_year_list(),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
        )

    finally:

        db.close()


# ==========================================================
# ADD CLASS
# ==========================================================


def add_class(
    class_name
):

    class_name = clean_name(
        class_name
    )


    if not class_name:

        choices = get_classes()

        return (
            "❌ Class name is required.",
            get_class_list(),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
        )


    db = SessionLocal()

    try:

        existing = (
            db.query(ClassSection)
            .filter(
                ClassSection.name
                == class_name
            )
            .first()
        )


        if existing:

            choices = get_classes()

            return (
                "❌ Class already exists.",
                get_class_list(),
                gr.Dropdown(
                    choices=choices,
                    value=None,
                ),
                gr.Dropdown(
                    choices=choices,
                    value=None,
                ),
                gr.Dropdown(
                    choices=choices,
                    value=None,
                ),
                gr.Dropdown(
                    choices=choices,
                    value=None,
                ),
                gr.Dropdown(
                    choices=choices,
                    value=None,
                ),
            )


        new_class = ClassSection(
            name=class_name
        )

        db.add(new_class)

        db.flush()


        subjects = (
            db.query(Subject)
            .filter(
                Subject.active == True
            )
            .all()
        )


        for subject in subjects:

            db.add(
                ClassSubject(
                    class_id=new_class.id,
                    subject_id=subject.id,
                )
            )


        db.commit()

        choices = get_classes()

        return (
            "✅ Class added successfully.",
            get_class_list(),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
        )


    except Exception as e:

        db.rollback()

        choices = get_classes()

        return (
            "❌ Error: " + str(e),
            get_class_list(),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
            gr.Dropdown(
                choices=choices,
                value=None,
            ),
        )

    finally:

        db.close()


# ==========================================================
# DELETE CLASS
# ==========================================================


def delete_class(
    class_value
):

    class_id = parse_id(
        class_value
    )


    if not class_id:

        choices = get_classes()

        return (
            "❌ Please select a Class.",
            get_class_list(),
            *[
                gr.Dropdown(
                    choices=choices,
                    value=None,
                )
                for _ in range(5)
            ],
        )


    db = SessionLocal()

    try:

        cls = db.get(
            ClassSection,
            class_id,
        )


        if cls is None:

            choices = get_classes()

            return (
                "❌ Class not found.",
                get_class_list(),
                *[
                    gr.Dropdown(
                        choices=choices,
                        value=None,
                    )
                    for _ in range(5)
                ],
            )


        active_students = (
            db.query(Student)
            .filter(
                Student.class_id == class_id,
                Student.active == True,
            )
            .count()
        )


        if active_students > 0:

            choices = get_classes()

            return (
                "❌ Cannot delete this Class because "
                "it still has active students.",
                get_class_list(),
                *[
                    gr.Dropdown(
                        choices=choices,
                        value=None,
                    )
                    for _ in range(5)
                ],
            )


        db.query(
            ClassSubject
        ).filter(
            ClassSubject.class_id
            == class_id
        ).delete(
            synchronize_session=False
        )


        db.delete(cls)

        db.commit()

        choices = get_classes()

        return (
            "✅ Class deleted successfully.",
            get_class_list(),
            *[
                gr.Dropdown(
                    choices=choices,
                    value=None,
                )
                for _ in range(5)
            ],
        )


    except Exception as e:

        db.rollback()

        choices = get_classes()

        return (
            "❌ Error: " + str(e),
            get_class_list(),
            *[
                gr.Dropdown(
                    choices=choices,
                    value=None,
                )
                for _ in range(5)
            ],
        )

    finally:

        db.close()


# ==========================================================
# ADD SUBJECT
# ==========================================================


def add_subject(
    subject_name,
    subject_code,
    theory,
    practical,
    internal,
    theory_max,
    practical_max,
    internal_max,
):

    subject_name = clean_name(
        subject_name
    )

    subject_code = clean_name(
        subject_code
    ).upper()


    if not subject_name:

        return (
            "❌ Subject name is required.",
            get_subject_list(),
            gr.Dropdown(
                choices=get_subject_choices(),
                value=None,
            ),
        )


    if not subject_code:

        return (
            "❌ Subject code is required.",
            get_subject_list(),
            gr.Dropdown(
                choices=get_subject_choices(),
                value=None,
            ),
        )


    if not any([
        theory,
        practical,
        internal,
    ]):

        return (
            "❌ Select at least one component.",
            get_subject_list(),
            gr.Dropdown(
                choices=get_subject_choices(),
                value=None,
            ),
        )


    theory_max = safe_int(
        theory_max
    )

    practical_max = safe_int(
        practical_max
    )

    internal_max = safe_int(
        internal_max
    )


    if theory and theory_max <= 0:

        return (
            "❌ Theory maximum must be greater than 0.",
            get_subject_list(),
            gr.Dropdown(
                choices=get_subject_choices(),
                value=None,
            ),
        )


    if practical and practical_max <= 0:

        return (
            "❌ Practical maximum must be greater than 0.",
            get_subject_list(),
            gr.Dropdown(
                choices=get_subject_choices(),
                value=None,
            ),
        )


    if internal and internal_max <= 0:

        return (
            "❌ Internal maximum must be greater than 0.",
            get_subject_list(),
            gr.Dropdown(
                choices=get_subject_choices(),
                value=None,
            ),
        )


    db = SessionLocal()

    try:

        existing = (
            db.query(Subject)
            .filter(
                Subject.code
                == subject_code
            )
            .first()
        )


        if existing:

            if not existing.active:

                existing.active = True
                existing.name = subject_name
                existing.theory = bool(theory)
                existing.practical = bool(practical)
                existing.internal = bool(internal)
                existing.theory_max = theory_max
                existing.practical_max = practical_max
                existing.internal_max = internal_max

                subject_id = existing.id

            else:

                return (
                    "❌ Subject code already exists.",
                    get_subject_list(),
                    gr.Dropdown(
                        choices=get_subject_choices(),
                        value=None,
                    ),
                )

        else:

            subject = Subject(

                name=subject_name,

                code=subject_code,

                theory=bool(theory),

                practical=bool(practical),

                internal=bool(internal),

                theory_max=theory_max,

                practical_max=practical_max,

                internal_max=internal_max,

                active=True,

            )

            db.add(subject)

            db.flush()

            subject_id = subject.id


        classes = (
            db.query(ClassSection)
            .all()
        )


        for cls in classes:

            exists = (
                db.query(ClassSubject)
                .filter_by(
                    class_id=cls.id,
                    subject_id=subject_id,
                )
                .first()
            )


            if not exists:

                db.add(
                    ClassSubject(
                        class_id=cls.id,
                        subject_id=subject_id,
                    )
                )


        db.commit()


        return (
            "✅ Subject added successfully.",
            get_subject_list(),
            gr.Dropdown(
                choices=get_subject_choices(),
                value=None,
            ),
        )


    except Exception as e:

        db.rollback()

        return (
            "❌ Error: " + str(e),
            get_subject_list(),
            gr.Dropdown(
                choices=get_subject_choices(),
                value=None,
            ),
        )

    finally:

        db.close()


# ==========================================================
# DELETE SUBJECT
# ==========================================================


def delete_subject(
    subject_value
):

    subject_id = parse_id(
        subject_value
    )


    if not subject_id:

        return (
            "❌ Please select a Subject.",
            get_subject_list(),
            gr.Dropdown(
                choices=get_subject_choices(),
                value=None,
            ),
        )


    db = SessionLocal()

    try:

        subject = db.get(
            Subject,
            subject_id,
        )


        if subject is None:

            return (
                "❌ Subject not found.",
                get_subject_list(),
                gr.Dropdown(
                    choices=get_subject_choices(),
                    value=None,
                ),
            )


        subject.active = False

        db.commit()


        return (
            "✅ Subject deleted. Existing marks are preserved.",
            get_subject_list(),
            gr.Dropdown(
                choices=get_subject_choices(),
                value=None,
            ),
        )


    except Exception as e:

        db.rollback()

        return (
            "❌ Error: " + str(e),
            get_subject_list(),
            gr.Dropdown(
                choices=get_subject_choices(),
                value=None,
            ),
        )

    finally:

        db.close()


# ==========================================================
# ADD EXAM
# ==========================================================


def add_exam(
    exam_name
):

    exam_name = clean_name(
        exam_name
    )


    if not exam_name:

        choices = get_exams()

        return (
            "❌ Exam name is required.",
            get_exam_list(),
            *[
                gr.Dropdown(
                    choices=choices,
                    value=None,
                )
                for _ in range(4)
            ],
        )


    db = SessionLocal()

    try:

        existing = (
            db.query(Exam)
            .filter(
                Exam.name
                == exam_name
            )
            .first()
        )


        if existing:

            if not existing.active:

                existing.active = True

                db.commit()

                choices = get_exams()

                return (
                    "✅ Exam restored successfully.",
                    get_exam_list(),
                    *[
                        gr.Dropdown(
                            choices=choices,
                            value=None,
                        )
                        for _ in range(4)
                    ],
                )


            choices = get_exams()

            return (
                "❌ Exam already exists.",
                get_exam_list(),
                *[
                    gr.Dropdown(
                        choices=choices,
                        value=None,
                    )
                    for _ in range(4)
                ],
            )


        db.add(
            Exam(
                name=exam_name,
                active=True,
            )
        )

        db.commit()

        choices = get_exams()

        return (
            "✅ Exam added successfully.",
            get_exam_list(),
            *[
                gr.Dropdown(
                    choices=choices,
                    value=None,
                )
                for _ in range(4)
            ],
        )


    except Exception as e:

        db.rollback()

        choices = get_exams()

        return (
            "❌ Error: " + str(e),
            get_exam_list(),
            *[
                gr.Dropdown(
                    choices=choices,
                    value=None,
                )
                for _ in range(4)
            ],
        )

    finally:

        db.close()


# ==========================================================
# DELETE EXAM
# ==========================================================


def delete_exam(
    exam_value
):

    exam_id = parse_id(
        exam_value
    )


    if not exam_id:

        choices = get_exams()

        return (
            "❌ Please select an Exam.",
            get_exam_list(),
            *[
                gr.Dropdown(
                    choices=choices,
                    value=None,
                )
                for _ in range(4)
            ],
        )


    db = SessionLocal()

    try:

        exam = db.get(
            Exam,
            exam_id,
        )


        if exam is None:

            choices = get_exams()

            return (
                "❌ Exam not found.",
                get_exam_list(),
                *[
                    gr.Dropdown(
                        choices=choices,
                        value=None,
                    )
                    for _ in range(4)
                ],
            )


        exam.active = False

        db.commit()

        choices = get_exams()

        return (
            "✅ Exam deleted. Existing marks are preserved.",
            get_exam_list(),
            *[
                gr.Dropdown(
                    choices=choices,
                    value=None,
                )
                for _ in range(4)
            ],
        )


    except Exception as e:

        db.rollback()

        choices = get_exams()

        return (
            "❌ Error: " + str(e),
            get_exam_list(),
            *[
                gr.Dropdown(
                    choices=choices,
                    value=None,
                )
                for _ in range(4)
            ],
        )

    finally:

        db.close()


# ==========================================================
# MARK ENTRY - LOAD
# ==========================================================


def load_marks(
    class_value,
    year_value,
    exam_value,
    subject_value,
):

    class_id = parse_id(
        class_value
    )

    year_id = parse_id(
        year_value
    )

    exam_id = parse_id(
        exam_value
    )

    subject_id = parse_id(
        subject_value
    )


    if not class_id:

        return (
            [],
            "❌ Please select Class.",
        )


    if not year_id:

        return (
            [],
            "❌ Please select Academic Year.",
        )


    if not exam_id:

        return (
            [],
            "❌ Please select Exam.",
        )


    if not subject_id:

        return (
            [],
            "❌ Please select Subject.",
        )


    db = SessionLocal()

    try:

        subject = db.get(
            Subject,
            subject_id,
        )


        if subject is None or not subject.active:

            return (
                [],
                "❌ Subject not found.",
            )


        students = (
            db.query(Student)
            .filter(
                Student.class_id == class_id,
                Student.active == True,
            )
            .order_by(
                Student.roll_no,
                Student.name,
            )
            .all()
        )


        headers = [
            "ID",
            "Roll No",
            "Student Name",
        ]


        if subject.theory:

            headers.append(
                f"Theory / {subject.theory_max}"
            )


        if subject.practical:

            headers.append(
                f"Practical / {subject.practical_max}"
            )


        if subject.internal:

            headers.append(
                f"Internal / {subject.internal_max}"
            )


        headers.append(
            "Total"
        )


        rows = []


        for student in students:

            mark = (
                db.query(Mark)
                .filter_by(
                    academic_year_id=year_id,
                    exam_id=exam_id,
                    student_id=student.id,
                    subject_id=subject_id,
                )
                .first()
            )


            theory = (
                mark.theory
                if mark
                else 0
            )

            practical = (
                mark.practical
                if mark
                else 0
            )

            internal = (
                mark.internal
                if mark
                else 0
            )


            total = (
                theory
                + practical
                + internal
            )


            row = [

                student.id,

                student.roll_no or "",

                student.name,

            ]


            if subject.theory:

                row.append(
                    theory
                )


            if subject.practical:

                row.append(
                    practical
                )


            if subject.internal:

                row.append(
                    internal
                )


            row.append(
                total
            )


            rows.append(row)


        pattern = []


        if subject.theory:

            pattern.append(
                f"Theory: {subject.theory_max}"
            )


        if subject.practical:

            pattern.append(
                f"Practical: {subject.practical_max}"
            )


        if subject.internal:

            pattern.append(
                f"Internal: {subject.internal_max}"
            )


        return (
            rows,
            "**Mark Pattern:** "
            + " + ".join(pattern),
        )


    finally:

        db.close()


# ==========================================================
# MARK ENTRY - SAVE
# ==========================================================


def save_marks(
    class_value,
    year_value,
    exam_value,
    subject_value,
    table_data,
):

    class_id = parse_id(
        class_value
    )

    year_id = parse_id(
        year_value
    )

    exam_id = parse_id(
        exam_value
    )

    subject_id = parse_id(
        subject_value
    )


    if not class_id:

        return "❌ Please select Class."


    if not year_id:

        return "❌ Please select Academic Year."


    if not exam_id:

        return "❌ Please select Exam."


    if not subject_id:

        return "❌ Please select Subject."


    if table_data is None:

        return (
            "❌ No student data found. "
            "Please click Load Students."
        )


    db = SessionLocal()

    try:

        subject = (
            db.query(Subject)
            .filter(
                Subject.id == subject_id,
                Subject.active == True,
            )
            .first()
        )


        if subject is None:

            return "❌ Subject not found."


        if hasattr(
            table_data,
            "values"
        ):

            rows = (
                table_data.values.tolist()
            )

        else:

            rows = table_data


        if not rows:

            return (
                "❌ No student rows found."
            )


        saved_count = 0


        for row in rows:

            if not row:

                continue


            if len(row) < 3:

                continue


            try:

                student_id = int(
                    row[0]
                )

            except Exception:

                continue


            student = (
                db.query(Student)
                .filter(
                    Student.id == student_id,
                    Student.class_id == class_id,
                    Student.active == True,
                )
                .first()
            )


            if student is None:

                continue


            position = 3


            theory = 0
            practical = 0
            internal = 0


            if subject.theory:

                if len(row) > position:

                    theory = safe_int(
                        row[position]
                    )

                position += 1


            if subject.practical:

                if len(row) > position:

                    practical = safe_int(
                        row[position]
                    )

                position += 1


            if subject.internal:

                if len(row) > position:

                    internal = safe_int(
                        row[position]
                    )

                position += 1


            # --------------------------------------------------
            # Validate maximum marks
            # --------------------------------------------------

            if theory < 0 or theory > subject.theory_max:

                return (
                    f"❌ Invalid Theory mark for "
                    f"{student.name}. "
                    f"Maximum is {subject.theory_max}."
                )


            if (
                subject.practical
                and (
                    practical < 0
                    or practical > subject.practical_max
                )
            ):

                return (
                    f"❌ Invalid Practical mark for "
                    f"{student.name}. "
                    f"Maximum is {subject.practical_max}."
                )


            if (
                subject.internal
                and (
                    internal < 0
                    or internal > subject.internal_max
                )
            ):

                return (
                    f"❌ Invalid Internal mark for "
                    f"{student.name}. "
                    f"Maximum is {subject.internal_max}."
                )


            total = (
                theory
                + practical
                + internal
            )


            mark = (
                db.query(Mark)
                .filter_by(
                    academic_year_id=year_id,
                    exam_id=exam_id,
                    student_id=student_id,
                    subject_id=subject_id,
                )
                .first()
            )


            if mark is None:

                mark = Mark(

                    academic_year_id=year_id,

                    exam_id=exam_id,

                    student_id=student_id,

                    subject_id=subject_id,

                )

                db.add(mark)


            mark.theory = theory

            mark.practical = practical

            mark.internal = internal

            mark.total = total

            mark.updated_at = datetime.utcnow()


            saved_count += 1


        if saved_count == 0:

            return (
                "❌ No valid student rows found."
            )


        db.commit()


        return (
            f"✅ Marks saved successfully for "
            f"{saved_count} student(s)."
        )


    except Exception as e:

        db.rollback()

        return (
            "❌ Error while saving marks: "
            + str(e)
        )

    finally:

        db.close()


# ==========================================================
# CONSOLIDATED REPORT
# ==========================================================
#
# Clean format:
#
# Roll No | Student Name | Subject | Exam |
# Theory | Practical | Internal | Subject Total
#
# Chemistry and Quarterly are NOT repeated in column names.
#
# ==========================================================


def generate_consolidated_report(
    year_value,
    class_value,
    exam_value,
):

    year_id = parse_id(
        year_value
    )

    class_id = parse_id(
        class_value
    )


    if not year_id:

        return (
            "❌ Please select Academic Year.",
            pd.DataFrame(),
        )


    if not class_id:

        return (
            "❌ Please select Class.",
            pd.DataFrame(),
        )


    if not exam_value:

        return (
            "❌ Please select Exam.",
            pd.DataFrame(),
        )


    db = SessionLocal()

    try:

        class_obj = (
            db.query(ClassSection)
            .filter(
                ClassSection.id == class_id
            )
            .first()
        )


        if class_obj is None:

            return (
                "❌ Class not found.",
                pd.DataFrame(),
            )


        students = (
            db.query(Student)
            .filter(
                Student.class_id == class_id,
                Student.active == True,
            )
            .order_by(
                Student.roll_no,
                Student.name,
            )
            .all()
        )


        if not students:

            return (
                "❌ No students found in this class.",
                pd.DataFrame(),
            )


        subjects = (
            db.query(Subject)
            .join(
                ClassSubject,
                ClassSubject.subject_id
                == Subject.id,
            )
            .filter(
                ClassSubject.class_id == class_id,
                Subject.active == True,
            )
            .order_by(
                Subject.name
            )
            .all()
        )


        if not subjects:

            return (
                "❌ No subjects found for this class.",
                pd.DataFrame(),
            )


        # --------------------------------------------------
        # Exams
        # --------------------------------------------------

        if str(
            exam_value
        ).startswith("ALL"):

            exams = (
                db.query(Exam)
                .filter(
                    Exam.active == True
                )
                .order_by(
                    Exam.id
                )
                .all()
            )

        else:

            exam_id = parse_id(
                exam_value
            )

            exam_obj = (
                db.query(Exam)
                .filter(
                    Exam.id == exam_id,
                    Exam.active == True,
                )
                .first()
            )


            if exam_obj is None:

                return (
                    "❌ Exam not found.",
                    pd.DataFrame(),
                )


            exams = [
                exam_obj
            ]


        if not exams:

            return (
                "❌ No exams found.",
                pd.DataFrame(),
            )


        # --------------------------------------------------
        # Build report
        # --------------------------------------------------

        report_rows = []


        for student in students:

            for exam in exams:

                exam_total = 0


                for subject in subjects:

                    mark = (
                        db.query(Mark)
                        .filter_by(
                            academic_year_id=year_id,
                            exam_id=exam.id,
                            student_id=student.id,
                            subject_id=subject.id,
                        )
                        .first()
                    )


                    theory = (
                        mark.theory
                        if mark
                        else 0
                    )

                    practical = (
                        mark.practical
                        if mark
                        else 0
                    )

                    internal = (
                        mark.internal
                        if mark
                        else 0
                    )


                    total = (
                        theory
                        + practical
                        + internal
                    )


                    exam_total += total


                    report_rows.append({

                        "Roll No":
                            student.roll_no or "",

                        "Student Name":
                            student.name,

                        "Subject":
                            subject.name,

                        "Exam":
                            exam.name,

                        "Theory":
                            theory
                            if subject.theory
                            else "",

                        "Practical":
                            practical
                            if subject.practical
                            else "",

                        "Internal":
                            internal
                            if subject.internal
                            else "",

                        "Subject Total":
                            total,

                    })


                # --------------------------------------------------
                # Exam total row
                # --------------------------------------------------

                report_rows.append({

                    "Roll No":
                        student.roll_no or "",

                    "Student Name":
                        student.name,

                    "Subject":
                        "EXAM TOTAL",

                    "Exam":
                        exam.name,

                    "Theory":
                        "",

                    "Practical":
                        "",

                    "Internal":
                        "",

                    "Subject Total":
                        exam_total,

                })


        report_df = pd.DataFrame(

            report_rows,

            columns=[

                "Roll No",

                "Student Name",

                "Subject",

                "Exam",

                "Theory",

                "Practical",

                "Internal",

                "Subject Total",

            ],

        )


        year_name = (

            str(year_value)
            .split("|", 1)[1]
            .strip()

            if "|"
            in str(year_value)

            else str(year_value)

        )


        exam_names = ", ".join(
            exam.name
            for exam in exams
        )


        message = (

            "### 📊 Consolidated Mark List\n\n"

            f"**Academic Year:** "
            f"{year_name}\n\n"

            f"**Class:** "
            f"{class_obj.name}\n\n"

            f"**Students:** "
            f"{len(students)}\n\n"

            f"**Subjects:** "
            f"{len(subjects)}\n\n"

            f"**Exams:** "
            f"{exam_names}\n\n"

            "### 📌 Report Structure\n\n"

            "**Roll No → Student → Subject → Exam "
            "→ Theory → Practical → Internal → Total**"

        )


        return (
            message,
            report_df,
        )


    except Exception as e:

        return (
            "❌ Error while generating report: "
            + str(e),
            pd.DataFrame(),
        )

    finally:

        db.close()


# ==========================================================
# LOGIN
# ==========================================================


def login(
    username,
    password,
):

    db = SessionLocal()

    try:

        teacher = (
            db.query(Teacher)
            .filter_by(
                username=(
                    username or ""
                ).strip(),
                active=True,
            )
            .first()
        )


        if not teacher:

            return (
                "❌ Invalid username or password.",
                gr.update(
                    visible=False
                ),
            )


        if not verify_password(
            password or "",
            teacher.password_hash,
        ):

            return (
                "❌ Invalid username or password.",
                gr.update(
                    visible=False
                ),
            )


        return (
            f"✅ Welcome, {teacher.name}",
            gr.update(
                visible=True
            ),
        )


    finally:

        db.close()


# ==========================================================
# CSS
# ==========================================================


css = """

.gradio-container {
    max-width: 1450px !important;
}

"""


# ==========================================================
# GRADIO APPLICATION
# ==========================================================


with gr.Blocks(
    title="School Mark Entry",
    css=css,
) as demo:


    # ======================================================
    # LOGIN
    # ======================================================

    gr.Markdown(
        "# 🏫 School Mark Entry System"
    )

    gr.Markdown(
        "### 🔐 Login"
    )


    with gr.Row():

        username = gr.Textbox(
            label="Username",
            placeholder="Enter username",
        )

        password = gr.Textbox(
            label="Password",
            type="password",
            placeholder="Enter password",
        )

        login_button = gr.Button(
            "🔐 Login",
            variant="primary",
        )


    login_message = gr.Markdown()


    # ======================================================
    # APPLICATION
    # ======================================================

    with gr.Column(
        visible=False
    ) as application:


        with gr.Tabs():


            # ==================================================
            # MASTER DATA
            # ==================================================

            with gr.Tab(
                "⚙️ Master Data"
            ):

                gr.Markdown(
                    "## ⚙️ Master Data Management"
                )


                # ==================================================
                # ACADEMIC YEAR
                # ==================================================

                gr.Markdown(
                    "### 📅 Academic Year"
                )


                with gr.Row():

                    academic_year_name = gr.Textbox(
                        label="Academic Year",
                        placeholder="Example: 2027-28",
                    )

                    add_year_button = gr.Button(
                        "➕ Add Year",
                        variant="primary",
                    )


                with gr.Row():

                    delete_year_select = gr.Dropdown(
                        choices=get_years(),
                        label="Select Year to Delete",
                    )

                    delete_year_button = gr.Button(
                        "🗑️ Delete Year",
                        variant="stop",
                    )


                year_message = gr.Markdown()


                year_table = gr.Dataframe(

                    headers=[
                        "ID",
                        "Academic Year",
                        "Status",
                    ],

                    value=get_year_list(),

                    interactive=False,

                )


                # ==================================================
                # CLASS
                # ==================================================

                gr.Markdown(
                    "### 🏫 Class"
                )


                with gr.Row():

                    class_name_input = gr.Textbox(
                        label="Class Name",
                        placeholder="Example: 12-C",
                    )

                    add_class_button = gr.Button(
                        "➕ Add Class",
                        variant="primary",
                    )


                with gr.Row():

                    delete_class_select = gr.Dropdown(
                        choices=get_classes(),
                        label="Select Class to Delete",
                    )

                    delete_class_button = gr.Button(
                        "🗑️ Delete Class",
                        variant="stop",
                    )


                class_message = gr.Markdown()


                class_table = gr.Dataframe(

                    headers=[
                        "ID",
                        "Class",
                    ],

                    value=get_class_list(),

                    interactive=False,

                )


                # ==================================================
                # SUBJECT
                # ==================================================

                gr.Markdown(
                    "### 📚 Subject"
                )


                with gr.Row():

                    subject_name_input = gr.Textbox(
                        label="Subject Name",
                        placeholder="Example: Chemistry",
                    )

                    subject_code_input = gr.Textbox(
                        label="Subject Code",
                        placeholder="Example: CHE",
                    )


                with gr.Row():

                    subject_theory = gr.Checkbox(
                        label="Theory",
                        value=True,
                    )

                    subject_practical = gr.Checkbox(
                        label="Practical",
                        value=False,
                    )

                    subject_internal = gr.Checkbox(
                        label="Internal",
                        value=True,
                    )


                with gr.Row():

                    subject_theory_max = gr.Number(
                        label="Theory Maximum",
                        value=80,
                        precision=0,
                    )

                    subject_practical_max = gr.Number(
                        label="Practical Maximum",
                        value=0,
                        precision=0,
                    )

                    subject_internal_max = gr.Number(
                        label="Internal Maximum",
                        value=20,
                        precision=0,
                    )


                with gr.Row():

                    add_subject_button = gr.Button(
                        "➕ Add Subject",
                        variant="primary",
                    )

                    delete_subject_select = gr.Dropdown(
                        choices=get_subject_choices(),
                        label="Select Subject to Delete",
                    )

                    delete_subject_button = gr.Button(
                        "🗑️ Delete Subject",
                        variant="stop",
                    )


                subject_message = gr.Markdown()


                subject_table = gr.Dataframe(

                    headers=[
                        "ID",
                        "Subject",
                        "Code",
                        "Components",
                        "Status",
                    ],

                    value=get_subject_list(),

                    interactive=False,

                )


                # ==================================================
                # EXAM
                # ==================================================

                gr.Markdown(
                    "### 📝 Exam"
                )


                with gr.Row():

                    exam_name_input = gr.Textbox(
                        label="Exam Name",
                        placeholder="Example: Monthly Test",
                    )

                    add_exam_button = gr.Button(
                        "➕ Add Exam",
                        variant="primary",
                    )


                with gr.Row():

                    delete_exam_select = gr.Dropdown(
                        choices=get_exams(),
                        label="Select Exam to Delete",
                    )

                    delete_exam_button = gr.Button(
                        "🗑️ Delete Exam",
                        variant="stop",
                    )


                exam_message = gr.Markdown()


                exam_table = gr.Dataframe(

                    headers=[
                        "ID",
                        "Exam",
                        "Status",
                    ],

                    value=get_exam_list(),

                    interactive=False,

                )


            # ==================================================
            # STUDENT MANAGEMENT
            # ==================================================

            with gr.Tab(
                "👨‍🎓 Student Management"
            ):

                gr.Markdown(
                    "## 👨‍🎓 Student Management"
                )


                with gr.Row():

                    admission_no = gr.Textbox(
                        label="Admission No",
                    )

                    roll_no = gr.Textbox(
                        label="Roll No",
                    )

                    student_name = gr.Textbox(
                        label="Student Name",
                    )

                    student_class = gr.Dropdown(
                        choices=get_classes(),
                        label="Class",
                    )


                with gr.Row():

                    add_student_button = gr.Button(
                        "➕ Add Student",
                        variant="primary",
                    )

                    delete_student_select = gr.Dropdown(
                        choices=get_student_delete_choices(),
                        label="Select Student to Delete",
                    )

                    delete_student_button = gr.Button(
                        "🗑️ Delete Student",
                        variant="stop",
                    )


                student_message = gr.Markdown()


                student_table = gr.Dataframe(

                    headers=[
                        "ID",
                        "Admission No",
                        "Roll No",
                        "Student Name",
                        "Class",
                    ],

                    value=get_student_list(),

                    interactive=False,

                )


            # ==================================================
            # MARK ENTRY
            # ==================================================

            with gr.Tab(
                "📝 Mark Entry"
            ):

                gr.Markdown(
                    "## 📝 Mark Entry"
                )


                with gr.Row():

                    mark_year = gr.Dropdown(
                        choices=get_years(),
                        label="Academic Year",
                    )

                    mark_class = gr.Dropdown(
                        choices=get_classes(),
                        label="Class",
                    )

                    mark_exam = gr.Dropdown(
                        choices=get_exams(),
                        label="Exam",
                    )

                    mark_subject = gr.Dropdown(
                        choices=[],
                        label="Subject",
                    )


                mark_class.change(

                    get_subjects_for_class,

                    inputs=mark_class,

                    outputs=mark_subject,

                )


                mark_pattern = gr.Markdown()


                load_button = gr.Button(
                    "📥 Load Students"
                )


                marks_table = gr.Dataframe(
                    interactive=True
                )


                load_button.click(

                    load_marks,

                    inputs=[

                        mark_class,

                        mark_year,

                        mark_exam,

                        mark_subject,

                    ],

                    outputs=[

                        marks_table,

                        mark_pattern,

                    ],

                )


                save_button = gr.Button(
                    "💾 Save Marks",
                    variant="primary",
                )


                save_message = gr.Markdown()


                save_button.click(

                    save_marks,

                    inputs=[

                        mark_class,

                        mark_year,

                        mark_exam,

                        mark_subject,

                        marks_table,

                    ],

                    outputs=save_message,

                )


            # ==================================================
            # VIEW MARKS
            # ==================================================

            with gr.Tab(
                "👁️ View Marks"
            ):

                gr.Markdown(
                    "## 👁️ Subject-wise Mark View"
                )


                with gr.Row():

                    view_year = gr.Dropdown(
                        choices=get_years(),
                        label="Academic Year",
                    )

                    view_class = gr.Dropdown(
                        choices=get_classes(),
                        label="Class",
                    )

                    view_exam = gr.Dropdown(
                        choices=get_exams(),
                        label="Exam",
                    )

                    view_subject = gr.Dropdown(
                        choices=[],
                        label="Subject",
                    )


                view_class.change(

                    get_subjects_for_class,

                    inputs=view_class,

                    outputs=view_subject,

                )


                view_button = gr.Button(
                    "👁️ View Marks"
                )


                view_pattern = gr.Markdown()


                view_table = gr.Dataframe(
                    interactive=False
                )


                view_button.click(

                    load_marks,

                    inputs=[

                        view_class,

                        view_year,

                        view_exam,

                        view_subject,

                    ],

                    outputs=[

                        view_table,

                        view_pattern,

                    ],

                )


            # ==================================================
            # CONSOLIDATED REPORT
            # ==================================================

            with gr.Tab(
                "📊 Mark List / Print"
            ):

                gr.Markdown(
                    "## 📊 Consolidated Mark List"
                )


                gr.Markdown(
                    """
Select **Academic Year + Class + Exam**.

The report will show:

**Roll No → Student → Subject → Exam → Theory → Practical → Internal → Total**
"""
                )


                with gr.Row():

                    list_year = gr.Dropdown(
                        choices=get_years(),
                        label="Academic Year",
                    )

                    list_class = gr.Dropdown(
                        choices=get_classes(),
                        label="Class",
                    )

                    list_exam = gr.Dropdown(
                        choices=get_all_exams(),
                        label="Exam",
                    )


                consolidated_button = gr.Button(

                    "📋 View Consolidated Mark List",

                    variant="primary",

                )


                consolidated_message = gr.Markdown()


                consolidated_table = gr.Dataframe(

                    interactive=False,

                    wrap=True,

                )


                gr.Markdown(
                    """
### 🖨️ Print

After the report appears,
use **Ctrl + P** in your browser to print.
"""
                )


                consolidated_button.click(

                    generate_consolidated_report,

                    inputs=[

                        list_year,

                        list_class,

                        list_exam,

                    ],

                    outputs=[

                        consolidated_message,

                        consolidated_table,

                    ],

                )


    # ======================================================
    # MASTER DATA EVENTS
    # ======================================================

    # ------------------------------------------------------
    # ADD YEAR
    #
    # Outputs:
    # 1 message
    # 2 table
    # 3 delete year
    # 4 mark year
    # 5 view year
    # 6 list year
    # ------------------------------------------------------

    add_year_button.click(

        add_academic_year,

        inputs=academic_year_name,

        outputs=[

            year_message,

            year_table,

            delete_year_select,

            mark_year,

            view_year,

            list_year,

        ],

    )


    # ------------------------------------------------------
    # DELETE YEAR
    # ------------------------------------------------------

    delete_year_button.click(

        delete_academic_year,

        inputs=delete_year_select,

        outputs=[

            year_message,

            year_table,

            delete_year_select,

            mark_year,

            view_year,

            list_year,

        ],

    )


    # ------------------------------------------------------
    # ADD CLASS
    #
    # Outputs:
    # 1 message
    # 2 table
    # 3 delete class
    # 4 student class
    # 5 mark class
    # 6 view class
    # 7 list class
    # ------------------------------------------------------

    add_class_button.click(

        add_class,

        inputs=class_name_input,

        outputs=[

            class_message,

            class_table,

            delete_class_select,

            student_class,

            mark_class,

            view_class,

            list_class,

        ],

    )


    # ------------------------------------------------------
    # DELETE CLASS
    # ------------------------------------------------------

    delete_class_button.click(

        delete_class,

        inputs=delete_class_select,

        outputs=[

            class_message,

            class_table,

            delete_class_select,

            student_class,

            mark_class,

            view_class,

            list_class,

        ],

    )


    # ------------------------------------------------------
    # ADD SUBJECT
    # ------------------------------------------------------

    add_subject_button.click(

        add_subject,

        inputs=[

            subject_name_input,

            subject_code_input,

            subject_theory,

            subject_practical,

            subject_internal,

            subject_theory_max,

            subject_practical_max,

            subject_internal_max,

        ],

        outputs=[

            subject_message,

            subject_table,

            delete_subject_select,

        ],

    )


    # ------------------------------------------------------
    # DELETE SUBJECT
    # ------------------------------------------------------

    delete_subject_button.click(

        delete_subject,

        inputs=delete_subject_select,

        outputs=[

            subject_message,

            subject_table,

            delete_subject_select,

        ],

    )


    # ------------------------------------------------------
    # ADD EXAM
    # ------------------------------------------------------

    add_exam_button.click(

        add_exam,

        inputs=exam_name_input,

        outputs=[

            exam_message,

            exam_table,

            delete_exam_select,

            mark_exam,

            view_exam,

            list_exam,

        ],

    )


    # ------------------------------------------------------
    # DELETE EXAM
    # ------------------------------------------------------

    delete_exam_button.click(

        delete_exam,

        inputs=delete_exam_select,

        outputs=[

            exam_message,

            exam_table,

            delete_exam_select,

            mark_exam,

            view_exam,

            list_exam,

        ],

    )


    # ======================================================
    # LOGIN EVENT
    # ======================================================

    login_button.click(

        login,

        inputs=[

            username,

            password,

        ],

        outputs=[

            login_message,

            application,

        ],

    )


    # ======================================================
    # LOGIN INFORMATION
    # ======================================================

    gr.Markdown(
        "**Initial Login:** `admin` / `Admin@123`"
    )


# ==========================================================
# START SERVER
# ==========================================================


if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "7860",
        )
    )


    demo.launch(

        server_name="0.0.0.0",

        server_port=port,

    )
```
