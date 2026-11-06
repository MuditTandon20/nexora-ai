from collections import Counter
import json
import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config import Settings
from app.db import Base
from app.demo import guard_demo
from app.models import Classroom, Submission, User
from evals.prepare_review import prepare
from evals.run import HERE, evaluate, load_cases
from test_ai import setup_material
from test_audit_security import homework
from app.routes import today


def test_dashboard_class_tasks_are_actionable_and_private(context):
    login, _ = context
    admin, teacher, student, outsider = [login(n) for n in ['admin', 'teacher', 'student', 'outsider']]
    cid, _ = setup_material(admin, teacher)
    earlier = homework(teacher, cid)
    later = teacher.post('/api/homework', json={'class_id':cid,'subject_id':1,'title':'Pending later assignment','instructions':'Explain a synthetic example.', 'due_date':str(today())}).json()['id']
    assert student.post(f'/api/homework/{later}/submit', json={'answer':'Synthetic answer'}).status_code == 200
    assert teacher.post(f'/api/classes/{cid}/attendance', json={'day':str(today()),'confirmed':True,'absent_ids':[4]}).status_code == 200
    overview = teacher.get('/api/dashboard').json()
    task = overview['class_tasks'][0]
    assert task['class_id'] == cid and task['students'] == 2 and task['present'] == 1
    assert task['attendance_saved'] and task['pending_review'] == 1
    assert overview['homework'][0]['id'] == later
    assert overview['ai_available'] is False
    assert student.get('/api/dashboard').json()['class_tasks'] == []
    assert all(h['pending_review'] == 0 for h in student.get('/api/dashboard').json()['homework'])
    assert outsider.get('/api/dashboard').json()['class_tasks'] == []


@pytest.mark.parametrize('changes', [{'environment':'production'}, {'ai_enabled':True}, {'storage_backend':'s3'}, {'database_url':'postgresql+psycopg://invalid/unused'}])
def test_demo_guard_rejects_remote_or_enabled_configuration(changes):
    with pytest.raises(ValueError):
        guard_demo(Settings(_env_file=None, database_url='sqlite:///synthetic-test.db', environment='development', ai_enabled=False, storage_backend='local').model_copy(update=changes), False)


def test_demo_seed_is_synthetic_reproducible_and_refuses_existing_school(monkeypatch):
    import app.demo as demo
    engine = create_engine('sqlite://', connect_args={'check_same_thread':False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(engine, expire_on_commit=False)
    monkeypatch.setattr(demo, 'SessionLocal', factory)
    monkeypatch.setattr('app.seed.SessionLocal', factory)
    monkeypatch.setattr(demo, 'settings', lambda: Settings(_env_file=None, database_url='sqlite:///synthetic-test.db', environment='development', ai_enabled=False, storage_backend='local'))
    demo.main()
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Classroom)) == 3
        assert db.scalar(select(func.count()).select_from(User).where(User.role=='student')) == 18
        assert db.scalar(select(func.count()).select_from(Submission).where(Submission.status=='submitted')) == 6
        assert all(email.endswith('@nexora.demo') for email in db.scalars(select(User.email)))
    with pytest.raises(ValueError, match='NEW empty'):
        demo.main()
    engine.dispose()


def test_teacher_question_coverage_and_unmeasured_review_pack(tmp_path):
    cases = load_cases([HERE/'teacher_demo_cases.jsonl'])
    responses = json.loads((HERE/'teacher_demo_stubs.json').read_text(encoding='utf-8'))
    assert len(cases) == 27
    assert Counter(c.grade for c in cases) == {6:9,7:9,8:9}
    assert Counter(c.subject for c in cases) == {'Science':9,'Mathematics':9,'English':9}
    assert sum(c.language=='hi' for c in cases) == 3
    report = evaluate(cases, responses)
    assert report['metrics']['unexpected_outcomes'] == 0
    assert report['metrics']['curriculum_alignment']['mean_score_0_to_2'] is None
    assert prepare(cases,responses,tmp_path)['reviewed_cases'] == 0
    text = (tmp_path/'TEACHER_REVIEW_PACK.md').read_text(encoding='utf-8')
    assert text.count('## demo-c') == 27
    with pytest.raises(ValueError):
        load_cases([tmp_path/'review_cases.template.jsonl'])
