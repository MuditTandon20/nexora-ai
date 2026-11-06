from datetime import date
from zoneinfo import ZoneInfo
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select, func, delete
from sqlalchemy.orm import Session as DB
from .db import get_db
from .models import *
from .schemas import *
from .security import current_user, require, passwords, DUMMY_HASH, create_session
from .access import classroom, class_ids, tenant_record, subject, audit, notify_class, public_user
from .config import settings

router = APIRouter(prefix='/api')


def today():
    return datetime.now(ZoneInfo('Asia/Kolkata')).date()


@router.post('/auth/login')
def login(data: LoginIn, response: Response, db: DB = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == data.email.strip().lower()))
    valid = passwords.verify(data.password, user.password_hash if user else DUMMY_HASH)
    if not user or not valid or not user.active:
        raise HTTPException(401, 'Email or password is incorrect')
    raw, session = create_session(db, user)
    db.commit()
    response.set_cookie('nexora_session', raw, httponly=True, secure=settings().environment == 'production',
                        samesite='lax', max_age=settings().session_hours * 3600, path='/')
    return {'user': public_user(user), 'csrf_token': session.csrf_token}


@router.get('/auth/me')
def me(request: Request, user: User = Depends(current_user), db: DB = Depends(get_db)):
    return {'user': public_user(user), 'school': db.get(School, user.school_id).name,
            'csrf_token': request.state.session.csrf_token}


@router.post('/auth/logout')
def logout(request: Request, response: Response, user: User = Depends(current_user), db: DB = Depends(get_db)):
    db.delete(request.state.session)
    db.commit()
    response.delete_cookie('nexora_session', path='/')
    return {'ok': True}


@router.post('/auth/password')
def password(data: PasswordIn, response: Response, user: User = Depends(current_user), db: DB = Depends(get_db)):
    if not passwords.verify(data.current_password, user.password_hash):
        raise HTTPException(400, 'Current password is incorrect')
    user.password_hash = passwords.hash(data.new_password)
    db.execute(delete(Session).where(Session.user_id == user.id))
    audit(db, user, 'password_changed', {})
    db.commit()
    response.delete_cookie('nexora_session', path='/')
    return {'ok': True}


@router.get('/users')
def users(user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'admin')
    return [public_user(u) for u in db.scalars(select(User).where(User.school_id == user.school_id).order_by(User.name))]


@router.post('/users', status_code=201)
def create_user(data: UserIn, user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'admin')
    record = User(school_id=user.school_id, name=data.name.strip(), email=data.email.strip().lower(),
                  password_hash=passwords.hash(data.password), role=data.role)
    db.add(record)
    db.flush()
    audit(db, user, 'account_created', {'user_id': record.id, 'role': record.role})
    db.commit()
    return public_user(record)


@router.get('/subjects')
def subjects(user: User = Depends(current_user), db: DB = Depends(get_db)):
    return [{'id': s.id, 'name': s.name} for s in db.scalars(select(Subject).where(Subject.school_id == user.school_id))]


@router.get('/classes')
def classes(user: User = Depends(current_user), db: DB = Depends(get_db)):
    result = []
    for c in db.scalars(select(Classroom).where(Classroom.id.in_(class_ids(db, user))).order_by(Classroom.name)):
        result.append({'id': c.id, 'name': c.name, 'grade': c.grade,
                       'students': db.scalar(select(func.count()).select_from(Enrollment).where(Enrollment.class_id == c.id))})
    return result


@router.post('/classes', status_code=201)
def create_class(data: ClassIn, user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'admin')
    for ids, role in [(data.teacher_ids, 'teacher'), (data.student_ids, 'student')]:
        if len(set(ids)) != len(ids):
            raise HTTPException(422, 'Duplicate member IDs')
        for member_id in ids:
            member = tenant_record(db, User, member_id, user)
            if member.role != role or not member.active:
                raise HTTPException(422, f'Invalid {role} account')
    record = Classroom(school_id=user.school_id, name=data.name.strip(), grade=data.grade)
    db.add(record)
    db.flush()
    for tid in data.teacher_ids:
        db.add(TeacherAssignment(class_id=record.id, teacher_id=tid))
    for sid in data.student_ids:
        db.add(Enrollment(class_id=record.id, student_id=sid))
    audit(db, user, 'class_created', {'class_id': record.id})
    db.commit()
    return {'id': record.id, 'name': record.name}


@router.get('/classes/{class_id}/roster')
def roster(class_id: int, user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'teacher', 'admin')
    classroom(db, class_id, user)
    return [{'id': u.id, 'name': u.name} for u in db.scalars(select(User).join(Enrollment, Enrollment.student_id == User.id)
                                                        .where(Enrollment.class_id == class_id).order_by(User.name))]


@router.get('/classes/{class_id}/attendance')
def attendance(class_id: int, day: date, user: User = Depends(current_user), db: DB = Depends(get_db)):
    classroom(db, class_id, user)
    query = select(Attendance).where(Attendance.class_id == class_id, Attendance.day == day)
    if user.role == 'student':
        query = query.where(Attendance.student_id == user.id)
    records = list(db.scalars(query))
    return {'saved': bool(records), 'version': max((r.updated_at.isoformat() for r in records), default=None),
            'records': [{'student_id': r.student_id, 'status': r.status} for r in records]}


@router.post('/classes/{class_id}/attendance')
def save_attendance(class_id: int, data: AttendanceIn, user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'teacher', 'admin')
    # Lock the class row to serialize concurrent saves on PostgreSQL.
    db.scalar(select(Classroom).where(Classroom.id == class_id).with_for_update())
    classroom(db, class_id, user)
    if not data.confirmed or data.day > today():
        raise HTTPException(422, 'Confirm attendance and select today or an earlier date')
    students = list(db.scalars(select(Enrollment.student_id).where(Enrollment.class_id == class_id)))
    if not students or not set(data.absent_ids).issubset(students):
        raise HTTPException(422, 'Attendance must refer to enrolled students')
    existing = list(db.scalars(select(Attendance).where(Attendance.class_id == class_id, Attendance.day == data.day)))
    version = max((r.updated_at.isoformat() for r in existing), default=None)
    if version != data.expected_version:
        raise HTTPException(409, 'Attendance changed; reload before saving')
    if existing and len(data.correction_reason.strip()) < 5:
        raise HTTPException(422, 'A correction reason is required')
    old = {r.student_id: r.status for r in existing}
    by_student = {r.student_id: r for r in existing}
    stamp = now()
    for sid in students:
        row = by_student.get(sid)
        if not row:
            row = Attendance(school_id=user.school_id, class_id=class_id, student_id=sid, day=data.day)
            db.add(row)
        row.status = 'absent' if sid in data.absent_ids else 'present'
        row.marked_by = user.id
        row.updated_at = stamp
    audit(db, user, 'attendance_corrected' if existing else 'attendance_saved',
          {'class_id': class_id, 'day': str(data.day), 'before': {str(k): v for k, v in old.items()},
           'absent_ids': data.absent_ids, 'reason': data.correction_reason})
    db.commit()
    return {'ok': True, 'present': len(students) - len(set(data.absent_ids)), 'total': len(students)}


@router.get('/attendance/history')
def attendance_history(user: User = Depends(current_user), db: DB = Depends(get_db)):
    query = select(Attendance).where(Attendance.class_id.in_(class_ids(db, user)))
    if user.role == 'student':
        query = query.where(Attendance.student_id == user.id)
    return [{'class_id': r.class_id, 'day': str(r.day), 'student_id': r.student_id, 'status': r.status}
            for r in db.scalars(query.order_by(Attendance.day.desc()).limit(1000))]


@router.get('/dashboard')
def dashboard(user: User = Depends(current_user), db: DB = Depends(get_db)):
    ids = class_ids(db, user)
    att = select(Attendance).where(Attendance.class_id.in_(ids), Attendance.day == today())
    if user.role == 'student':
        att = att.where(Attendance.student_id == user.id)
    rows = list(db.scalars(att))
    hw = list(db.scalars(select(Homework).where(Homework.class_id.in_(ids)).order_by(Homework.due_date)))
    sub_query = select(Submission).join(Homework, Homework.id == Submission.homework_id).where(Homework.class_id.in_(ids))
    if user.role == 'student':
        sub_query = sub_query.where(Submission.student_id == user.id)
    submissions = list(db.scalars(sub_query))
    return {'date': str(today()), 'classes': len(ids), 'attendance_present': sum(r.status == 'present' for r in rows),
            'attendance_total': len(rows), 'attendance_status': rows[0].status if user.role == 'student' and rows else None,
            'pending_review': sum(s.status == 'submitted' for s in submissions),
            'homework': [{'id': h.id, 'title': h.title, 'due_date': str(h.due_date), 'class_id': h.class_id} for h in hw[:6]],
            'materials': db.scalar(select(func.count()).select_from(Material).where(Material.class_id.in_(ids), Material.approved == True)),
            'announcements': [{'id': n.id, 'title': n.title, 'body': n.body} for n in db.scalars(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(4))]}


@router.get('/notifications')
def notifications(user: User = Depends(current_user), db: DB = Depends(get_db)):
    result = [{'id': n.id, 'title': n.title, 'body': n.body, 'read': n.read, 'created_at': n.created_at.isoformat()}
              for n in db.scalars(select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(100))]
    # Deadlines are derived from current assignments rather than requiring a scheduler.
    query = select(Homework).where(Homework.class_id.in_(class_ids(db, user)), Homework.due_date >= today())
    for h in db.scalars(query):
        if (h.due_date - today()).days <= 2:
            result.append({'id': f'due-{h.id}', 'title': 'Upcoming deadline', 'body': f'{h.title} is due {h.due_date}', 'read': True, 'created_at': ''})
    return result


@router.post('/notifications/{notification_id}/read')
def read_notification(notification_id: int, user: User = Depends(current_user), db: DB = Depends(get_db)):
    record = tenant_record(db, Notification, notification_id, user)
    if record.user_id != user.id:
        raise HTTPException(404, 'Notification not found')
    record.read = True
    db.commit()
    return {'ok': True}


@router.post('/announcements')
def announcement(data: AnnouncementIn, user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'admin')
    for uid in db.scalars(select(User.id).where(User.school_id == user.school_id, User.active == True)):
        db.add(Notification(school_id=user.school_id, user_id=uid, title=data.title, body=data.body))
    audit(db, user, 'announcement_published', {'title': data.title})
    db.commit()
    return {'ok': True}


@router.get('/audit')
def audit_history(user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'admin')
    return [{'id': a.id, 'action': a.action, 'actor_id': a.actor_id, 'details': a.details, 'created_at': a.created_at.isoformat()}
            for a in db.scalars(select(AuditLog).where(AuditLog.school_id == user.school_id).order_by(AuditLog.id.desc()).limit(100))]
