import os
import hashlib
import secrets
from datetime import datetime

import gradio as gr
from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean,
    DateTime, ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker


# ==========================================================
# SCHOOL MARK ENTRY SYSTEM
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
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ==========================================================
# DATABASE TABLES
# ==========================================================

class AcademicYear(Base):
    __tablename__ = "academic_years"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    active = Column(Boolean, default=True)


class ClassSection(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True)
    admission_no = Column(String(50), unique=True, nullable=False)
    roll_no = Column(String(50))
    name = Column(String(200), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    active = Column(Boolean, default=True)


class Teacher(Base):
    __tablename__ = "teachers"

    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    password_hash = Column(String(500), nullable=False)
    role = Column(String(20), default="teacher")
    active = Column(Boolean, default=True)


class Subject(Base):
    __tablename__ = "subjects"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)

    theory = Column(Boolean, default=True)
    practical = Column(Boolean, default=False)
    internal = Column(Boolean, default=True)

    theory_max = Column(Integer, default=0)
    practical_max = Column(Integer, default=0)
    internal_max = Column(Integer, default=0)

    active = Column(Boolean, default=True)


class ClassSubject(Base):
    __tablename__ = "class_subjects"

    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "class_id",
            "subject_id",
            name="uq_class_subject"
        ),
    )


class Exam(Base):
    __tablename__ = "exams"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    active = Column(Boolean, default=True)


class Mark(Base):
    __tablename__ = "marks"

    id = Column(Integer, primary_key=True)

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

    theory = Column(Integer, default=0)
    practical = Column(Integer, default=0)
    internal = Column(Integer, default=0)
    total = Column(Integer, default=0)

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


# Create tables
Base.metadata.create_all(engine)


# ==========================================================
# PASSWORD
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
        salt, digest = stored.split("$", 1)

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
# INITIAL DATA
# ==========================================================

def seed_database():

    db = SessionLocal()

    try:

        # Academic Year
        if not db.query(AcademicYear).first():

            db.add(
                AcademicYear(
                    name="2026-27",
                    active=True
                )
            )

        # Classes
        if not db.query(ClassSection).first():

            db.add_all([
                ClassSection(name="10-A"),
                ClassSection(name="10-B"),
                ClassSection(name="11-A"),
                ClassSection(name="11-B"),
                ClassSection(name="12-A"),
                ClassSection(name="12-B")
            ])

        # Exams
        if not db.query(Exam).first():

            db.add_all([
                Exam(name="Unit Test 1"),
                Exam(name="Quarterly"),
                Exam(name="Half-Yearly"),
                Exam(name="Annual")
            ])

        # Subjects
        if not db.query(Subject).first():

            db.add_all([

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

            ])

        # Admin
        if not db.query(Teacher).filter_by(
            username="admin"
        ).first():

            db.add(
                Teacher(
                    username="admin",
                    name="Administrator",
                    password_hash=hash_password(
                        "Admin@123"
                    ),
                    role="admin"
                )
            )

        db.commit()

        # Connect subjects to all classes
        all_classes = db.query(
            ClassSection
        ).all()

        all_subjects = db.query(
            Subject
        ).all()

        for cls in all_classes:

            for subject in all_subjects:

                exists = db.query(
                    ClassSubject
                ).filter_by(
                    class_id=cls.id,
                    subject_id=subject.id
                ).first()

                if not exists:

                    db.add(
                        ClassSubject(
                            class_id=cls.id,
                            subject_id=subject.id
                        )
                    )

        db.commit()

    finally:

        db.close()


seed_database()


# ==========================================================
# HELPERS
# ==========================================================

def parse_id(value):

    if not value:
        return None

    try:
        return int(
            str(value).split("|", 1)[0].strip()
        )

    except Exception:
        return None


def get_classes():

    db = SessionLocal()

    try:

        rows = db.query(
            ClassSection
        ).order_by(
            ClassSection.name
        ).all()

        return [
            f"{x.id} | {x.name}"
            for x in rows
        ]

    finally:
        db.close()


def get_years():

    db = SessionLocal()

    try:

        rows = db.query(
            AcademicYear
        ).filter_by(
            active=True
        ).all()

        return [
            f"{x.id} | {x.name}"
            for x in rows
        ]

    finally:
        db.close()


def get_exams():

    db = SessionLocal()

    try:

        rows = db.query(
            Exam
        ).filter_by(
            active=True
        ).all()

        return [
            f"{x.id} | {x.name}"
            for x in rows
        ]

    finally:
        db.close()


def get_subjects_for_class(class_value):

    class_id = parse_id(class_value)

    if not class_id:
        return gr.Dropdown(
            choices=[],
            value=None
        )

    db = SessionLocal()

    try:

        subjects = (
            db.query(Subject)
            .filter(Subject.active == True)
            .order_by(Subject.name)
            .all()
        )

        subject_choices = [
            f"{subject.id} | {subject.name}"
            for subject in subjects
        ]

        return gr.Dropdown(
            choices=subject_choices,
            value=None
        )

    finally:
        db.close()

# ==========================================================
# STUDENT MANAGEMENT
# ==========================================================

def add_student(
    admission_no,
    roll_no,
    student_name,
    class_value
):

    admission_no = (
        admission_no or ""
    ).strip()

    roll_no = (
        roll_no or ""
    ).strip()

    student_name = (
        student_name or ""
    ).strip()

    class_id = parse_id(
        class_value
    )

    if not admission_no:

        return (
            "❌ Admission No is required.",
            get_student_list()
        )

    if not student_name:

        return (
            "❌ Student Name is required.",
            get_student_list()
        )

    if not class_id:

        return (
            "❌ Please select Class.",
            get_student_list()
        )

    db = SessionLocal()

    try:

        old_student = db.query(
            Student
        ).filter_by(
            admission_no=admission_no
        ).first()

        if old_student:

            return (
                "❌ This Admission No already exists.",
                get_student_list()
            )

        new_student = Student(
            admission_no=admission_no,
            roll_no=roll_no,
            name=student_name,
            class_id=class_id,
            active=True
        )

        db.add(new_student)
        db.commit()

        return (
            "✅ Student added successfully.",
            get_student_list()
        )

    except Exception as e:

        db.rollback()

        return (
            "❌ Error: " + str(e),
            get_student_list()
        )

    finally:

        db.close()


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
                Student.active == True
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
# MARK ENTRY
# ==========================================================

def load_marks(
    class_value,
    year_value,
    exam_value,
    subject_value
):

    class_id = parse_id(class_value)
    year_id = parse_id(year_value)
    exam_id = parse_id(exam_value)
    subject_id = parse_id(subject_value)

    if not all([
        class_id,
        year_id,
        exam_id,
        subject_id
    ]):

        return (
            [],
            "Please select all options."
        )

    db = SessionLocal()

    try:

        subject = db.get(
            Subject,
            subject_id
        )

        students = (
            db.query(Student)
            .filter_by(
                class_id=class_id,
                active=True
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
            "Student Name",
            "Theory"
        ]

        if subject.practical:
            headers.append("Practical")

        if subject.internal:
            headers.append("Internal")

        headers.append("Total")

        rows = []

        for student in students:

            mark = db.query(
                Mark
            ).filter_by(
                academic_year_id=year_id,
                exam_id=exam_id,
                student_id=student.id,
                subject_id=subject_id
            ).first()

            theory = mark.theory if mark else 0
            practical = mark.practical if mark else 0
            internal = mark.internal if mark else 0

            total = (
                theory +
                practical +
                internal
            )

            row = [
                student.id,
                student.roll_no or "",
                student.name,
                theory
            ]

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
            "**Mark Pattern:** " +
            " + ".join(pattern)
        )

    finally:

        db.close()


def save_marks(
    class_value,
    year_value,
    exam_value,
    subject_value,
    table_data
):

    class_id = parse_id(class_value)
    year_id = parse_id(year_value)
    exam_id = parse_id(exam_value)
    subject_id = parse_id(subject_value)

    if not all([
        class_id,
        year_id,
        exam_id,
        subject_id
    ]):

        return "❌ Select all options first."

    db = SessionLocal()

    try:

        subject = db.get(
            Subject,
            subject_id
        )
    if table_data is None:
        table_data = []

    for row in table_data:

            if not row:
                continue

            student_id = int(
                row[0]
            )

            position = 3

            theory = int(
                row[position] or 0
            )

            position += 1

            practical = 0
            internal = 0

            if subject.practical:

                practical = int(
                    row[position] or 0
                )

                position += 1

            if subject.internal:

                internal = int(
                    row[position] or 0
                )

                position += 1

            total = (
                theory +
                practical +
                internal
            )

            mark = db.query(
                Mark
            ).filter_by(
                academic_year_id=year_id,
                exam_id=exam_id,
                student_id=student_id,
                subject_id=subject_id
            ).first()

            if not mark:

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

        db.commit()

        return "✅ Marks saved successfully."

    except Exception as e:

        db.rollback()

        return "❌ Error: " + str(e)

    finally:

        db.close()


# ==========================================================
# LOGIN
# ==========================================================

def login(
    username,
    password
):

    db = SessionLocal()

    try:

        teacher = db.query(
            Teacher
        ).filter_by(
            username=(username or "").strip(),
            active=True
        ).first()

        if not teacher:

            return (
                "❌ Invalid username or password.",
                gr.update(visible=False)
            )

        if not verify_password(
            password or "",
            teacher.password_hash
        ):

            return (
                "❌ Invalid username or password.",
                gr.update(visible=False)
            )

        return (
            f"✅ Welcome, {teacher.name}",
            gr.update(visible=True)
        )

    finally:

        db.close()


# ==========================================================
# GRADIO UI
# ==========================================================

css = """
.gradio-container {
    max-width: 1450px !important;
}
"""

with gr.Blocks(
    title="School Mark Entry",
    css=css
) as demo:

    gr.Markdown(
        "# 🏫 School Mark Entry System"
    )

    gr.Markdown(
        "### Login"
    )

    with gr.Row():

        username = gr.Textbox(
            label="Username"
        )

        password = gr.Textbox(
            label="Password",
            type="password"
        )

        login_button = gr.Button(
            "🔐 Login",
            variant="primary"
        )

    login_message = gr.Markdown()

    with gr.Column(
        visible=False
    ) as application:

        with gr.Tabs():

            # ==================================================
            # STUDENT MANAGEMENT
            # ==================================================

            with gr.Tab(
                "👨‍🎓 Student Management"
            ):

                gr.Markdown(
                    "## Student Management"
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
                        student_table
                    ]
                )


            # ==================================================
            # MARK ENTRY
            # ==================================================

            with gr.Tab(
                "📝 Mark Entry"
            ):

                gr.Markdown(
                    "## Mark Entry"
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
                    "Load Students"
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
            ):

                gr.Markdown(
                    "## Subject-wise Mark View"
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
                    "View Marks"
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
            # MARK LIST
            # ==================================================

            with gr.Tab(
                "📊 Mark List / Print"
            ):

                gr.Markdown(
                    "## Consolidated Mark List"
                )

                gr.Markdown(
                    "Select Academic Year, Exam and Class."
                )

                with gr.Row():

                    list_year = gr.Dropdown(
                        choices=get_years(),
                        label="Academic Year"
                    )

                    list_exam = gr.Dropdown(
                        choices=get_exams(),
                        label="Exam"
                    )

                    list_class = gr.Dropdown(
                        choices=get_classes(),
                        label="Class"
                    )

                gr.Markdown(
                    "Students and subjects will appear after "
                    "the mark list is connected to the database."
                )

                gr.Markdown(
                    "🖨️ Use the browser Print option "
                    "(Ctrl + P) to print."
                )


    login_button.click(
        login,
        inputs=[
            username,
            password
        ],
        outputs=[
            login_message,
            application
        ]
    )


    gr.Markdown(
        "**Initial Login:** admin / Admin@123"
    )


# ==========================================================
# START SERVER
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
