"""Fresh, local-only teacher demo. Every account/record is synthetic."""
from datetime import timedelta
from sqlalchemy import select
from .config import settings
from .db import SessionLocal
from .models import School, User, Classroom, Enrollment, TeacherAssignment, Attendance, Subject, Material, Homework, Submission
from .routes import today
from .security import passwords
from .seed import seed


def guard_demo(cfg, contains_school):
    if cfg.environment != 'development' or cfg.ai_enabled or cfg.storage_backend != 'local' or not cfg.database_url.startswith('sqlite:///'):
        raise ValueError('Teacher demo requires development, a local SQLite file, local storage and AI_ENABLED=false')
    if contains_school:
        raise ValueError('Teacher demo needs a NEW empty database; existing school records will not be changed')


def main():
    with SessionLocal() as db:
        guard_demo(settings(), db.scalar(select(School)) is not None)
    seed()
    with SessionLocal() as db:
        school = db.scalar(select(School))
        teacher = db.scalar(select(User).where(User.email == 'teacher@nexora.demo'))
        science = db.scalar(select(Subject).where(Subject.name == 'Science'))
        class6 = db.scalar(select(Classroom))
        class6_students = list(db.scalars(select(User).join(Enrollment, Enrollment.student_id == User.id).where(Enrollment.class_id == class6.id).order_by(User.id)))
        class6_homework = db.scalar(select(Homework).where(Homework.class_id == class6.id))
        groups = [(class6, class6_students, class6_homework, ['submitted', 'needs_revision', 'complete'])]
        people = {
            7: ['Kabir Nair', 'Tara Joshi', 'Dev Malhotra', 'Aisha Sen', 'Neel Kumar', 'Ira Das'],
            8: ['Arjun Menon', 'Zoya Roy', 'Ved Sinha', 'Anika Patel', 'Riya Bose', 'Om Desai'],
        }
        lessons = {
            7: ('How heat travels', 'Conduction transfers heat through a material. A metal spoon in hot soup can become warm as heat travels through the metal. Compare the hot end and the handle carefully without touching hot objects.'),
            8: ('Friction in everyday life', 'Friction acts between surfaces in contact and opposes relative motion. Friction between shoes and the ground helps us walk without slipping. Different surfaces can provide different amounts of grip.'),
        }
        for grade in [7, 8]:
            c = Classroom(school_id=school.id, name=f'Class {grade} · A', grade=grade)
            db.add(c)
            db.flush()
            db.add(TeacherAssignment(class_id=c.id, teacher_id=teacher.id))
            learners = []
            for index, name in enumerate(people[grade], 1):
                learner = User(school_id=school.id, name=name, email=f'c{grade}-{index}@nexora.demo', role='student', password_hash=passwords.hash('NexoraDemo!2026'))
                db.add(learner)
                db.flush()
                db.add(Enrollment(class_id=c.id, student_id=learner.id))
                learners.append(learner)
                for offset in range(1, 8):
                    db.add(Attendance(school_id=school.id, class_id=c.id, student_id=learner.id, day=today() - timedelta(days=offset), status='absent' if index == 2 and offset == 3 else 'present', marked_by=teacher.id))
            title, content = lessons[grade]
            db.add(Material(school_id=school.id, class_id=c.id, subject_id=science.id, title=title, content=content, approved=True, created_by=teacher.id))
            h = Homework(school_id=school.id, class_id=c.id, subject_id=science.id,
                         title='Explain a warming spoon' if grade == 7 else 'Friction around you',
                         instructions='Use the approved chapter to explain one everyday example in your own words.',
                         due_date=today() + timedelta(days=1 if grade == 7 else -1), created_by=teacher.id)
            db.add(h)
            db.flush()
            groups.append((c, learners, h, ['submitted', 'submitted', 'submitted', 'complete'] if grade == 7 else ['submitted', 'submitted', 'complete']))
        for c, learners, h, statuses in groups:
            for index, (learner, status) in enumerate(zip(learners, statuses)):
                db.add(Submission(school_id=school.id, homework_id=h.id, student_id=learner.id,
                                  answer=('Plants need light, water and carbon dioxide to make food.' if c.grade == 6 else
                                          'Heat can travel through the metal from the soup to the spoon handle.' if c.grade == 7 else
                                          'The grip between my shoe and the ground helps stop my foot slipping.'),
                                  status=status, feedback='Add a clear link to the chapter evidence.' if status == 'needs_revision' else 'Clear example, thank you.' if status == 'complete' else ''))
            if c.grade != 7:
                for index, learner in enumerate(learners):
                    db.add(Attendance(school_id=school.id, class_id=c.id, student_id=learner.id, day=today(), status='absent' if c.grade == 6 and index == 4 else 'present', marked_by=teacher.id))
        db.commit()
    print('Teacher demo ready: 3 classes, 18 synthetic learners, 6 submissions waiting for review. AI stays disabled.')


if __name__ == '__main__':
    main()
