"""Explicit, development-only synthetic demo data. Never runs on application startup."""
import argparse
from datetime import timedelta
from sqlalchemy import select
from .db import SessionLocal
from .models import *
from .security import passwords
from .config import settings
from .routes import today

CHAPTER = '''Plants make their own food through photosynthesis. Leaves contain a green pigment called chlorophyll. Chlorophyll captures energy from sunlight. Plants use sunlight, carbon dioxide from the air, and water from the soil to produce glucose. Glucose is a simple sugar that provides energy for the plant. Oxygen is released during photosynthesis. Roots absorb water and minerals from the soil. The stem transports water to the leaves. Tiny openings in leaves called stomata allow gases to move in and out. Photosynthesis is important because it provides food and oxygen for living things. A plant kept without light cannot carry out photosynthesis normally. We should protect trees because they support life on Earth.'''


def seed():
    if settings().environment == 'production':
        raise SystemExit('Demo seeding is disabled in production. Use app.bootstrap.')
    with SessionLocal() as db:
        if db.scalar(select(School)):
            print('Database already contains a school; no changes made.')
            return
        school = School(name='Greenwood Public School · Demo')
        db.add(school)
        db.flush()
        people = [('Ananya Sharma', 'admin', 'admin@nexora.demo'), ('Meera Iyer', 'teacher', 'teacher@nexora.demo'),
                  ('Aarav Mehta', 'student', 'student@nexora.demo'), ('Diya Kapoor', 'student', 'diya@nexora.demo'),
                  ('Ishaan Rao', 'student', 'ishaan@nexora.demo'), ('Myra Singh', 'student', 'myra@nexora.demo'),
                  ('Rohan Shah', 'student', 'rohan@nexora.demo'), ('Sana Ali', 'student', 'sana@nexora.demo')]
        users = []
        for name, role, email in people:
            u = User(school_id=school.id, name=name, role=role, email=email, password_hash=passwords.hash('NexoraDemo!2026'))
            db.add(u)
            users.append(u)
        c = Classroom(school_id=school.id, name='Class 6 · A', grade=6)
        db.add(c)
        science = Subject(school_id=school.id, name='Science')
        db.add_all([science, Subject(school_id=school.id, name='Mathematics'), Subject(school_id=school.id, name='English'), Subject(school_id=school.id, name='Hindi')])
        db.flush()
        db.add(TeacherAssignment(class_id=c.id, teacher_id=users[1].id))
        for u in users[2:]:
            db.add(Enrollment(class_id=c.id, student_id=u.id))
            for offset in range(1, 8):
                db.add(Attendance(school_id=school.id, class_id=c.id, student_id=u.id, day=today() - timedelta(days=offset),
                                  status='absent' if u.id == users[4].id and offset == 3 else 'present', marked_by=users[1].id))
        material = Material(school_id=school.id, class_id=c.id, subject_id=science.id, title='How plants make food',
                            content=CHAPTER, approved=True, created_by=users[1].id)
        db.add(material)
        db.add(Homework(school_id=school.id, class_id=c.id, subject_id=science.id, title='A leaf’s little kitchen',
                        instructions='Explain photosynthesis in your own words. Name the three things a plant needs and describe why trees matter.',
                        due_date=today() + timedelta(days=2), created_by=users[1].id))
        for u in users:
            db.add(Notification(school_id=school.id, user_id=u.id, title='Welcome to your Nexora demo',
                                body='All names and learning records here are synthetic. Explore your classroom and try a complete workflow.'))
        db.flush()
        quiz = Quiz(school_id=school.id, class_id=c.id, material_id=material.id, title='The green world challenge',
                    summary='Plants use sunlight, water and carbon dioxide to make glucose. Chlorophyll captures sunlight and oxygen is released.',
                    language='en', published=True, model='teacher-authored-demo', prompt_version='manual-v1', created_by=users[1].id)
        db.add(quiz)
        db.flush()
        for question, options, answer, quote, topic in [
            ('What process do plants use to make food?', ['Photosynthesis', 'Digestion', 'Freezing', 'Melting'], 'Photosynthesis', 'Plants make their own food through photosynthesis.', 'Photosynthesis'),
            ('Which pigment captures sunlight?', ['Chlorophyll', 'Oxygen', 'Water', 'Glucose'], 'Chlorophyll', 'Chlorophyll captures energy from sunlight.', 'Chlorophyll'),
            ('Which gas is released during photosynthesis?', ['Oxygen', 'Nitrogen', 'Carbon dioxide', 'Helium'], 'Oxygen', 'Oxygen is released during photosynthesis.', 'Gas exchange'),
            ('Which part absorbs water from soil?', ['Roots', 'Flowers', 'Seeds', 'Leaves'], 'Roots', 'Roots absorb water and minerals from the soil.', 'Plant parts'),
            ('What simple sugar provides energy to plants?', ['Glucose', 'Salt', 'Water', 'Starch only'], 'Glucose', 'Glucose is a simple sugar that provides energy for the plant.', 'Plant nutrition')]:
            db.add(QuizQuestion(quiz_id=quiz.id, kind='mcq', question=question, options=options, answer=answer,
                                explanation=quote, source_quote=quote, topic=topic))
        db.add_all([Flashcard(quiz_id=quiz.id, front='What is photosynthesis?', back='How plants make glucose using sunlight, water and carbon dioxide.'),
                    Flashcard(quiz_id=quiz.id, front='What does chlorophyll do?', back='It captures sunlight in leaves.')])
        db.add(QuizQuestion(quiz_id=quiz.id, kind='short_answer', question='Why are trees important for living things?', options=[],
                            answer='Trees carry out photosynthesis, which provides food and oxygen for living things.',
                            explanation='Use your chapter to connect photosynthesis with the needs of living things.',
                            source_quote='Photosynthesis is important because it provides food and oxygen for living things.', topic='Life on Earth'))
        db.commit()
    print('Synthetic school created. Demo password: NexoraDemo!2026')


if __name__ == '__main__':
    seed()
