from datetime import date, datetime, timezone
from sqlalchemy import JSON, Boolean, CheckConstraint, Date, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base


def now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class School(Base):
    __tablename__ = 'schools'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(160))


class Tenant:
    school_id: Mapped[int] = mapped_column(ForeignKey('schools.id'), index=True)


class User(Tenant, Base):
    __tablename__ = 'users'
    __table_args__ = (CheckConstraint("role IN ('admin','teacher','student')"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(200), unique=True)
    password_hash: Mapped[str] = mapped_column(Text)
    role: Mapped[str] = mapped_column(String(20))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Session(Base):
    __tablename__ = 'sessions'
    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    csrf_token: Mapped[str] = mapped_column(String(100))
    expires_at: Mapped[datetime] = mapped_column(DateTime, index=True)


class Classroom(Tenant, Base):
    __tablename__ = 'classes'
    __table_args__ = (UniqueConstraint('school_id', 'name'), CheckConstraint('grade >= 1 AND grade <= 10'))
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))
    grade: Mapped[int] = mapped_column(Integer)


class Subject(Tenant, Base):
    __tablename__ = 'subjects'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(80))


class Enrollment(Base):
    __tablename__ = 'enrollments'
    __table_args__ = (UniqueConstraint('class_id', 'student_id'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey('classes.id'), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)


class TeacherAssignment(Base):
    __tablename__ = 'teacher_assignments'
    __table_args__ = (UniqueConstraint('class_id', 'teacher_id'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey('classes.id'), index=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)


class Attendance(Tenant, Base):
    __tablename__ = 'attendance_records'
    __table_args__ = (UniqueConstraint('class_id', 'day', 'student_id'), CheckConstraint("status IN ('present','absent')"))
    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey('classes.id'), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    day: Mapped[date] = mapped_column(Date, index=True)
    status: Mapped[str] = mapped_column(String(12))
    marked_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    updated_at: Mapped[datetime] = mapped_column(default=now, onupdate=now)


class Material(Tenant, Base):
    __tablename__ = 'study_materials'
    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey('classes.id'), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey('subjects.id'))
    title: Mapped[str] = mapped_column(String(160))
    content: Mapped[str] = mapped_column(Text)
    file_key: Mapped[str | None] = mapped_column(String(200))
    approved: Mapped[bool] = mapped_column(default=False)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))
    created_at: Mapped[datetime] = mapped_column(default=now)


class Homework(Tenant, Base):
    __tablename__ = 'homework'
    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey('classes.id'), index=True)
    subject_id: Mapped[int] = mapped_column(ForeignKey('subjects.id'))
    title: Mapped[str] = mapped_column(String(160))
    instructions: Mapped[str] = mapped_column(Text)
    due_date: Mapped[date] = mapped_column(Date)
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))


class Submission(Tenant, Base):
    __tablename__ = 'homework_submissions'
    __table_args__ = (UniqueConstraint('homework_id', 'student_id'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    homework_id: Mapped[int] = mapped_column(ForeignKey('homework.id'), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    answer: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default='submitted')
    feedback: Mapped[str] = mapped_column(Text, default='')
    submitted_at: Mapped[datetime] = mapped_column(default=now)


class Quiz(Tenant, Base):
    __tablename__ = 'quizzes'
    id: Mapped[int] = mapped_column(primary_key=True)
    class_id: Mapped[int] = mapped_column(ForeignKey('classes.id'), index=True)
    material_id: Mapped[int] = mapped_column(ForeignKey('study_materials.id'))
    title: Mapped[str] = mapped_column(String(160))
    summary: Mapped[str] = mapped_column(Text)
    language: Mapped[str] = mapped_column(String(10), default='en')
    published: Mapped[bool] = mapped_column(default=False)
    model: Mapped[str] = mapped_column(String(120))
    prompt_version: Mapped[str] = mapped_column(String(30))
    created_by: Mapped[int] = mapped_column(ForeignKey('users.id'))


class QuizQuestion(Base):
    __tablename__ = 'quiz_questions'
    id: Mapped[int] = mapped_column(primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey('quizzes.id'), index=True)
    kind: Mapped[str] = mapped_column(String(20))
    question: Mapped[str] = mapped_column(Text)
    options: Mapped[list] = mapped_column(JSON, default=list)
    answer: Mapped[str] = mapped_column(Text)
    explanation: Mapped[str] = mapped_column(Text)
    source_quote: Mapped[str] = mapped_column(Text)
    topic: Mapped[str] = mapped_column(String(100))


class Flashcard(Base):
    __tablename__ = 'flashcards'
    id: Mapped[int] = mapped_column(primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey('quizzes.id'), index=True)
    front: Mapped[str] = mapped_column(Text)
    back: Mapped[str] = mapped_column(Text)


class QuizAttempt(Tenant, Base):
    __tablename__ = 'quiz_attempts'
    __table_args__ = (UniqueConstraint('quiz_id', 'student_id', 'mode', 'day'),)
    id: Mapped[int] = mapped_column(primary_key=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey('quizzes.id'))
    student_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    mode: Mapped[str] = mapped_column(String(10))
    day: Mapped[date] = mapped_column(Date)
    score: Mapped[int] = mapped_column(Integer)
    total: Mapped[int] = mapped_column(Integer)
    responses: Mapped[list] = mapped_column(JSON)


class Notification(Tenant, Base):
    __tablename__ = 'notifications'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    title: Mapped[str] = mapped_column(String(200))
    body: Mapped[str] = mapped_column(Text)
    read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=now)


class AuditLog(Tenant, Base):
    __tablename__ = 'audit_logs'
    id: Mapped[int] = mapped_column(primary_key=True)
    actor_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    action: Mapped[str] = mapped_column(String(80))
    details: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(default=now)


class AIEvent(Tenant, Base):
    __tablename__ = 'ai_events'
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'), index=True)
    feature: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(120))
    prompt_version: Mapped[str] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(30))
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost: Mapped[float] = mapped_column(default=0)
    error: Mapped[str] = mapped_column(String(200), default='')
    created_at: Mapped[datetime] = mapped_column(default=now, index=True)


Index('ix_material_class_approved', Material.class_id, Material.approved)
