"""Synthetic audit coverage. Model responses are stubbed; no live inference is allowed."""
import io
import json
from datetime import timedelta

import httpx
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from sqlalchemy import func, select

from app.config import settings
from app.main import app
from app.models import AIEvent, Attendance, Notification, Session, Submission, User, now
from app.security import token_hash
from test_ai import setup_material
from test_foundation import make_class
from test_learning import CONTENT
from app.routes import today


@pytest.fixture(autouse=True)
def no_live_inference(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail('Audit tests must not call a live AI provider')
    monkeypatch.setattr('app.ai.call_provider', forbidden)
    monkeypatch.setattr(settings(), 'ai_enabled', False)


def readable_pdf():
    writer = PdfWriter()
    page = writer.add_blank_page(600, 800)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'), NameObject('/Subtype'): NameObject('/Type1'), NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): writer._add_object(font)})})
    stream = DecodedStreamObject()
    stream.set_data(b'BT /F1 12 Tf 50 700 Td (Plants make food through photosynthesis. Roots absorb water from soil.) Tj ET')
    page[NameObject('/Contents')] = writer._add_object(stream)
    output = io.BytesIO()
    writer.write(output)
    return output.getvalue()


def homework(teacher, cid):
    response = teacher.post('/api/homework', json={'class_id': cid, 'subject_id': 1, 'title': 'Audit homework', 'instructions': 'Explain photosynthesis using your own words.', 'due_date': str(today())})
    assert response.status_code == 201, response.text
    return response.json()['id']


def test_cross_school_lists_and_detail_access(context):
    login, _ = context
    admin, teacher, outsider = [login(n) for n in ['admin', 'teacher', 'outsider']]
    cid, mid = setup_material(admin, teacher)
    hid = homework(teacher, cid)
    for role in ['teacher', 'student']:
        name = f'other_{role}'
        response = outsider.post('/api/users', json={'name': name, 'email': f'{name}@test.in', 'password': 'TestPassword!2026', 'role': role})
        assert response.status_code == 201, response.text
        other = login(name)
        assert other.get('/api/classes').json() == []
        assert other.get('/api/materials').json() == []
        assert other.get('/api/homework').json() == []
        assert other.get('/api/quizzes').json() == []
        assert other.get(f'/api/classes/{cid}/attendance', params={'day': str(today())}).status_code == 404
        assert other.get(f'/api/materials/{mid}/download').status_code == 404
        if role == 'student':
            assert other.post(f'/api/homework/{hid}/submit', json={'answer': 'Cross-school attempt'}).status_code == 404
            assert other.post('/api/ai/tutor', json={'material_id': mid, 'question': 'What do leaves do?'}).status_code == 404
        else:
            assert other.get(f'/api/homework/{hid}/submissions').status_code == 404
            assert other.post(f'/api/materials/{mid}/approve').status_code == 404
    # School B's newly created accounts legitimately produce its own audit rows.
    assert {row['actor_id'] for row in outsider.get('/api/audit').json()} == {5}
    assert outsider.get('/api/users').json()[0]['school_id'] == 2


def test_actual_pdf_is_private_across_school_class_draft_and_anonymous(context, tmp_path, monkeypatch):
    login, _ = context
    admin, teacher, student, outsider = [login(n) for n in ['admin', 'teacher', 'student', 'outsider']]
    monkeypatch.setattr(settings(), 'upload_dir', str(tmp_path))
    cid = make_class(admin)
    pdf = readable_pdf()
    uploaded = teacher.post('/api/materials/upload', data={'class_id': cid, 'subject_id': 1, 'title': 'Private audit PDF'}, files={'file': ('audit.pdf', pdf, 'application/pdf')})
    assert uploaded.status_code == 201, uploaded.text
    mid = uploaded.json()['id']
    path = f'/api/materials/{mid}/download'
    with TestClient(app) as anonymous:
        assert anonymous.get(path).status_code == 401
    assert student.get(path).status_code == 404  # draft
    assert outsider.get(path).status_code == 404
    assert teacher.post(f'/api/materials/{mid}/approve').status_code == 200
    assert student.get(path).content == pdf
    assert outsider.get(path).status_code == 404
    unassigned_id = admin.post('/api/users', json={'name': 'Unassigned learner', 'email': 'unassigned@test.in', 'password': 'TestPassword!2026', 'role': 'student'}).json()['id']
    unassigned = login('unassigned')
    assert unassigned.get(path).status_code == 403
    assert unassigned.get('/api/materials').json() == []
    actual = next(tmp_path.rglob('*.pdf'))
    assert student.get('/uploads/' + actual.relative_to(tmp_path).as_posix()).status_code == 404
    assert student.get(path).headers['cache-control'] == 'no-store'


def test_stale_correction_cannot_overwrite_newer_roll_call(context):
    login, factory = context
    admin, teacher = login('admin'), login('teacher')
    cid = make_class(admin)
    path = f'/api/classes/{cid}/attendance'
    initial = {'day': str(today()), 'absent_ids': [4], 'confirmed': True}
    assert teacher.post(path, json=initial).status_code == 200
    version_a = teacher.get(path, params={'day': str(today())}).json()['version']
    correction = {**initial, 'expected_version': version_a, 'correction_reason': 'Verified arrival', 'absent_ids': []}
    assert teacher.post(path, json=correction).status_code == 200
    assert teacher.post(path, json={**initial, 'expected_version': version_a, 'correction_reason': 'Stale open tab'}).status_code == 409
    current = teacher.get(path, params={'day': str(today())}).json()
    assert all(r['status'] == 'present' for r in current['records'])
    assert teacher.post(path, json={**initial, 'expected_version': current['version']}).status_code == 422
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Attendance)) == 2


def test_duplicate_submission_is_one_row_and_cannot_impersonate_peer(context):
    login, factory = context
    admin, teacher, student, peer = [login(n) for n in ['admin', 'teacher', 'student', 'peer']]
    hid = homework(teacher, make_class(admin))
    path = f'/api/homework/{hid}/submit'
    for answer in ['First draft', 'Revised synthetic draft']:
        assert student.post(path, json={'answer': answer, 'student_id': 4}).status_code == 200
    with factory() as db:
        rows = list(db.scalars(select(Submission).where(Submission.homework_id == hid)))
        assert len(rows) == 1 and rows[0].student_id == 3
        assert rows[0].answer == 'Revised synthetic draft'
        sid = rows[0].id
    assert peer.get('/api/homework').json()[0]['my_submission'] is None
    assert peer.get(f'/api/homework/{hid}/submissions').status_code == 403
    assert peer.post(f'/api/submissions/{sid}/review', json={'status': 'complete', 'feedback': 'Forged review'}).status_code == 403
    assert teacher.post(f'/api/submissions/{sid}/review', json={'status': 'complete', 'feedback': 'Reviewed'}).status_code == 200
    assert student.post(path, json={'answer': 'After completion'}).status_code == 409


def test_peer_notification_and_password_revocation(context):
    login, factory = context
    student, peer = login('student'), login('peer')
    with factory() as db:
        note = Notification(school_id=1, user_id=3, title='Private notice', body='Synthetic student-only message')
        db.add(note)
        db.commit()
        nid = note.id
    assert peer.post(f'/api/notifications/{nid}/read').status_code == 404
    assert all(n['id'] != nid for n in peer.get('/api/notifications').json())
    second_session = login('student')
    assert student.post('/api/auth/password', json={'current_password': 'wrong', 'new_password': 'ChangedPassword!2026'}).status_code == 400
    assert student.post('/api/auth/password', json={'current_password': 'TestPassword!2026', 'new_password': 'ChangedPassword!2026'}).status_code == 200
    assert second_session.get('/api/auth/me').status_code == 401
    assert peer.get('/api/auth/me').status_code == 200


def test_expired_session_origin_and_production_cookie(context, monkeypatch):
    login, factory = context
    admin = login('admin')
    assert admin.post('/api/announcements', json={'title': 'Blocked origin', 'body': 'Synthetic message'}, headers={'origin': 'https://untrusted.invalid'}).status_code == 403
    cookie = admin.cookies.get('nexora_session')
    with factory() as db:
        db.get(Session, token_hash(cookie)).expires_at = now() - timedelta(seconds=1)
        db.commit()
    assert admin.get('/api/auth/me').status_code == 401
    monkeypatch.setattr(settings(), 'environment', 'production')
    with TestClient(app, base_url='https://testserver') as client:
        result = client.post('/api/auth/login', json={'email': 'admin@test.in', 'password': 'TestPassword!2026'})
        assert result.status_code == 200
        header = result.headers['set-cookie'].lower()
        assert 'secure' in header and 'httponly' in header and 'samesite=lax' in header


@pytest.mark.parametrize('bad', [None, {}, {'choices': []}, {'choices': None}, {'choices': [{'message': {'content': '{}'}}]}])
def test_invalid_ai_envelopes_fail_closed(context, monkeypatch, bad):
    login, factory = context
    admin, teacher = login('admin'), login('teacher')
    _, mid = setup_material(admin, teacher)
    cfg = settings()
    for key, value in [('ai_enabled', True), ('llm_base_url', 'https://invalid.test/v1'), ('llm_api_key', 'synthetic'), ('llm_model', 'stub')]:
        monkeypatch.setattr(cfg, key, value)
    monkeypatch.setattr('app.ai.call_provider', lambda *args: bad)
    result = teacher.post('/api/ai/generate', json={'material_id': mid})
    assert result.status_code == 502
    with factory() as db:
        assert db.scalar(select(AIEvent)).status in ['provider_error', 'validation_error']


def test_provider_timeout_has_safe_failure(context, monkeypatch):
    login, factory = context
    admin, teacher = login('admin'), login('teacher')
    _, mid = setup_material(admin, teacher)
    for key, value in [('ai_enabled', True), ('llm_base_url', 'https://invalid.test/v1'), ('llm_api_key', 'synthetic'), ('llm_model', 'stub')]:
        monkeypatch.setattr(settings(), key, value)
    def timeout(*args):
        raise httpx.ReadTimeout('synthetic timeout')
    monkeypatch.setattr('app.ai.call_provider', timeout)
    result = teacher.post('/api/ai/generate', json={'material_id': mid})
    assert result.status_code == 502
    with factory() as db:
        assert db.scalar(select(AIEvent)).error == 'ReadTimeout'
