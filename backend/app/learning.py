from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile
from fastapi.responses import Response
from sqlalchemy import select, func
from sqlalchemy.orm import Session as DB
from .db import get_db
from .models import *
from .schemas import MaterialIn, HomeworkIn, SubmitIn, ReviewIn
from .security import current_user, require
from .access import classroom, class_ids, tenant_record, subject, audit, notify_class
from .storage import read_pdf, store_pdf, load_pdf

router = APIRouter(prefix='/api')


def allowed_material(db, material_id, user):
    material = tenant_record(db, Material, material_id, user)
    classroom(db, material.class_id, user)
    if user.role == 'student' and not material.approved:
        raise HTTPException(404, 'Material not found')
    return material


@router.get('/materials')
def materials(user: User = Depends(current_user), db: DB = Depends(get_db)):
    query = select(Material).where(Material.class_id.in_(class_ids(db, user)))
    if user.role == 'student':
        query = query.where(Material.approved == True)
    return [{'id': m.id, 'title': m.title, 'class_id': m.class_id, 'subject_id': m.subject_id,
             'content': m.content, 'approved': m.approved, 'has_file': bool(m.file_key), 'created_at': m.created_at.isoformat()}
            for m in db.scalars(query.order_by(Material.created_at.desc()))]


@router.post('/materials', status_code=201)
def create_material(data: MaterialIn, user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'teacher', 'admin')
    classroom(db, data.class_id, user)
    subject(db, data.subject_id, user)
    row = Material(**data.model_dump(), school_id=user.school_id, created_by=user.id)
    db.add(row)
    db.flush()
    if row.approved:
        notify_class(db, user, row.class_id, 'New study material', row.title)
    audit(db, user, 'material_created', {'material_id': row.id, 'approved': row.approved})
    db.commit()
    return {'id': row.id}


@router.post('/materials/upload', status_code=201)
async def upload_material(class_id: int = Form(...), subject_id: int = Form(...), title: str = Form(...),
                          file: UploadFile = File(...), user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'teacher', 'admin')
    classroom(db, class_id, user)
    subject(db, subject_id, user)
    if not 3 <= len(title.strip()) <= 160:
        raise HTTPException(422, 'Title must be 3–160 characters')
    data, content = await read_pdf(file)
    key = store_pdf(user.school_id, data)
    row = Material(class_id=class_id, subject_id=subject_id, title=title, content=content, file_key=key,
                   school_id=user.school_id, created_by=user.id, approved=False)
    db.add(row)
    db.flush()
    audit(db, user, 'pdf_uploaded', {'material_id': row.id})
    db.commit()
    return {'id': row.id}


@router.post('/materials/{material_id}/approve')
def approve_material(material_id: int, user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'teacher', 'admin')
    row = allowed_material(db, material_id, user)
    if not row.approved:
        row.approved = True
        notify_class(db, user, row.class_id, 'New study material', row.title)
        audit(db, user, 'material_approved', {'material_id': row.id})
    db.commit()
    return {'ok': True}


@router.get('/materials/{material_id}/download')
def download(material_id: int, user: User = Depends(current_user), db: DB = Depends(get_db)):
    row = allowed_material(db, material_id, user)
    if not row.file_key:
        raise HTTPException(404, 'This lesson contains text only')
    try:
        data = load_pdf(row.file_key)
    except FileNotFoundError:
        raise HTTPException(404, 'Stored file unavailable; contact your school')
    return Response(data, media_type='application/pdf', headers={'Content-Disposition': f'attachment; filename="lesson-{row.id}.pdf"'})


@router.get('/homework')
def homework(user: User = Depends(current_user), db: DB = Depends(get_db)):
    result = []
    for h in db.scalars(select(Homework).where(Homework.class_id.in_(class_ids(db, user))).order_by(Homework.due_date)):
        query = select(Submission).where(Submission.homework_id == h.id)
        if user.role == 'student':
            query = query.where(Submission.student_id == user.id)
        subs = list(db.scalars(query))
        result.append({'id': h.id, 'class_id': h.class_id, 'subject_id': h.subject_id, 'title': h.title,
                       'instructions': h.instructions, 'due_date': str(h.due_date), 'submission_count': len(subs),
                       'student_count': db.scalar(select(func.count()).select_from(Enrollment).where(Enrollment.class_id == h.class_id)),
                       'my_submission': {'answer': subs[0].answer, 'status': subs[0].status, 'feedback': subs[0].feedback} if user.role == 'student' and subs else None})
    return result


@router.post('/homework', status_code=201)
def create_homework(data: HomeworkIn, user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'teacher', 'admin')
    classroom(db, data.class_id, user)
    subject(db, data.subject_id, user)
    row = Homework(**data.model_dump(), school_id=user.school_id, created_by=user.id)
    db.add(row)
    db.flush()
    notify_class(db, user, row.class_id, 'New homework', f'{row.title} · Due {row.due_date}')
    audit(db, user, 'homework_created', {'homework_id': row.id})
    db.commit()
    return {'id': row.id}


@router.post('/homework/{homework_id}/submit')
def submit(homework_id: int, data: SubmitIn, user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'student')
    h = tenant_record(db, Homework, homework_id, user)
    classroom(db, h.class_id, user)
    row = db.scalar(select(Submission).where(Submission.homework_id == h.id, Submission.student_id == user.id).with_for_update())
    if row and row.status == 'complete':
        raise HTTPException(409, 'Your teacher has already marked this complete')
    if row and row.status == 'submitted' and row.answer == data.answer:
        return {'ok': True}  # Exact retry: no timestamp or notification changes.
    needs_notification = row is None or row.status == 'needs_revision'
    if not row:
        row = Submission(school_id=user.school_id, homework_id=h.id, student_id=user.id)
        db.add(row)
    row.answer, row.status, row.submitted_at = data.answer, 'submitted', now()
    if needs_notification:
        db.add(Notification(school_id=user.school_id, user_id=h.created_by, title='Homework submitted', body=f'A submission for {h.title} is ready to review.'))
    db.commit()
    return {'ok': True}


@router.get('/homework/{homework_id}/submissions')
def submissions(homework_id: int, user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'teacher', 'admin')
    h = tenant_record(db, Homework, homework_id, user)
    classroom(db, h.class_id, user)
    return [{'id': s.id, 'student_name': u.name, 'answer': s.answer, 'status': s.status,
             'feedback': s.feedback, 'submitted_at': s.submitted_at.isoformat()}
            for s, u in db.execute(select(Submission, User).join(User, User.id == Submission.student_id).where(Submission.homework_id == h.id))]


@router.post('/submissions/{submission_id}/review')
def review(submission_id: int, data: ReviewIn, user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'teacher', 'admin')
    s = tenant_record(db, Submission, submission_id, user)
    h = tenant_record(db, Homework, s.homework_id, user)
    classroom(db, h.class_id, user)
    s.status, s.feedback = data.status, data.feedback
    audit(db, user, 'submission_reviewed', {'submission_id': s.id, 'status': data.status})
    db.add(Notification(school_id=user.school_id, user_id=s.student_id, title='Homework reviewed', body=f'{h.title}: {data.status.replace("_", " ")}'))
    db.commit()
    return {'ok': True}
