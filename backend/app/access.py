from fastapi import HTTPException
from sqlalchemy import select
from .models import Classroom, Enrollment, TeacherAssignment, Subject, AuditLog, Notification, User


def tenant_record(db, model, record_id, user):
    record = db.get(model, record_id)
    if not record or record.school_id != user.school_id:
        raise HTTPException(404, 'Record not found')
    return record


def class_ids(db, user):
    query = select(Classroom.id).where(Classroom.school_id == user.school_id)
    if user.role == 'teacher':
        query = query.join(TeacherAssignment).where(TeacherAssignment.teacher_id == user.id)
    elif user.role == 'student':
        query = query.join(Enrollment).where(Enrollment.student_id == user.id)
    return list(db.scalars(query))


def classroom(db, class_id, user):
    obj = tenant_record(db, Classroom, class_id, user)
    if class_id not in class_ids(db, user):
        raise HTTPException(403, 'You are not assigned to this class')
    return obj


def subject(db, subject_id, user):
    return tenant_record(db, Subject, subject_id, user)


def audit(db, user, action, details):
    db.add(AuditLog(school_id=user.school_id, actor_id=user.id, action=action, details=details))


def notify_class(db, user, class_id, title, body):
    for student_id in db.scalars(select(Enrollment.student_id).where(Enrollment.class_id == class_id)):
        db.add(Notification(school_id=user.school_id, user_id=student_id, title=title, body=body))


def public_user(user):
    return {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role, 'school_id': user.school_id}
