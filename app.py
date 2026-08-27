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
    UniqueConstraint
)

from sqlalchemy.orm import (
    declarative_base,
    sessionmaker
)


# ==========================================================
# SCHOOL MARK ENTRY SYSTEM
# FINAL VERSION
# ==========================================================


# ==========================================================
# DATABASE CONFIGURATION
# ==========================================================

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[11:]


if DATABASE_URL:

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True
    )

else:

    engine = create_engine(
        "sqlite:///school_marks.db",
        connect_args={
            "check_same_thread": False
        }
    )


SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False
)

Base = declarative_base()


# ==========================================================
# DATABASE TABLES
# ==========================================================


class AcademicYear(Base):

    __tablename__ = "academic_years"

    id = Column(
        Integer,
        primary_key=True
    )

    name = Column(
        String(50),
        unique=True,
        nullable=False
    )

    active = Column(
        Boolean,
        default=True
    )


class ClassSection(Base):

    __tablename__ = "classes"

    id = Column(
        Integer,
        primary_key=True
    )

    name = Column(
        String(50),
        unique=True,
        nullable=False
    )

    active = Column(
        Boolean,
        default=True
    )


class Student(Base):

    __tablename__ = "students"

    id = Column(
        Integer,
        primary_key=True
    )

    admission_no = Column(
        String(50),
        unique=True,
        nullable=False
    )

    roll_no = Column(
        String(50)
    )

    name = Column(
        String(200),
        nullable=False
    )

    class_id = Column(
        Integer,
        ForeignKey("classes.id"),
        nullable=False
    )

    active = Column(
        Boolean,
        default=True
    )


class Teacher(Base):

    __tablename__ = "teachers"

    id = Column(
        Integer,
        primary_key=True
    )

    username = Column(
        String(100),
        unique=True,
        nullable=False
    )

    name = Column(
        String(200),
        nullable=False
    )

    password_hash = Column(
        String(500),
        nullable=False
    )

    role = Column(
        String(20),
        default="teacher"
    )

    active = Column(
        Boolean,
        default=True
    )


class Subject(Base):

    __tablename__ = "subjects"

    id = Column(
        Integer,
        primary_key=True
    )

    name = Column(
        String(200),
        nullable=False
    )

    code = Column(
        String(50),
        unique=True,
        nullable=False
    )

    theory = Column(
        Boolean,
        default=True
    )

    practical = Column(
        Boolean,
        default=False
    )

    internal = Column(
        Boolean,
        default=True
    )

    theory_max = Column(
        Integer,
        default=0
    )

    practical_max = Column(
        Integer,
        default=0
    )

    internal_max = Column(
        Integer,
        default=0
    )

    active = Column(
        Boolean,
        default=True
    )


class ClassSubject(Base):

    __tablename__ = "class_subjects"

    id = Column(
        Integer,
        primary_key=True
    )

    class_id = Column(
        Integer,
        ForeignKey("classes.id"),
        nullable=False
    )

    subject_id = Column(
        Integer,
        ForeignKey("subjects.id"),
        nullable=False
    )

    __table_args__ = (
        UniqueConstraint(
            "class_id",
            "subject_id",
            name="uq_class_subject"
        ),
    )


class Exam(Base):

    __tablename__ = "exams"

    id = Column(
        Integer,
        primary_key=True
    )

    name = Column(
        String(100),
        unique=True,
        nullable=False
    )

    active = Column(
        Boolean,
        default=True
    )


class Mark(Base):

    __tablename__ = "marks"

    id = Column(
        Integer,
        primary_key=True
    )

    academic_year_id = Column(
        Integer,
        ForeignKey("academic_years.id"),
        nullable=False
    )

    exam_id = Column(
        Integer,
        ForeignKey("exams.id"),
        nullable=False
    )

    student_id = Column(
        Integer,
        ForeignKey("students.id"),
        nullable=False
    )

    subject_id = Column(
        Integer,
        ForeignKey("subjects.id"),
        nullable=False
    )

    theory = Column(
        Integer,
        default=0
    )

    practical = Column(
        Integer,
        default=0
    )

    internal = Column(
        Integer,
        default=0
    )

    total = Column(
        Integer,
        default=0
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow
    )

    __table_args__ = (
        UniqueConstraint(
            "academic_year_id",
            "exam_id",
            "student_id",
            "subject_id",
            name="uq_student_exam_subject"
        ),
    )


# ==========================================================
# CREATE TABLES
# ==========================================================

Base.metadata.create_all(engine)


# ==========================================================
# PASSWORD FUNCTIONS
# ==========================================================

def hash_password(password):

    salt = secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        120000
    ).hex()

    return salt + "$" + digest


def verify_password(password, stored):

    try:

        salt, digest = stored.split(
            "$",
            1
        )

        check = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode(),
            salt.encode(),
            120000
        ).hex()

        return secrets.compare_digest(
            check,
            digest
        )

    except Exception:

        return False


# ==========================================================
# GENERAL HELPERS
# ==========================================================

def parse_id(value):

    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    try:

        return int(
            text.split(
                "|",
                1
            )[0].strip()
        )

    except Exception:

        return None


def clean_text(value):

    return str(
        value or ""
    ).strip()


def display_name(value):

    text = str(
        value or ""
    )

    if "|" in text:

        return text.split(
            "|",
            1
        )[1].strip()

    return text.strip()


# ==========================================================
# DROPDOWN FUNCTIONS
# ==========================================================

def get_classes():

    db = SessionLocal()

    try:

        rows = (
            db.query(ClassSection)
            .filter(
                ClassSection.active == True
            )
            .order_by(
                ClassSection.name
            )
            .all()
        )

        return [
            f"{x.id} | {x.name}"
            for x in rows
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
            f"{x.id} | {x.name}"
            for x in rows
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
            f"{x.id} | {x.name}"
            for x in rows
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

        result = [
            "ALL | All Exams"
        ]

        result.extend(
            [
                f"{x.id} | {x.name}"
                for x in rows
            ]
        )

        return result

    finally:

        db.close()


def get_subjects():

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
            f"{x.id} | {x.name}"
            for x in rows
        ]

    finally:

        db.close()


# ==========================================================
# SUBJECTS FOR CLASS
# ==========================================================

def get_subjects_for_class(class_value):

    class_id = parse_id(
        class_value
    )

    if not class_id:

        return gr.Dropdown(
            choices=[],
            value=None
        )

    db = SessionLocal()

    try:

        subjects = (
            db.query(Subject)
            .join(
                ClassSubject,
                ClassSubject.subject_id == Subject.id
            )
            .filter(
                ClassSubject.class_id == class_id,
                Subject.active == True
            )
            .order_by(
                Subject.name
            )
            .all()
        )

        choices = [
            f"{x.id} | {x.name}"
            for x in subjects
        ]

        return gr.Dropdown(
            choices=choices,
            value=None
        )

    finally:

        db.close()


# ==========================================================
# STUDENTS FOR CLASS
# ==========================================================

def get_students_for_class(class_value):

    class_id = parse_id(
        class_value
    )

    if not class_id:

        return gr.Dropdown(
            choices=[],
            value=None
        )

    db = SessionLocal()

    try:

        students = (
            db.query(Student)
            .filter(
                Student.class_id == class_id,
                Student.active == True
            )
            .order_by(
                Student.roll_no,
                Student.name
            )
            .all()
        )

        choices = [
            f"{x.id} | {x.roll_no or '-'} | {x.name}"
            for x in students
        ]

        return gr.Dropdown(
            choices=choices,
            value=None
        )

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
                ClassSection
            )
            .join(
                ClassSection,
                Student.class_id == ClassSection.id
            )
            .filter(
                Student.active == True,
                ClassSection.active == True
            )
            .order_by(
                ClassSection.name,
                Student.roll_no,
                Student.name
            )
            .all()
        )

        return [
            [
                student.id,
                student.admission_no,
                student.roll_no or "",
                student.name,
                cls.name
            ]
            for student, cls in rows
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
    class_value
):

    admission_no = clean_text(
        admission_no
    )

    roll_no = clean_text(
        roll_no
    )

    student_name = clean_text(
        student_name
    )

    class_id = parse_id(
        class_value
    )

    if not admission_no:

        return (
            "❌ Admission No is required.",
            get_student_list(),
            get_students_for_class(
                class_value
            )
        )

    if not student_name:

        return (
            "❌ Student Name is required.",
            get_student_list(),
            get_students_for_class(
                class_value
            )
        )

    if not class_id:

        return (
            "❌ Please select Class.",
            get_student_list(),
            get_students_for_class(
                class_value
            )
        )

    db = SessionLocal()

    try:

        old = (
            db.query(Student)
            .filter(
                Student.admission_no == admission_no
            )
            .first()
        )

        if old:

            if old.active:

                return (
                    "❌ This Admission No already exists.",
                    get_student_list(),
                    get_students_for_class(
                        class_value
                    )
                )

            old.active = True
            old.roll_no = roll_no
            old.name = student_name
            old.class_id = class_id

            db.commit()

            return (
                "✅ Student restored successfully.",
                get_student_list(),
                get_students_for_class(
                    class_value
                )
            )

        student = Student(
            admission_no=admission_no,
            roll_no=roll_no,
            name=student_name,
            class_id=class_id,
            active=True
        )

        db.add(student)

        db.commit()

        return (
            "✅ Student added successfully.",
            get_student_list(),
            get_students_for_class(
                class_value
            )
        )

    except Exception as e:

        db.rollback()

        return (
            "❌ Error: " + str(e),
            get_student_list(),
            get_students_for_class(
                class_value
            )
        )

    finally:

        db.close()


# ==========================================================
# DELETE STUDENT
# ==========================================================

def delete_student(
    class_value,
    student_value
):

    class_id = parse_id(
        class_value
    )

    student_id = parse_id(
        student_value
    )

    if not class_id:

        return (
            "❌ Please select Class.",
            get_student_list(),
            gr.Dropdown(
                choices=[],
                value=None
            )
        )

    if not student_id:

        return (
            "❌ Please select Student.",
            get_student_list(),
            get_students_for_class(
                class_value
            )
        )

    db = SessionLocal()

    try:

        student = (
            db.query(Student)
            .filter(
                Student.id == student_id,
                Student.class_id == class_id
            )
            .first()
        )

        if not student:

            return (
                "❌ Student not found.",
                get_student_list(),
                get_students_for_class(
                    class_value
                )
            )

        student.active = False

        db.commit()

        return (
            f"✅ Student '{student.name}' deleted successfully.",
            get_student_list(),
            get_students_for_class(
                class_value
            )
        )

    except Exception as e:

        db.rollback()

        return (
            "❌ Error while deleting student: " + str(e),
            get_student_list(),
            get_students_for_class(
                class_value
            )
        )

    finally:

        db.close()


# ==========================================================
# ADD ACADEMIC YEAR
# ==========================================================

def add_academic_year(year_name):

    year_name = clean_text(
        year_name
    )

    if not year_name:

        return (
            "❌ Academic Year is required.",
            get_years()
        )

    db = SessionLocal()

    try:

        old = (
            db.query(AcademicYear)
            .filter(
                AcademicYear.name == year_name
            )
            .first()
        )

        if old:

            if old.active:

                return (
                    "❌ Academic Year already exists.",
                    get_years()
                )

            old.active = True

            db.commit()

            return (
                "✅ Academic Year restored.",
                get_years()
            )

        db.add(
            AcademicYear(
                name=year_name,
                active=True
            )
        )

        db.commit()

        return (
            "✅ Academic Year added successfully.",
            get_years()
        )

    except Exception as e:

        db.rollback()

        return (
            "❌ Error: " + str(e),
            get_years()
        )

    finally:

        db.close()


# ==========================================================
# DELETE ACADEMIC YEAR
# ==========================================================

def delete_academic_year(year_value):

    year_id = parse_id(
        year_value
    )

    if not year_id:

        return (
            "❌ Please select Academic Year.",
            get_years()
        )

    db = SessionLocal()

    try:

        obj = db.get(
            AcademicYear,
            year_id
        )

        if not obj:

            return (
                "❌ Academic Year not found.",
                get_years()
            )

        obj.active = False

        db.commit()

        return (
            f"✅ Academic Year '{obj.name}' deleted.",
            get_years()
        )

    except Exception as e:

        db.rollback()

        return (
            "❌ Error: " + str(e),
            get_years()
        )

    finally:

        db.close()


# ==========================================================
# ADD CLASS
# ==========================================================

def add_class(class_name):

    class_name = clean_text(
        class_name
    )

    if not class_name:

        return (
            "❌ Class name is required.",
            get_classes()
        )

    db = SessionLocal()

    try:

        old = (
            db.query(ClassSection)
            .filter(
                ClassSection.name == class_name
            )
            .first()
        )

        if old:

            if old.active:

                return (
                    "❌ Class already exists.",
                    get_classes()
                )

            old.active = True

            subjects = (
                db.query(Subject)
                .filter(
                    Subject.active == True
                )
                .all()
            )

            for subject in subjects:

                exists = (
                    db.query(ClassSubject)
                    .filter_by(
                        class_id=old.id,
                        subject_id=subject.id
                    )
                    .first()
                )

                if not exists:

                    db.add(
                        ClassSubject(
                            class_id=old.id,
                            subject_id=subject.id
                        )
                    )

            db.commit()

            return (
                "✅ Class restored.",
                get_classes()
            )

        obj = ClassSection(
            name=class_name,
            active=True
        )

        db.add(obj)

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
                    class_id=obj.id,
                    subject_id=subject.id
                )
            )

        db.commit()

        return (
            "✅ Class added successfully.",
            get_classes()
        )

    except Exception as e:

        db.rollback()

        return (
            "❌ Error: " + str(e),
            get_classes()
        )

    finally:

        db.close()


# ==========================================================
# DELETE CLASS
# ==========================================================

def delete_class(class_value):

    class_id = parse_id(
        class_value
    )

    if not class_id:

        return (
            "❌ Please select Class.",
            get_classes()
        )

    db = SessionLocal()

    try:

        obj = db.get(
            ClassSection,
            class_id
        )

        if not obj:

            return (
                "❌ Class not found.",
                get_classes()
            )

        obj.active = False

        students = (
            db.query(Student)
            .filter(
                Student.class_id == class_id
            )
            .all()
        )

        for student in students:

            student.active = False

        db.commit()

        return (
            f"✅ Class '{obj.name}' deleted.",
            get_classes()
        )

    except Exception as e:

        db.rollback()

        return (
            "❌ Error: " + str(e),
            get_classes()
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
    internal_max
):

    subject_name = clean_text(
        subject_name
    )

    subject_code = clean_text(
        subject_code
    )

    if not subject_name:

        return (
            "❌ Subject Name is required.",
            get_subjects()
        )

    if not subject_code:

        return (
            "❌ Subject Code is required.",
            get_subjects()
        )

    try:

        theory_max = int(
            theory_max or 0
        )

        practical_max = int(
            practical_max or 0
        )

        internal_max = int(
            internal_max or 0
        )

    except Exception:

        return (
            "❌ Maximum marks must be numbers.",
            get_subjects()
        )

    if not theory and not practical and not internal:

        return (
            "❌ Select at least one component.",
            get_subjects()
        )

    db = SessionLocal()

    try:

        old = (
            db.query(Subject)
            .filter(
                Subject.code == subject_code
            )
            .first()
        )

        if old:

            if old.active:

                return (
                    "❌ Subject Code already exists.",
                    get_subjects()
                )

            old.active = True
            old.name = subject_name
            old.theory = theory
            old.practical = practical
            old.internal = internal
            old.theory_max = theory_max
            old.practical_max = practical_max
            old.internal_max = internal_max

            db.commit()

            return (
                "✅ Subject restored.",
                get_subjects()
            )

        name_exists = (
            db.query(Subject)
            .filter(
                Subject.name == subject_name,
                Subject.active == True
            )
            .first()
        )

        if name_exists:

            return (
                "❌ Subject Name already exists.",
                get_subjects()
            )

        obj = Subject(
            name=subject_name,
            code=subject_code,
            theory=theory,
            practical=practical,
            internal=internal,
            theory_max=theory_max,
            practical_max=practical_max,
            internal_max=internal_max,
            active=True
        )

        db.add(obj)

        db.flush()

        classes = (
            db.query(ClassSection)
            .filter(
                ClassSection.active == True
            )
            .all()
        )

        for cls in classes:

            db.add(
                ClassSubject(
                    class_id=cls.id,
                    subject_id=obj.id
                )
            )

        db.commit()

        return (
            "✅ Subject added successfully.",
            get_subjects()
        )

    except Exception as e:

        db.rollback()

        return (
            "❌ Error: " + str(e),
            get_subjects()
        )

    finally:

        db.close()


# ==========================================================
# DELETE SUBJECT
# ==========================================================

def delete_subject(subject_value):

    subject_id = parse_id(
        subject_value
    )

    if not subject_id:

        return (
            "❌ Please select Subject.",
            get_subjects()
        )

    db = SessionLocal()

    try:

        obj = db.get(
            Subject,
            subject_id
        )

        if not obj:

            return (
                "❌ Subject not found.",
                get_subjects()
            )

        obj.active = False

        db.commit()

        return (
            f"✅ Subject '{obj.name}' deleted.",
            get_subjects()
        )

    except Exception as e:

        db.rollback()

        return (
            "❌ Error: " + str(e),
            get_subjects()
        )

    finally:

        db.close()


# ==========================================================
# ADD EXAM
# ==========================================================

def add_exam(exam_name):

    exam_name = clean_text(
        exam_name
    )

    if not exam_name:

        return (
            "❌ Exam Name is required.",
            get_exams(),
            get_all_exams()
        )

    db = SessionLocal()

    try:

        old = (
            db.query(Exam)
            .filter(
                Exam.name == exam_name
            )
            .first()
        )

        if old:

            if old.active:

                return (
                    "❌ Exam already exists.",
                    get_exams(),
                    get_all_exams()
                )

            old.active = True

            db.commit()

            return (
                "✅ Exam restored.",
                get_exams(),
                get_all_exams()
            )

        db.add(
            Exam(
                name=exam_name,
                active=True
            )
        )

        db.commit()

        return (
            "✅ Exam added successfully.",
            get_exams(),
            get_all_exams()
        )

    except Exception as e:

        db.rollback()

        return (
            "❌ Error: " + str(e),
            get_exams(),
            get_all_exams()
        )

    finally:

        db.close()


# ==========================================================
# DELETE EXAM
# ==========================================================

def delete_exam(exam_value):

    exam_id = parse_id(
        exam_value
    )

    if not exam_id:

        return (
            "❌ Please select Exam.",
            get_exams(),
            get_all_exams()
        )

    db = SessionLocal()

    try:

        obj = db.get(
            Exam,
            exam_id
        )

        if not obj:

            return (
                "❌ Exam not found.",
                get_exams(),
                get_all_exams()
            )

        obj.active = False

        db.commit()

        return (
            f"✅ Exam '{obj.name}' deleted.",
            get_exams(),
            get_all_exams()
        )

    except Exception as e:

        db.rollback()

        return (
            "❌ Error: " + str(e),
            get_exams(),
            get_all_exams()
        )

    finally:

        db.close()


# ==========================================================
# USER / TEACHER MANAGEMENT
# ==========================================================

def get_teachers():

    db = SessionLocal()

    try:

        rows = (
            db.query(Teacher)
            .filter(
                Teacher.active == True
            )
            .order_by(
                Teacher.username
            )
            .all()
        )

        return [
            [
                x.id,
                x.username,
                x.name,
                x.role
            ]
            for x in rows
        ]

    finally:

        db.close()


# ==========================================================
# ADD TEACHER / USER
# ==========================================================

def add_teacher(
    username,
    teacher_name,
    password,
    confirm_password
):

    username = clean_text(
        username
    )

    teacher_name = clean_text(
        teacher_name
    )

    password = str(
        password or ""
    ).strip()

    confirm_password = str(
        confirm_password or ""
    ).strip()

    if not username:

        return (
            "❌ Username is required.",
            get_teachers()
        )

    if not teacher_name:

        return (
            "❌ User Name is required.",
            get_teachers()
        )

    if not password:

        return (
            "❌ Password is required.",
            get_teachers()
        )

    if not confirm_password:

        return (
            "❌ Confirm Password is required.",
            get_teachers()
        )

    if password != confirm_password:

        return (
            "❌ Password and Confirm Password do not match.",
            get_teachers()
        )

    if len(password) < 6:

        return (
            "❌ Password must contain at least 6 characters.",
            get_teachers()
        )

    db = SessionLocal()

    try:

        old = (
            db.query(Teacher)
            .filter(
                Teacher.username == username
            )
            .first()
        )

        if old:

            if old.active:

                return (
                    "❌ Username already exists.",
                    get_teachers()
                )

            old.active = True
            old.name = teacher_name
            old.password_hash = hash_password(
                password
            )
            old.role = "teacher"

            db.commit()

            return (
                "✅ User restored successfully.",
                get_teachers()
            )

        teacher = Teacher(
            username=username,
            name=teacher_name,
            password_hash=hash_password(
                password
            ),
            role="teacher",
            active=True
        )

        db.add(teacher)

        db.commit()

        return (
            "✅ User created successfully.",
            get_teachers()
        )

    except Exception as e:

        db.rollback()

        return (
            "❌ Error: " + str(e),
            get_teachers()
        )

    finally:

        db.close()


# ==========================================================
# DELETE TEACHER
# ==========================================================

def delete_teacher(username):

    username = clean_text(
        username
    )

    if not username:

        return (
            "❌ Please enter Username.",
            get_teachers()
        )

    if username.lower() == "admin":

        return (
            "❌ Main admin account cannot be deleted.",
            get_teachers()
        )

    db = SessionLocal()

    try:

        teacher = (
            db.query(Teacher)
            .filter(
                Teacher.username == username,
                Teacher.active == True
            )
            .first()
        )

        if not teacher:

            return (
                "❌ User not found.",
                get_teachers()
            )

        teacher.active = False

        db.commit()

        return (
            f"✅ User '{username}' deleted.",
            get_teachers()
        )

    except Exception as e:

        db.rollback()

        return (
            "❌ Error: " + str(e),
            get_teachers()
        )

    finally:

        db.close()


# ==========================================================
# SEED DATABASE
# ==========================================================

def seed_database():

    db = SessionLocal()

    try:

        if not db.query(AcademicYear).first():

            db.add(
                AcademicYear(
                    name="2026-27",
                    active=True
                )
            )

        if not db.query(ClassSection).first():

            db.add_all(
                [
                    ClassSection(name="10-A"),
                    ClassSection(name="10-B"),
                    ClassSection(name="11-A"),
                    ClassSection(name="11-B"),
                    ClassSection(name="12-A"),
                    ClassSection(name="12-B")
                ]
            )

        if not db.query(Exam).first():

            db.add_all(
                [
                    Exam(name="Unit Test 1"),
                    Exam(name="Quarterly"),
                    Exam(name="Half-Yearly"),
                    Exam(name="Annual")
                ]
            )

        if not db.query(Subject).first():

            db.add_all(
                [
                    Subject(
                        name="Tamil",
                        code="TAM",
                        theory=True,
                        practical=False,
                        internal=True,
                        theory_max=80,
                        internal_max=20
                    ),

                    Subject(
                        name="English",
                        code="ENG",
                        theory=True,
                        practical=False,
                        internal=True,
                        theory_max=80,
                        internal_max=20
                    ),

                    Subject(
                        name="Mathematics",
                        code="MAT",
                        theory=True,
                        practical=False,
                        internal=True,
                        theory_max=80,
                        internal_max=20
                    ),

                    Subject(
                        name="Physics",
                        code="PHY",
                        theory=True,
                        practical=True,
                        internal=True,
                        theory_max=70,
                        practical_max=20,
                        internal_max=10
                    ),

                    Subject(
                        name="Chemistry",
                        code="CHE",
                        theory=True,
                        practical=True,
                        internal=True,
                        theory_max=70,
                        practical_max=20,
                        internal_max=10
                    ),

                    Subject(
                        name="Computer Science",
                        code="CS",
                        theory=True,
                        practical=True,
                        internal=True,
                        theory_max=70,
                        practical_max=20,
                        internal_max=10
                    )
                ]
            )

        admin = (
            db.query(Teacher)
            .filter(
                Teacher.username == "admin"
            )
            .first()
        )

        if not admin:

            db.add(
                Teacher(
                    username="admin",
                    name="Administrator",
                    password_hash=hash_password(
                        "Admin@123"
                    ),
                    role="admin",
                    active=True
                )
            )

        elif not admin.active:

            admin.active = True
            admin.role = "admin"

        db.commit()

        classes = (
            db.query(ClassSection)
            .filter(
                ClassSection.active == True
            )
            .all()
        )

        subjects = (
            db.query(Subject)
            .filter(
                Subject.active == True
            )
            .all()
        )

        for cls in classes:

            for subject in subjects:

                exists = (
                    db.query(ClassSubject)
                    .filter_by(
                        class_id=cls.id,
                        subject_id=subject.id
                    )
                    .first()
                )

                if not exists:

                    db.add(
                        ClassSubject(
                            class_id=cls.id,
                            subject_id=subject.id
                        )
                    )

        db.commit()

    except Exception:

        db.rollback()

        raise

    finally:

        db.close()


seed_database()


# ==========================================================
# MARK ENTRY - LOAD
# ==========================================================

def load_marks(
    class_value,
    year_value,
    exam_value,
    subject_value
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

    if not all(
        [
            class_id,
            year_id,
            exam_id,
            subject_id
        ]
    ):

        return (
            [],
            "❌ Please select Class, Academic Year, Exam and Subject."
        )

    db = SessionLocal()

    try:

        subject = db.get(
            Subject,
            subject_id
        )

        if not subject or not subject.active:

            return (
                [],
                "❌ Subject not found."
            )

        students = (
            db.query(Student)
            .filter(
                Student.class_id == class_id,
                Student.active == True
            )
            .order_by(
                Student.roll_no,
                Student.name
            )
            .all()
        )

        headers = [
            "ID",
            "Roll No",
            "Student Name"
        ]

        if subject.theory:
            headers.append("Theory")

        if subject.practical:
            headers.append("Practical")

        if subject.internal:
            headers.append("Internal")

        headers.append("Total")

        rows = []

        for student in students:

            mark = (
                db.query(Mark)
                .filter_by(
                    academic_year_id=year_id,
                    exam_id=exam_id,
                    student_id=student.id,
                    subject_id=subject_id
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
                student.name
            ]

            if subject.theory:
                row.append(theory)

            if subject.practical:
                row.append(practical)

            if subject.internal:
                row.append(internal)

            row.append(total)

            rows.append(row)

        pattern = []

        if subject.theory:

            pattern.append(
                f"Theory / {subject.theory_max}"
            )

        if subject.practical:

            pattern.append(
                f"Practical / {subject.practical_max}"
            )

        if subject.internal:

            pattern.append(
                f"Internal / {subject.internal_max}"
            )

        return (
            rows,
            "**Mark Pattern:** "
            + " + ".join(pattern)
        )

    finally:

        db.close()


# ==========================================================
# SAVE MARKS
# ==========================================================

def save_marks(
    class_value,
    year_value,
    exam_value,
    subject_value,
    table_data
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

        return "❌ No student data found."

    db = SessionLocal()

    try:

        subject = db.get(
            Subject,
            subject_id
        )

        if not subject:

            return "❌ Subject not found."

        if hasattr(
            table_data,
            "values"
        ):

            rows = table_data.values.tolist()

        else:

            rows = table_data

        if not rows:

            return "❌ No student rows found."

        saved_count = 0

        for row in rows:

            if not row or len(row) < 4:
                continue

            try:

                student_id = int(
                    row[0]
                )

            except Exception:

                continue

            position = 3

            theory = 0
            practical = 0
            internal = 0

            try:

                if subject.theory:

                    if len(row) > position:

                        if row[position] not in [
                            None,
                            ""
                        ]:

                            theory = int(
                                float(
                                    row[position]
                                )
                            )

                    position += 1

                if subject.practical:

                    if len(row) > position:

                        if row[position] not in [
                            None,
                            ""
                        ]:

                            practical = int(
                                float(
                                    row[position]
                                )
                            )

                    position += 1

                if subject.internal:

                    if len(row) > position:

                        if row[position] not in [
                            None,
                            ""
                        ]:

                            internal = int(
                                float(
                                    row[position]
                                )
                            )

                    position += 1

            except Exception:

                return (
                    f"❌ Invalid mark value "
                    f"for student ID {student_id}."
                )

            if theory < 0:

                return (
                    f"❌ Theory mark cannot be negative "
                    f"for student ID {student_id}."
                )

            if practical < 0:

                return (
                    f"❌ Practical mark cannot be negative "
                    f"for student ID {student_id}."
                )

            if internal < 0:

                return (
                    f"❌ Internal mark cannot be negative "
                    f"for student ID {student_id}."
                )

            if (
                subject.theory
                and theory > subject.theory_max
            ):

                return (
                    f"❌ Theory mark exceeds maximum "
                    f"({subject.theory_max}) "
                    f"for student ID {student_id}."
                )

            if (
                subject.practical
                and practical > subject.practical_max
            ):

                return (
                    f"❌ Practical mark exceeds maximum "
                    f"({subject.practical_max}) "
                    f"for student ID {student_id}."
                )

            if (
                subject.internal
                and internal > subject.internal_max
            ):

                return (
                    f"❌ Internal mark exceeds maximum "
                    f"({subject.internal_max}) "
                    f"for student ID {student_id}."
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
                    subject_id=subject_id
                )
                .first()
            )

            if mark is None:

                mark = Mark(
                    academic_year_id=year_id,
                    exam_id=exam_id,
                    student_id=student_id,
                    subject_id=subject_id
                )

                db.add(mark)

            mark.theory = theory
            mark.practical = practical
            mark.internal = internal
            mark.total = total
            mark.updated_at = datetime.utcnow()

            saved_count += 1

        if saved_count == 0:

            return "❌ No valid student rows found."

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
# REPORT HTML
# ==========================================================

def generate_report_html(
    year_value,
    class_value,
    exam_value
):

    year_id = parse_id(
        year_value
    )

    class_id = parse_id(
        class_value
    )

    if not year_id:

        return (
            "<div class='report-error'>"
            "❌ Please select Academic Year."
            "</div>"
        )

    if not class_id:

        return (
            "<div class='report-error'>"
            "❌ Please select Class."
            "</div>"
        )

    if not exam_value:

        return (
            "<div class='report-error'>"
            "❌ Please select Exam."
            "</div>"
        )

    db = SessionLocal()

    try:

        class_obj = db.get(
            ClassSection,
            class_id
        )

        if not class_obj:

            return (
                "<div class='report-error'>"
                "❌ Class not found."
                "</div>"
            )

        year_obj = db.get(
            AcademicYear,
            year_id
        )

        if not year_obj:

            return (
                "<div class='report-error'>"
                "❌ Academic Year not found."
                "</div>"
            )

        students = (
            db.query(Student)
            .filter(
                Student.class_id == class_id,
                Student.active == True
            )
            .order_by(
                Student.roll_no,
                Student.name
            )
            .all()
        )

        subjects = (
            db.query(Subject)
            .join(
                ClassSubject,
                ClassSubject.subject_id == Subject.id
            )
            .filter(
                ClassSubject.class_id == class_id,
                Subject.active == True
            )
            .order_by(
                Subject.name
            )
            .all()
        )

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

            exam_obj = db.get(
                Exam,
                exam_id
            )

            if (
                not exam_obj
                or not exam_obj.active
            ):

                return (
                    "<div class='report-error'>"
                    "❌ Exam not found."
                    "</div>"
                )

            exams = [
                exam_obj
            ]

        if not students:

            return (
                "<div class='report-error'>"
                "❌ No students found."
                "</div>"
            )

        if not subjects:

            return (
                "<div class='report-error'>"
                "❌ No subjects found."
                "</div>"
            )

        if not exams:

            return (
                "<div class='report-error'>"
                "❌ No exams found."
                "</div>"
            )

        html = """
        <div id="print-report-area" class="school-report">
        """

        html += """
        <div class="report-header">
            <h1>🏫 SCHOOL MARK LIST</h1>
        """

        html += (
            "<div class='report-info'>"
            f"<b>Academic Year:</b> {year_obj.name}"
            "&nbsp;&nbsp;"
            f"<b>Class:</b> {class_obj.name}"
            "&nbsp;&nbsp;"
            "<b>Exam:</b> "
        )

        if len(exams) == 1:

            html += exams[0].name

        else:

            html += "All Exams"

        html += """
        </div>
        </div>
        """

        html += """
        <div class="table-wrapper">
        <table class="mark-report">
        <thead>
        <tr>
            <th rowspan="2">Roll No</th>
            <th rowspan="2">Student Name</th>
        """

        # --------------------------------------------------
        # EXAM HEADERS
        # --------------------------------------------------

        for exam in exams:

            colspan = 0

            for subject in subjects:

                components = 0

                if subject.theory:
                    components += 1

                if subject.practical:
                    components += 1

                if subject.internal:
                    components += 1

                components += 1

                colspan += components

            html += (
                f"<th colspan='{colspan}' "
                f"class='exam-header'>"
                f"{exam.name}"
                f"</th>"
            )

        html += """
        </tr>
        <tr>
        """

        # --------------------------------------------------
        # SUBJECT HEADERS
        # --------------------------------------------------

        for exam in exams:

            for subject in subjects:

                components = (
                    (1 if subject.theory else 0)
                    + (1 if subject.practical else 0)
                    + (1 if subject.internal else 0)
                    + 1
                )

                html += (
                    f"<th colspan='{components}' "
                    f"class='subject-header'>"
                    f"{subject.name}"
                    f"</th>"
                )

        html += """
        </tr>
        <tr>
            <th></th>
            <th></th>
        """

        # --------------------------------------------------
        # COMPONENT HEADERS
        # --------------------------------------------------

        for exam in exams:

            for subject in subjects:

                if subject.theory:

                    html += "<th>Theory</th>"

                if subject.practical:

                    html += "<th>Practical</th>"

                if subject.internal:

                    html += "<th>Internal</th>"

                html += "<th>Total</th>"

        html += """
        </tr>
        </thead>
        <tbody>
        """

        # --------------------------------------------------
        # STUDENT DATA
        # --------------------------------------------------

        for student in students:

            html += "<tr>"

            html += (
                f"<td>{student.roll_no or ''}</td>"
                f"<td class='student-name'>"
                f"{student.name}"
                f"</td>"
            )

            for exam in exams:

                for subject in subjects:

                    mark = (
                        db.query(Mark)
                        .filter_by(
                            academic_year_id=year_id,
                            exam_id=exam.id,
                            student_id=student.id,
                            subject_id=subject.id
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

                    if subject.theory:

                        html += (
                            f"<td>{theory}</td>"
                        )

                    if subject.practical:

                        html += (
                            f"<td>{practical}</td>"
                        )

                    if subject.internal:

                        html += (
                            f"<td>{internal}</td>"
                        )

                    html += (
                        f"<td class='total-cell'>"
                        f"{total}"
                        f"</td>"
                    )

            html += "</tr>"

        html += """
        </tbody>
        </table>
        </div>
        """

        html += (
            "<div class='report-footer'>"
            f"Total Students: {len(students)}"
            "</div>"
        )

        html += "</div>"

        return html

    except Exception as e:

        return (
            "<div class='report-error'>"
            "❌ Error generating report: "
            + str(e)
            + "</div>"
        )

    finally:

        db.close()


# ==========================================================
# CONSOLIDATED REPORT
# ==========================================================

def generate_consolidated_report(
    year_value,
    class_value,
    exam_value
):

    return generate_report_html(
        year_value,
        class_value,
        exam_value
    )


# ==========================================================
# LOGIN
# ==========================================================

def login(
    username,
    password
):

    db = SessionLocal()

    try:

        username = clean_text(
            username
        )

        teacher = (
            db.query(Teacher)
            .filter(
                Teacher.username == username,
                Teacher.active == True
            )
            .first()
        )

        if not teacher:

            return (
                "❌ Invalid username or password.",
                gr.update(
                    visible=False
                ),
                gr.update(
                    visible=False
                ),
                gr.update(
                    visible=False
                ),
                gr.update(
                    visible=False
                ),
                gr.update(
                    visible=False
                )
            )

        if not verify_password(
            password or "",
            teacher.password_hash
        ):

            return (
                "❌ Invalid username or password.",
                gr.update(
                    visible=False
                ),
                gr.update(
                    visible=False
                ),
                gr.update(
                    visible=False
                ),
                gr.update(
                    visible=False
                ),
                gr.update(
                    visible=False
                )
            )

        # --------------------------------------------------
        # ADMIN LOGIN
        # --------------------------------------------------

        if teacher.role == "admin":

            return (
                f"✅ Welcome, {teacher.name} (Administrator)",

                gr.update(
                    visible=True
                ),

                gr.update(
                    visible=True
                ),

                gr.update(
                    visible=True
                ),

                gr.update(
                    visible=True
                ),

                gr.update(
                    visible=True
                )
            )

        # --------------------------------------------------
        # TEACHER LOGIN
        # --------------------------------------------------

        return (
            f"✅ Welcome, {teacher.name}",

            gr.update(
                visible=False
            ),

            gr.update(
                visible=False
            ),

            gr.update(
                visible=True
            ),

            gr.update(
                visible=True
            ),

            gr.update(
                visible=False
            )
        )

    finally:

        db.close()


# ==========================================================
# CSS
# ==========================================================

css = """

.gradio-container {
    max-width: 1500px !important;
}


/* ========================================================
   REPORT SCREEN
   ======================================================== */

.school-report {
    background: white;
    color: black;
    padding: 20px;
    width: 100%;
    overflow-x: auto;
}

.report-header {
    text-align: center;
    margin-bottom: 15px;
}

.report-header h1 {
    margin: 0 0 10px 0;
    font-size: 24px;
}

.report-info {
    font-size: 15px;
    padding: 8px;
}

.table-wrapper {
    width: 100%;
    overflow-x: auto;
}

.mark-report {
    border-collapse: collapse;
    width: 100%;
    min-width: 900px;
    font-size: 12px;
}

.mark-report th,
.mark-report td {
    border: 1px solid #333;
    padding: 6px;
    text-align: center;
    vertical-align: middle;
}

.mark-report th {
    font-weight: bold;
}

.mark-report .student-name {
    text-align: left;
    min-width: 160px;
}

.mark-report .total-cell {
    font-weight: bold;
}

.exam-header {
    font-size: 13px;
}

.subject-header {
    font-size: 12px;
}

.report-footer {
    margin-top: 15px;
    font-weight: bold;
}

.report-error {
    padding: 15px;
    font-weight: bold;
}


/* ========================================================
   PRINT ONLY REPORT
   ======================================================== */

@media print {

    body * {
        visibility: hidden !important;
    }

    #report-container,
    #report-container * {
        visibility: visible !important;
    }

    #report-container {
        position: absolute !important;
        left: 0 !important;
        top: 0 !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 0 !important;
        background: white !important;
        overflow: visible !important;
    }

    #print-report-area {
        position: relative !important;
        left: 0 !important;
        top: 0 !important;
        width: 100% !important;
        margin: 0 !important;
        padding: 10px !important;
        background: white !important;
        color: black !important;
    }

    .school-report {
        width: 100% !important;
        overflow: visible !important;
        background: white !important;
        color: black !important;
    }

    .table-wrapper {
        width: 100% !important;
        overflow: visible !important;
    }

    .mark-report {
        width: 100% !important;
        min-width: 0 !important;
        border-collapse: collapse !important;
        font-size: 8px !important;
    }

    .mark-report th,
    .mark-report td {
        padding: 3px !important;
        border: 1px solid #000 !important;
    }

    .report-header {
        display: block !important;
        text-align: center !important;
    }

    .report-footer {
        display: block !important;
    }

    @page {
        size: A4 landscape;
        margin: 8mm;
    }
}
"""


# ==========================================================
# JAVASCRIPT
# ==========================================================

js = """
function printMarkReport() {
    window.print();
}
"""


# ==========================================================
# GRADIO APPLICATION
# ==========================================================

with gr.Blocks(
    title="School Mark Entry System",
    css=css,
    js=js
) as demo:

    gr.Markdown(
        "# 🏫 School Mark Entry System"
    )

    # ======================================================
    # LOGIN
    # ======================================================

    gr.Markdown(
        "### 🔐 Login"
    )

    with gr.Row():

        username = gr.Textbox(
            label="Username",
            placeholder="Enter username"
        )

        password = gr.Textbox(
            label="Password",
            type="password",
            placeholder="Enter password"
        )

        login_button = gr.Button(
            "🔐 Login",
            variant="primary"
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
            # MASTER MANAGEMENT
            # ==================================================

            with gr.Tab(
                "⚙️ Master Management",
                visible=False
            ) as master_tab:

                gr.Markdown(
                    "## ⚙️ Master Data Management"
                )

                # ----------------------------------------------
                # ACADEMIC YEAR
                # ----------------------------------------------

                gr.Markdown(
                    "### 📅 Academic Year"
                )

                with gr.Row():

                    year_name = gr.Textbox(
                        label="Academic Year",
                        placeholder="Example: 2026-27"
                    )

                    add_year_button = gr.Button(
                        "➕ Add Year",
                        variant="primary"
                    )

                with gr.Row():

                    delete_year_select = gr.Dropdown(
                        choices=get_years(),
                        label="Select Academic Year"
                    )

                    delete_year_button = gr.Button(
                        "🗑️ Delete Year",
                        variant="stop"
                    )

                year_message = gr.Markdown()

                # ----------------------------------------------
                # CLASS
                # ----------------------------------------------

                gr.Markdown(
                    "### 🏫 Classes"
                )

                with gr.Row():

                    class_name = gr.Textbox(
                        label="Class Name",
                        placeholder="Example: 10-A"
                    )

                    add_class_button = gr.Button(
                        "➕ Add Class",
                        variant="primary"
                    )

                with gr.Row():

                    delete_class_select = gr.Dropdown(
                        choices=get_classes(),
                        label="Select Class"
                    )

                    delete_class_button = gr.Button(
                        "🗑️ Delete Class",
                        variant="stop"
                    )

                class_message = gr.Markdown()

                # ----------------------------------------------
                # SUBJECT
                # ----------------------------------------------

                gr.Markdown(
                    "### 📚 Subjects"
                )

                with gr.Row():

                    subject_name = gr.Textbox(
                        label="Subject Name"
                    )

                    subject_code = gr.Textbox(
                        label="Subject Code"
                    )

                with gr.Row():

                    subject_theory = gr.Checkbox(
                        label="Theory",
                        value=True
                    )

                    subject_practical = gr.Checkbox(
                        label="Practical",
                        value=False
                    )

                    subject_internal = gr.Checkbox(
                        label="Internal",
                        value=True
                    )

                with gr.Row():

                    subject_theory_max = gr.Number(
                        label="Theory Max",
                        value=80,
                        precision=0
                    )

                    subject_practical_max = gr.Number(
                        label="Practical Max",
                        value=20,
                        precision=0
                    )

                    subject_internal_max = gr.Number(
                        label="Internal Max",
                        value=20,
                        precision=0
                    )

                add_subject_button = gr.Button(
                    "➕ Add Subject",
                    variant="primary"
                )

                with gr.Row():

                    delete_subject_select = gr.Dropdown(
                        choices=get_subjects(),
                        label="Select Subject"
                    )

                    delete_subject_button = gr.Button(
                        "🗑️ Delete Subject",
                        variant="stop"
                    )

                subject_message = gr.Markdown()

                # ----------------------------------------------
                # EXAM
                # ----------------------------------------------

                gr.Markdown(
                    "### 📝 Exams"
                )

                with gr.Row():

                    exam_name = gr.Textbox(
                        label="Exam Name",
                        placeholder="Example: Quarterly"
                    )

                    add_exam_button = gr.Button(
                        "➕ Add Exam",
                        variant="primary"
                    )

                with gr.Row():

                    delete_exam_select = gr.Dropdown(
                        choices=get_exams(),
                        label="Select Exam"
                    )

                    delete_exam_button = gr.Button(
                        "🗑️ Delete Exam",
                        variant="stop"
                    )

                exam_message = gr.Markdown()

                # ----------------------------------------------
                # USER MANAGEMENT
                # ----------------------------------------------

                gr.Markdown(
                    "### 👤 Teacher / User Management"
                )

                with gr.Row():

                    new_username = gr.Textbox(
                        label="Username",
                        placeholder="Example: teacher1"
                    )

                    new_teacher_name = gr.Textbox(
                        label="User Name",
                        placeholder="Example: Tamil Teacher"
                    )

                    new_teacher_password = gr.Textbox(
                        label="Password",
                        type="password",
                        placeholder="Minimum 6 characters"
                    )

                    new_teacher_confirm_password = gr.Textbox(
                        label="Confirm Password",
                        type="password",
                        placeholder="Re-enter password"
                    )

                add_teacher_button = gr.Button(
                    "➕ Create User",
                    variant="primary"
                )

                teacher_message = gr.Markdown()

                teacher_table = gr.Dataframe(
                    headers=[
                        "ID",
                        "Username",
                        "Name",
                        "Role"
                    ],
                    value=get_teachers(),
                    interactive=False
                )

                gr.Markdown(
                    "### 🗑️ Delete User"
                )

                delete_teacher_username = gr.Textbox(
                    label="Username to Delete",
                    placeholder="Enter username"
                )

                delete_teacher_button = gr.Button(
                    "🗑️ Delete User",
                    variant="stop"
                )

                delete_teacher_message = gr.Markdown()

            # ==================================================
            # STUDENT MANAGEMENT
            # ==================================================

            with gr.Tab(
                "👨‍🎓 Student Management",
                visible=False
            ) as student_management_tab:

                gr.Markdown(
                    "## 👨‍🎓 Student Management"
                )

                gr.Markdown(
                    "### ➕ Add Student"
                )

                with gr.Row():

                    admission_no = gr.Textbox(
                        label="Admission No"
                    )

                    roll_no = gr.Textbox(
                        label="Roll No"
                    )

                    student_name = gr.Textbox(
                        label="Student Name"
                    )

                    student_class = gr.Dropdown(
                        choices=get_classes(),
                        label="Class"
                    )

                add_student_button = gr.Button(
                    "➕ Add Student",
                    variant="primary"
                )

                student_message = gr.Markdown()

                # ----------------------------------------------
                # DELETE STUDENT
                # ----------------------------------------------

                gr.Markdown(
                    "### 🗑️ Delete Student"
                )

                with gr.Row():

                    delete_student_class = gr.Dropdown(
                        choices=get_classes(),
                        label="Select Class"
                    )

                    delete_student_select = gr.Dropdown(
                        choices=[],
                        label="Select Student"
                    )

                delete_student_button = gr.Button(
                    "🗑️ Delete Selected Student",
                    variant="stop"
                )

                delete_student_message = gr.Markdown()

                # ----------------------------------------------
                # STUDENT TABLE
                # ----------------------------------------------

                gr.Markdown(
                    "### 👨‍🎓 Current Student List"
                )

                student_table = gr.Dataframe(
                    headers=[
                        "ID",
                        "Admission No",
                        "Roll No",
                        "Student Name",
                        "Class"
                    ],
                    value=get_student_list(),
                    interactive=False
                )

            # ==================================================
            # MARK ENTRY
            # ==================================================

            with gr.Tab(
                "📝 Mark Entry"
            ) as mark_entry_tab:

                gr.Markdown(
                    "## 📝 Mark Entry"
                )

                with gr.Row():

                    mark_year = gr.Dropdown(
                        choices=get_years(),
                        label="Academic Year"
                    )

                    mark_class = gr.Dropdown(
                        choices=get_classes(),
                        label="Class"
                    )

                    mark_exam = gr.Dropdown(
                        choices=get_exams(),
                        label="Exam"
                    )

                    mark_subject = gr.Dropdown(
                        choices=[],
                        label="Subject"
                    )

                mark_class.change(
                    get_subjects_for_class,
                    inputs=mark_class,
                    outputs=mark_subject
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
                        mark_subject
                    ],
                    outputs=[
                        marks_table,
                        mark_pattern
                    ]
                )

                save_button = gr.Button(
                    "💾 Save Marks",
                    variant="primary"
                )

                save_message = gr.Markdown()

                save_button.click(
                    save_marks,
                    inputs=[
                        mark_class,
                        mark_year,
                        mark_exam,
                        mark_subject,
                        marks_table
                    ],
                    outputs=save_message
                )

            # ==================================================
            # VIEW MARKS
            # ==================================================

            with gr.Tab(
                "👁️ View Marks"
            ) as view_marks_tab:

                gr.Markdown(
                    "## 👁️ Subject-wise Mark View"
                )

                with gr.Row():

                    view_year = gr.Dropdown(
                        choices=get_years(),
                        label="Academic Year"
                    )

                    view_class = gr.Dropdown(
                        choices=get_classes(),
                        label="Class"
                    )

                    view_exam = gr.Dropdown(
                        choices=get_exams(),
                        label="Exam"
                    )

                    view_subject = gr.Dropdown(
                        choices=[],
                        label="Subject"
                    )

                view_class.change(
                    get_subjects_for_class,
                    inputs=view_class,
                    outputs=view_subject
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
                        view_subject
                    ],
                    outputs=[
                        view_table,
                        view_pattern
                    ]
                )

            # ==================================================
            # REPORT
            # ==================================================

            with gr.Tab(
                "📊 Mark List / Print",
                visible=False
            ) as report_tab:

                gr.Markdown(
                    "## 📊 Consolidated Mark List"
                )

                with gr.Row():

                    list_year = gr.Dropdown(
                        choices=get_years(),
                        label="Academic Year"
                    )

                    list_class = gr.Dropdown(
                        choices=get_classes(),
                        label="Class"
                    )

                    list_exam = gr.Dropdown(
                        choices=get_all_exams(),
                        label="Exam"
                    )

                consolidated_button = gr.Button(
                    "📋 View Consolidated Mark List",
                    variant="primary"
                )

                print_button = gr.Button(
                    "🖨️ PRINT REPORT",
                    variant="secondary"
                )

                consolidated_report = gr.HTML(
                    value="",
                    elem_id="report-container"
                )

                consolidated_button.click(
                    generate_consolidated_report,
                    inputs=[
                        list_year,
                        list_class,
                        list_exam
                    ],
                    outputs=consolidated_report
                )

                # --------------------------------------------------
                # PRINT BUTTON
                # --------------------------------------------------

                print_button.click(
                    None,
                    inputs=None,
                    outputs=None,
                    js="window.print();"
                )

                gr.Markdown(
                    """
### 🖨️ Print Instructions

1. Academic Year select செய்யுங்கள்.
2. Class select செய்யுங்கள்.
3. Exam select செய்யுங்கள்.
4. **View Consolidated Mark List** அழுத்துங்கள்.
5. Mark List வந்ததும் **🖨️ PRINT REPORT** அழுத்துங்கள்.
6. Print dialog வரும்.
7. Printer அல்லது **Save as PDF** தேர்வு செய்யலாம்.

**Print-ல் Mark List / Report மட்டும் வரும்.**

**முழு Gradio page print ஆகாது.**
"""
                )

    # ======================================================
    # LOGIN EVENT
    # ======================================================

    login_button.click(
        login,
        inputs=[
            username,
            password
        ],
        outputs=[
            login_message,
            master_tab,
            student_management_tab,
            mark_entry_tab,
            view_marks_tab,
            report_tab
        ]
    )

    # ======================================================
    # MASTER EVENTS
    # ======================================================

    add_year_button.click(
        add_academic_year,
        inputs=year_name,
        outputs=[
            year_message,
            delete_year_select
        ]
    )

    delete_year_button.click(
        delete_academic_year,
        inputs=delete_year_select,
        outputs=[
            year_message,
            delete_year_select
        ]
    )

    add_class_button.click(
        add_class,
        inputs=class_name,
        outputs=[
            class_message,
            delete_class_select
        ]
    )

    delete_class_button.click(
        delete_class,
        inputs=delete_class_select,
        outputs=[
            class_message,
            delete_class_select
        ]
    )

    add_subject_button.click(
        add_subject,
        inputs=[
            subject_name,
            subject_code,
            subject_theory,
            subject_practical,
            subject_internal,
            subject_theory_max,
            subject_practical_max,
            subject_internal_max
        ],
        outputs=[
            subject_message,
            delete_subject_select
        ]
    )

    delete_subject_button.click(
        delete_subject,
        inputs=delete_subject_select,
        outputs=[
            subject_message,
            delete_subject_select
        ]
    )

    add_exam_button.click(
        add_exam,
        inputs=exam_name,
        outputs=[
            exam_message,
            delete_exam_select,
            list_exam
        ]
    )

    delete_exam_button.click(
        delete_exam,
        inputs=delete_exam_select,
        outputs=[
            exam_message,
            delete_exam_select,
            list_exam
        ]
    )

    # ======================================================
    # USER EVENTS
    # ======================================================

    add_teacher_button.click(
        add_teacher,
        inputs=[
            new_username,
            new_teacher_name,
            new_teacher_password,
            new_teacher_confirm_password
        ],
        outputs=[
            teacher_message,
            teacher_table
        ]
    )

    delete_teacher_button.click(
        delete_teacher,
        inputs=delete_teacher_username,
        outputs=[
            delete_teacher_message,
            teacher_table
        ]
    )

    # ======================================================
    # STUDENT EVENTS
    # ======================================================

    student_class.change(
        get_students_for_class,
        inputs=student_class,
        outputs=delete_student_select
    )

    delete_student_class.change(
        get_students_for_class,
        inputs=delete_student_class,
        outputs=delete_student_select
    )

    add_student_button.click(
        add_student,
        inputs=[
            admission_no,
            roll_no,
            student_name,
            student_class
        ],
        outputs=[
            student_message,
            student_table,
            delete_student_select
        ]
    )

    delete_student_button.click(
        delete_student,
        inputs=[
            delete_student_class,
            delete_student_select
        ],
        outputs=[
            delete_student_message,
            student_table,
            delete_student_select
        ]
    )

    # ======================================================
    # INITIAL INFORMATION
    # ======================================================

    gr.Markdown(
        "**Initial Admin Login:** `admin` / `Admin@123`"
    )


# ==========================================================
# START APPLICATION
# ==========================================================

if __name__ == "__main__":

    port = int(
        os.getenv(
            "PORT",
            "7860"
        )
    )

    demo.launch(
        server_name="0.0.0.0",
        server_port=port
    )
