from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, delete, func
from sqlalchemy.orm import Session as DB
from .db import get_db
from .models import *
from .schemas import *
from .security import current_user, require
from .access import classroom, class_ids, tenant_record, audit, notify_class
from .learning import allowed_material
from .routes import today
from .ai import generate, retrieve, validate_grounding, PROMPT_VERSION
from .config import settings

router = APIRouter(prefix='/api')


def allowed_quiz(db, quiz_id, user):
    row = tenant_record(db, Quiz, quiz_id, user)
    classroom(db, row.class_id, user)
    if user.role == 'student' and not row.published:
        raise HTTPException(404, 'Quiz not found')
    return row


def write_pack(db, quiz, pack):
    db.execute(delete(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id))
    db.execute(delete(Flashcard).where(Flashcard.quiz_id == quiz.id))
    quiz.title, quiz.summary = pack.title, pack.summary
    for q in pack.questions:
        db.add(QuizQuestion(quiz_id=quiz.id, **q.model_dump()))
    for card in pack.flashcards:
        db.add(Flashcard(quiz_id=quiz.id, **card.model_dump()))


@router.get('/ai/status')
def ai_status(user: User = Depends(current_user)):
    cfg = settings()
    return {'configured': bool(cfg.ai_enabled and cfg.llm_base_url and cfg.llm_api_key and cfg.llm_model), 'daily_limit': cfg.ai_daily_limit}


@router.post('/ai/generate', status_code=201)
def generate_pack(data: GenerateIn, user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'teacher', 'admin')
    material = allowed_material(db, data.material_id, user)
    if not material.approved:
        raise HTTPException(422, 'Approve the source material first')
    c = classroom(db, material.class_id, user)
    pack = generate(db, user, 'quiz', material.content, c.grade, data.language)
    quiz = Quiz(school_id=user.school_id, class_id=c.id, material_id=material.id, title=pack.title,
                summary=pack.summary, language=data.language, model=settings().llm_model,
                prompt_version=PROMPT_VERSION, created_by=user.id)
    db.add(quiz)
    db.flush()
    write_pack(db, quiz, pack)
    audit(db, user, 'learning_pack_generated', {'quiz_id': quiz.id})
    db.commit()
    return {'id': quiz.id}


@router.post('/ai/tutor')
def tutor(data: TutorIn, user: User = Depends(current_user), db: DB = Depends(get_db)):
    material = allowed_material(db, data.material_id, user)
    if not material.approved:
        raise HTTPException(422, 'Choose an approved chapter')
    c = classroom(db, material.class_id, user)
    source = retrieve(db, material.content, data.question)
    result = generate(db, user, 'tutor', source, c.grade, data.language, data.question)
    return result.model_dump()


@router.get('/quizzes')
def quizzes(user: User = Depends(current_user), db: DB = Depends(get_db)):
    query = select(Quiz).where(Quiz.class_id.in_(class_ids(db, user)))
    if user.role == 'student':
        query = query.where(Quiz.published == True)
    return [{'id': q.id, 'title': q.title, 'class_id': q.class_id, 'material_id': q.material_id, 'published': q.published,
             'language': q.language, 'model': q.model, 'prompt_version': q.prompt_version}
            for q in db.scalars(query.order_by(Quiz.id.desc()))]


@router.get('/quizzes/{quiz_id}')
def quiz_detail(quiz_id: int, user: User = Depends(current_user), db: DB = Depends(get_db)):
    q = allowed_quiz(db, quiz_id, user)
    questions = []
    for row in db.scalars(select(QuizQuestion).where(QuizQuestion.quiz_id == q.id).order_by(QuizQuestion.id)):
        item = {'id': row.id, 'kind': row.kind, 'question': row.question, 'options': row.options, 'topic': row.topic}
        if user.role != 'student':
            item.update(answer=row.answer, explanation=row.explanation, source_quote=row.source_quote)
        questions.append(item)
    return {'id': q.id, 'title': q.title, 'summary': q.summary, 'published': q.published, 'questions': questions,
            'flashcards': [{'front': c.front, 'back': c.back} for c in db.scalars(select(Flashcard).where(Flashcard.quiz_id == q.id))]}


@router.get('/quizzes/{quiz_id}/practice/{question_id}')
def short_answer_practice(quiz_id: int, question_id: int, user: User = Depends(current_user), db: DB = Depends(get_db)):
    q = allowed_quiz(db, quiz_id, user)
    row = db.get(QuizQuestion, question_id)
    if not row or row.quiz_id != q.id or row.kind != 'short_answer':
        raise HTTPException(404, 'Short-answer practice question not found')
    return {'answer': row.answer, 'explanation': row.explanation, 'source_quote': row.source_quote}


@router.put('/quizzes/{quiz_id}')
def edit_quiz(quiz_id: int, data: LearningPack, user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'teacher', 'admin')
    q = allowed_quiz(db, quiz_id, user)
    if q.published:
        raise HTTPException(409, 'Published packs are frozen to keep learning results reproducible')
    material = allowed_material(db, q.material_id, user)
    try:
        validate_grounding(data, material.content)
    except ValueError as exc:
        raise HTTPException(422, str(exc))
    write_pack(db, q, data)
    audit(db, user, 'learning_pack_edited', {'quiz_id': q.id})
    db.commit()
    return {'ok': True}


@router.post('/quizzes/{quiz_id}/publish')
def publish_quiz(quiz_id: int, user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'teacher', 'admin')
    q = allowed_quiz(db, quiz_id, user)
    material = allowed_material(db, q.material_id, user)
    if not material.approved:
        raise HTTPException(422, 'Source material must be approved')
    rows = list(db.scalars(select(QuizQuestion).where(QuizQuestion.quiz_id == q.id)))
    if sum(r.kind == 'mcq' for r in rows) < 5:
        raise HTTPException(422, 'A challenge needs at least five multiple-choice questions')
    if not q.published:
        q.published = True
        notify_class(db, user, q.class_id, 'A new learning challenge', q.title)
        audit(db, user, 'learning_pack_published', {'quiz_id': q.id})
    db.commit()
    return {'ok': True}


def challenge_questions(db, quiz_id, mode):
    rows = list(db.scalars(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz_id, QuizQuestion.kind == 'mcq').order_by(QuizQuestion.id)))
    return rows[:5] if mode == 'daily' else rows


@router.get('/arena')
def arena(user: User = Depends(current_user), db: DB = Depends(get_db)):
    available = list(db.scalars(select(Quiz).where(Quiz.class_id.in_(class_ids(db, user)), Quiz.published == True).order_by(Quiz.id)))
    attempts = list(db.scalars(select(QuizAttempt).where(QuizAttempt.student_id == user.id, QuizAttempt.school_id == user.school_id).order_by(QuizAttempt.id)))
    daily = available[today().toordinal() % len(available)] if available else None
    badges = []
    if attempts:
        badges.append({'name': 'Curious mind', 'description': 'Completed a first learning challenge', 'icon': '✦'})
    this_week = today() - __import__('datetime').timedelta(days=today().weekday())
    if len({a.day for a in attempts if a.day >= this_week}) >= 3:
        badges.append({'name': 'Making space to learn', 'description': 'Practised on three days this week', 'icon': '❋'})
    if len(attempts) >= 2 and attempts[-1].score / max(attempts[-1].total, 1) > attempts[-2].score / max(attempts[-2].total, 1):
        badges.append({'name': 'A step forward', 'description': 'Improved practice accuracy', 'icon': '↗'})
    completed = any(a.mode == 'daily' and a.day == today() for a in attempts)
    return {'daily_quiz_id': daily.id if daily else None, 'daily_completed': completed, 'badges': badges,
            'completed_challenges': len(attempts), 'history': [{'id': a.id, 'quiz_id': a.quiz_id, 'score': a.score, 'total': a.total, 'day': str(a.day), 'mode': a.mode} for a in attempts[-20:]]}


@router.post('/quizzes/{quiz_id}/check')
def check_answer(quiz_id: int, data: AttemptIn, user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'student')
    q = allowed_quiz(db, quiz_id, user)
    rows = {r.id: r for r in challenge_questions(db, q.id, data.mode)}
    if len(data.answers) != 1 or not set(data.answers).issubset(rows):
        raise HTTPException(422, 'Check one multiple-choice answer at a time')
    qid, answer = next(iter(data.answers.items()))
    row = rows[qid]
    if answer not in row.options:
        raise HTTPException(422, 'Select one of the offered options')
    return {'correct': answer == row.answer, 'answer': row.answer, 'explanation': row.explanation, 'source_quote': row.source_quote}


@router.post('/quizzes/{quiz_id}/attempts', status_code=201)
def attempt(quiz_id: int, data: AttemptIn, user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'student')
    q = allowed_quiz(db, quiz_id, user)
    if data.mode == 'daily':
        state = arena(user, db)
        if state['daily_completed']:
            raise HTTPException(409, 'Today’s challenge is already completed')
        if state['daily_quiz_id'] != q.id:
            raise HTTPException(422, 'Choose today’s challenge')
    rows = challenge_questions(db, q.id, data.mode)
    if not rows or set(data.answers) != {r.id for r in rows}:
        raise HTTPException(422, 'Answer all challenge questions')
    if any(data.answers[r.id] not in r.options for r in rows):
        raise HTTPException(422, 'Answers must match offered options')
    results = [{'question_id': r.id, 'topic': r.topic, 'correct': data.answers[r.id] == r.answer} for r in rows]
    score = sum(r['correct'] for r in results)
    row = QuizAttempt(school_id=user.school_id, quiz_id=q.id, student_id=user.id, mode=data.mode, day=today(),
                      score=score, total=len(rows), responses=results)
    db.add(row)
    db.commit()
    return {'score': score, 'total': len(rows), 'message': 'Thanks for making room to learn. Every question is a step forward.'}


@router.get('/analytics')
def analytics(user: User = Depends(current_user), db: DB = Depends(get_db)):
    require(user, 'teacher', 'admin')
    ids = class_ids(db, user)
    attendance = db.execute(select(Attendance.day, func.count(), func.sum(__import__('sqlalchemy').case((Attendance.status == 'present', 1), else_=0)))
                            .where(Attendance.class_id.in_(ids)).group_by(Attendance.day).order_by(Attendance.day.desc()).limit(14)).all()
    assignments = []
    for h in db.scalars(select(Homework).where(Homework.class_id.in_(ids))):
        total = db.scalar(select(func.count()).select_from(Enrollment).where(Enrollment.class_id == h.class_id))
        count = db.scalar(select(func.count()).select_from(Submission).where(Submission.homework_id == h.id))
        complete = db.scalar(select(func.count()).select_from(Submission).where(Submission.homework_id == h.id, Submission.status == 'complete'))
        assignments.append({'title': h.title, 'students': total, 'submitted': count, 'complete': complete})
    topics = {}
    # Only aggregate practice answers, never publish individual student rankings.
    attempts = list(db.scalars(select(QuizAttempt).join(Quiz, Quiz.id == QuizAttempt.quiz_id).where(Quiz.class_id.in_(ids))))
    for a in attempts:
        for r in a.responses:
            item = topics.setdefault(r['topic'], {'topic': r['topic'], 'correct': 0, 'total': 0})
            item['correct'] += int(r['correct'])
            item['total'] += 1
    return {'attendance': [{'day': str(day), 'total': total, 'present': int(present or 0)} for day, total, present in reversed(attendance)],
            'assignments': assignments, 'topics': sorted(topics.values(), key=lambda t:t['correct']/max(t['total'],1)),
            'practice_attempts': len(attempts)}
