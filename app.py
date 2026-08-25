import os
import hashlib
import secrets
from datetime import datetime

import gradio as gr
from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey,
    UniqueConstraint
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

# ==========================================================
# SCHOOL MARK ENTRY SYSTEM
# Python + Gradio + SQLAlchemy + PostgreSQL
#
# Render:
#   DATABASE_URL = Render PostgreSQL Internal Database URL
#
# Local:
#   If DATABASE_URL is absent, SQLite is used automatically.
# ==========================================================

DATABASE_URL = os.getenv("DATABASE_URL", "").strip()

if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = "postgresql://" + DATABASE_URL[len("postgres://"):]

if DATABASE_URL:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    engine = create_engine(
        "sqlite:///school_marks.db",
        connect_args={"check_same_thread": False}
    )

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# ---------------- DATABASE TABLES ----------------

class School(Base):
    __tablename__ = "schools"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    code = Column(String(50), unique=True, nullable=False)


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
    class_section = relationship("ClassSection")


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
        UniqueConstraint("class_id", "subject_id", name="uq_class_subject"),
    )


class Exam(Base):
    __tablename__ = "exams"
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    active = Column(Boolean, default=True)


class Mark(Base):
    __tablename__ = "marks"
    id = Column(Integer, primary_key=True)
    academic_year_id = Column(Integer, ForeignKey("academic_years.id"), nullable=False)
    exam_id = Column(Integer, ForeignKey("exams.id"), nullable=False)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)
    subject_id = Column(Integer, ForeignKey("subjects.id"), nullable=False)
    theory = Column(Integer, default=0)
    practical = Column(Integer, default=0)
    internal = Column(Integer, default=0)
    total = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow)
    __table_args__ = (
        UniqueConstraint(
            "academic_year_id", "exam_id", "student_id", "subject_id",
            name="uq_student_exam_subject"
        ),
    )


Base.metadata.create_all(engine)


# ---------------- SECURITY ----------------

def hash_password(password):
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode(), salt.encode(), 120000
    ).hex()
    return f"{salt}${digest}"


def verify_password(password, stored):
    try:
        salt, digest = stored.split("$", 1)
        check = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), salt.encode(), 120000
        ).hex()
        return secrets.compare_digest(check, digest)
    except Exception:
        return False


# ---------------- INITIAL DATA ----------------

def seed_database():
    db = SessionLocal()
    try:
        if not db.query(School).first():
            db.add(School(name="My School", code="SCHOOL001"))

        if not db.query(AcademicYear).first():
            db.add(AcademicYear(name="2026-27", active=True))

        if not db.query(ClassSection).first():
            db.add_all([
                ClassSection(name="10-A"),
                ClassSection(name="10-B"),
                ClassSection(name="11-A"),
                ClassSection(name="11-B"),
            ])

        if not db.query(Exam).first():
            db.add_all([
                Exam(name="Unit Test 1"),
                Exam(name="Quarterly"),
                Exam(name="Half-Yearly"),
                Exam(name="Annual"),
            ])

        if not db.query(Subject).first():
            db.add_all([
                Subject(name="Tamil", code="TAM", theory=True, practical=False,
                        internal=True, theory_max=80, internal_max=20),
                Subject(name="English", code="ENG", theory=True, practical=False,
                        internal=True, theory_max=80, internal_max=20),
                Subject(name="Mathematics", code="MAT", theory=True, practical=False,
                        internal=True, theory_max=80, internal_max=20),
                Subject(name="Physics", code="PHY", theory=True, practical=True,
                        internal=True, theory_max=70, practical_max=20, internal_max=10),
                Subject(name="Chemistry", code="CHE", theory=True, practical=True,
                        internal=True, theory_max=70, practical_max=20, internal_max=10),
                Subject(name="Computer Science", code="CS", theory=True, practical=True,
                        internal=True, theory_max=70, practical_max=20, internal_max=10),
            ])

        if not db.query(Teacher).filter_by(username="admin").first():
            db.add(Teacher(
                username="admin",
                name="Administrator",
                password_hash=hash_password("Admin@123"),
                role="admin"
            ))

        db.commit()

        classes = db.query(ClassSection).all()
        subjects = db.query(Subject).all()

        for c in classes:
            for s in subjects:
                if not db.query(ClassSubject).filter_by(
                    class_id=c.id, subject_id=s.id
                ).first():
                    db.add(ClassSubject(class_id=c.id, subject_id=s.id))

        db.commit()
    finally:
        db.close()


seed_database()


# ---------------- HELPERS ----------------

def parse_id(value):
    if not value:
        return None
    try:
        return int(str(value).split("|", 1)[0].strip())
    except Exception:
        return None


def make_choices(rows):
    return [f"{row[0]} | {row[1]}" for row in rows]


def years():
    db = SessionLocal()
    try:
        return make_choices([
            (x.id, x.name)
            for x in db.query(AcademicYear).filter_by(active=True)
        ])
    finally:
        db.close()


def classes():
    db = SessionLocal()
    try:
        return make_choices([
            (x.id, x.name)
            for x in db.query(ClassSection).order_by(ClassSection.name)
        ])
    finally:
        db.close()


def exams():
    db = SessionLocal()
    try:
        return make_choices([
            (x.id, x.name)
            for x in db.query(Exam).filter_by(active=True)
        ])
    finally:
        db.close()


def subjects_for_class(class_value):
    class_id = parse_id(class_value)
    if not class_id:
        return []

    db = SessionLocal()
    try:
        rows = (
            db.query(Subject)
            .join(ClassSubject, ClassSubject.subject_id == Subject.id)
            .filter(
                ClassSubject.class_id == class_id,
                Subject.active == True
            )
            .order_by(Subject.name)
            .all()
        )
        return [f"{s.id} | {s.name}" for s in rows]
    finally:
        db.close()


def subject_pattern(subject_value):
    subject_id = parse_id(subject_value)
    if not subject_id:
        return "Select a subject."

    db = SessionLocal()
    try:
        s = db.get(Subject, subject_id)
        if not s:
            return "Subject not found."

        items = []
        if s.theory:
            items.append(f"Theory / {s.theory_max}")
        if s.practical:
            items.append(f"Practical / {s.practical_max}")
        if s.internal:
            items.append(f"Internal / {s.internal_max}")

        total = s.theory_max + s.practical_max + s.internal_max
        return "**Mark Pattern:** " + " + ".join(items) + f" = **{total}**"
    finally:
        db.close()


# ---------------- MARK ENTRY ----------------

def load_marks(class_value, year_value, exam_value, subject_value):
    class_id = parse_id(class_value)
    year_id = parse_id(year_value)
    exam_id = parse_id(exam_value)
    subject_id = parse_id(subject_value)

    if not all([class_id, year_id, exam_id, subject_id]):
        return [], "Please select Academic Year, Class, Exam and Subject."

    db = SessionLocal()
    try:
        subject = db.get(Subject, subject_id)

        students = (
            db.query(Student)
            .filter_by(class_id=class_id, active=True)
            .order_by(Student.roll_no, Student.name)
            .all()
        )

        headers = ["ID", "Roll No", "Student Name", "Theory"]
        if subject.practical:
            headers.append("Practical")
        if subject.internal:
            headers.append("Internal")
        headers.append("Total")

        rows = []
        for st in students:
            m = db.query(Mark).filter_by(
                academic_year_id=year_id,
                exam_id=exam_id,
                student_id=st.id,
                subject_id=subject_id
            ).first()

            row = [
                st.id,
                st.roll_no or "",
                st.name,
                m.theory if m else 0
            ]

            if subject.practical:
                row.append(m.practical if m else 0)

            if subject.internal:
                row.append(m.internal if m else 0)

            row.append(m.total if m else 0)
            rows.append(row)

        return rows, subject_pattern(subject_value)
    finally:
        db.close()


def recalculate(table_data):
    if not table_data:
        return table_data

    result = []
    for row in table_data:
        row = list(row)
        try:
            total = sum(int(x or 0) for x in row[3:-1])
            row[-1] = total
        except Exception:
            pass
        result.append(row)

    return result


def save_marks(class_value, year_value, exam_value, subject_value, table_data):
    class_id = parse_id(class_value)
    year_id = parse_id(year_value)
    exam_id = parse_id(exam_value)
    subject_id = parse_id(subject_value)

    if not all([class_id, year_id, exam_id, subject_id]):
        return "❌ Select all four selections first."

    db = SessionLocal()
    try:
        subject = db.get(Subject, subject_id)

        for row in table_data or []:
            if not row:
                continue

            student_id = int(row[0])
            pos = 3

            theory = int(row[pos] or 0)
            pos += 1

            practical = 0
            internal = 0

            if subject.practical:
                practical = int(row[pos] or 0)
                pos += 1

            if subject.internal:
                internal = int(row[pos] or 0)
                pos += 1

            if theory < 0 or theory > subject.theory_max:
                raise ValueError(f"Theory must be 0-{subject.theory_max}")

            if practical < 0 or practical > subject.practical_max:
                raise ValueError(f"Practical must be 0-{subject.practical_max}")

            if internal < 0 or internal > subject.internal_max:
                raise ValueError(f"Internal must be 0-{subject.internal_max}")

            total = theory + practical + internal

            mark = db.query(Mark).filter_by(
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
        return f"❌ {e}"
    finally:
        db.close()


# ---------------- CONSOLIDATED MARK LIST ----------------

def mark_list(class_value, year_value, exam_value):
    class_id = parse_id(class_value)
    year_id = parse_id(year_value)
    exam_id = parse_id(exam_value)

    if not all([class_id, year_id, exam_id]):
        return [], "Please select Academic Year, Exam and Class."

    db = SessionLocal()
    try:
        cls = db.get(ClassSection, class_id)

        subjects = (
            db.query(Subject)
            .join(ClassSubject, ClassSubject.subject_id == Subject.id)
            .filter(
                ClassSubject.class_id == class_id,
                Subject.active == True
            )
            .order_by(Subject.name)
            .all()
        )

        students = (
            db.query(Student)
            .filter_by(class_id=class_id, active=True)
            .order_by(Student.roll_no, Student.name)
            .all()
        )

        headers = ["Roll No", "Student Name"]

        for s in subjects:
            headers.append(f"{s.name} Theory")
            if s.practical:
                headers.append(f"{s.name} Practical")
            if s.internal:
                headers.append(f"{s.name} Internal")
            headers.append(f"{s.name} Total")

        headers.append("Grand Total")

        rows = []

        for st in students:
            row = [st.roll_no or "", st.name]
            grand = 0

            for s in subjects:
                m = db.query(Mark).filter_by(
                    academic_year_id=year_id,
                    exam_id=exam_id,
                    student_id=st.id,
                    subject_id=s.id
                ).first()

                theory = m.theory if m else 0
                practical = m.practical if m else 0
                internal = m.internal if m else 0
                total = m.total if m else theory + practical + internal

                row.append(theory)

                if s.practical:
                    row.append(practical)

                if s.internal:
                    row.append(internal)

                row.append(total)
                grand += total

            row.append(grand)
            rows.append(row)

        return rows, f"### 📊 {cls.name} — Consolidated Mark List"
    finally:
        db.close()


# ---------------- LOGIN ----------------

def login(username, password):
    db = SessionLocal()
    try:
        teacher = db.query(Teacher).filter_by(
            username=(username or "").strip(),
            active=True
        ).first()

        if not teacher or not verify_password(
            password or "", teacher.password_hash
        ):
            return "❌ Invalid username or password.", gr.update(visible=False)

        return f"✅ Welcome, {teacher.name}", gr.update(visible=True)
    finally:
        db.close()


# ---------------- UI ----------------

css = """
.gradio-container { max-width: 1450px !important; }
#title { text-align:center; }
"""

with gr.Blocks(title="School Mark Entry System", css=css) as demo:

    gr.Markdown("# 🏫 School Mark Entry System", elem_id="title")
    gr.Markdown("### Login to continue")

    with gr.Row():
        login_user = gr.Textbox(label="Username")
        login_pass = gr.Textbox(label="Password", type="password")
        login_button = gr.Button("🔐 Login", variant="primary")

    login_message = gr.Markdown()

    with gr.Column(visible=False) as app_area:

        with gr.Tabs():

            # ================= MARK ENTRY =================
            with gr.Tab("📝 Mark Entry"):
                gr.Markdown("## Mark Entry")

                with gr.Row():
                    me_year = gr.Dropdown(
                        choices=years(), label="Academic Year"
                    )
                    me_class = gr.Dropdown(
                        choices=classes(), label="Class"
                    )
                    me_exam = gr.Dropdown(
                        choices=exams(), label="Exam"
                    )
                    me_subject = gr.Dropdown(
                        choices=[], label="Subject"
                    )

                me_class.change(
                    subjects_for_class,
                    inputs=me_class,
                    outputs=me_subject
                )

                me_pattern = gr.Markdown("Select a subject.")

                me_subject.change(
                    subject_pattern,
                    inputs=me_subject,
                    outputs=me_pattern
                )

                me_load = gr.Button("Load Students")
                me_table = gr.Dataframe(
                    headers=[
                        "ID", "Roll No", "Student Name",
                        "Theory", "Internal", "Total"
                    ],
                    interactive=True,
                    wrap=True
                )

                me_load.click(
                    load_marks,
                    inputs=[me_class, me_year, me_exam, me_subject],
                    outputs=[me_table, me_pattern]
                )

                me_table.change(
                    recalculate,
                    inputs=me_table,
                    outputs=me_table
                )

                me_save = gr.Button(
                    "💾 Save Marks",
                    variant="primary"
                )
                me_result = gr.Markdown()

                me_save.click(
                    save_marks,
                    inputs=[
                        me_class, me_year, me_exam,
                        me_subject, me_table
                    ],
                    outputs=me_result
                )

            # ================= VIEW MARKS =================
            with gr.Tab("👁️ View Marks"):
                gr.Markdown("## Subject-wise View")

                with gr.Row():
                    vm_year = gr.Dropdown(
                        choices=years(), label="Academic Year"
                    )
                    vm_class = gr.Dropdown(
                        choices=classes(), label="Class"
                    )
                    vm_exam = gr.Dropdown(
                        choices=exams(), label="Exam"
                    )
                    vm_subject = gr.Dropdown(
                        choices=[], label="Subject"
                    )

                vm_class.change(
                    subjects_for_class,
                    inputs=vm_class,
                    outputs=vm_subject
                )

                vm_button = gr.Button("View Marks")
                vm_result = gr.Markdown()
                vm_table = gr.Dataframe(
                    interactive=False,
                    wrap=True
                )

                vm_button.click(
                    load_marks,
                    inputs=[
                        vm_class, vm_year,
                        vm_exam, vm_subject
                    ],
                    outputs=[vm_table, vm_result]
                )

            # ================= MARK LIST =================
            with gr.Tab("📊 Mark List / Print"):
                gr.Markdown(
                    "## Consolidated Mark List\n"
                    "Select Academic Year + Exam + Class. "
                    "All students and all subjects will be shown."
                )

                with gr.Row():
                    ml_year = gr.Dropdown(
                        choices=years(), label="Academic Year"
                    )
                    ml_exam = gr.Dropdown(
                        choices=exams(), label="Exam"
                    )
                    ml_class = gr.Dropdown(
                        choices=classes(), label="Class"
                    )

                ml_button = gr.Button(
                    "📊 Generate Mark List",
                    variant="primary"
                )

                ml_result = gr.Markdown()
                ml_table = gr.Dataframe(
                    interactive=False,
                    wrap=True
                )

                ml_button.click(
                    mark_list,
                    inputs=[ml_class, ml_year, ml_exam],
                    outputs=[ml_table, ml_result]
                )

                gr.Markdown(
                    "🖨️ After generating the list, use your browser's "
                    "Print option (Ctrl+P) to print or save as PDF."
                )

    login_button.click(
        login,
        inputs=[login_user, login_pass],
        outputs=[login_message, app_area]
    )

    gr.Markdown(
        "Initial admin login: **admin** / **Admin@123**. "
        "Change this before real school use."
    )


if __name__ == "__main__":
    port = int(os.getenv("PORT", "7860"))
    demo.launch(server_name="0.0.0.0", server_port=port)
