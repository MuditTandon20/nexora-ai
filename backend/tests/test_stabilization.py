"""Regression tests for audit findings F-01 through F-05 and F-07."""
import asyncio
import json

import pytest
from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import func, select

from app.ai import process_completion, validate_grounding
from app.config import settings
from app.models import AIEvent, Notification, Submission
from app.request_limits import RequestBodyLimit
from app.schemas import LearningPack, TutorOut
from test_ai import pack_payload, setup_material
from test_audit_security import homework
from test_foundation import make_class
from test_learning import CONTENT


def envelope(content, **extra):
    return {'choices': [{'message': {'content': json.dumps(content)}}], **extra}


def tutor_reply(**changes):
    return {'answer': 'Plants make food by freezing water into ice.',
            'source_quote': 'Plants make their own food through photosynthesis.',
            'follow_up': 'Which ice cubes do plants eat?', 'insufficient_context': False, **changes}


@pytest.mark.parametrize('name', ['  ', '\t\n', ' A '])
def test_f01_rejects_normalized_short_class_names(context, name):
    login, _ = context
    assert login('admin').post('/api/classes', json={'name': name, 'grade': 5}).status_code == 422


def test_f01_normalizes_before_uniqueness(context):
    login, _ = context
    admin = login('admin')
    first = admin.post('/api/classes', json={'name': '  Class 3 B  ', 'grade': 3})
    assert first.status_code == 201 and first.json()['name'] == 'Class 3 B'
    assert admin.post('/api/classes', json={'name': 'Class 3 B', 'grade': 3}).status_code == 409


@pytest.mark.parametrize('usage', [None, {'prompt_tokens': 10, 'completion_tokens': 20}])
def test_f02_null_or_valid_usage_finishes_successfully(context, monkeypatch, usage):
    login, factory = context
    admin, teacher = login('admin'), login('teacher')
    _, mid = setup_material(admin, teacher)
    configure_stub(monkeypatch, envelope(tutor_reply(), usage=usage))
    result = teacher.post('/api/ai/tutor', json={'material_id': mid, 'question': 'How do plants make food?'})
    assert result.status_code == 200, result.text
    with factory() as db:
        assert db.scalar(select(AIEvent)).status == 'success'


def configure_stub(monkeypatch, response):
    # Temporary settings only; a stub replaces the sole provider boundary first.
    monkeypatch.setattr('app.ai.call_provider', lambda *args: response)
    for key, value in [('ai_enabled', True), ('llm_base_url', 'https://invalid.test/v1'), ('llm_api_key', 'stub'), ('llm_model', 'stub')]:
        monkeypatch.setattr(settings(), key, value)


@pytest.mark.parametrize('response', [
    {'choices': [{}]},
    envelope(tutor_reply(), usage=[]),
    envelope(tutor_reply(), usage={'prompt_tokens': -1, 'completion_tokens': 2}),
    envelope(tutor_reply(), usage={'prompt_tokens': '10', 'completion_tokens': 2}),
    envelope(tutor_reply(), usage={'prompt_tokens': True, 'completion_tokens': 2}),
    {'choices': [{'message': {'content': '{}'}, 'finish_reason': 'length'}]},
])
def test_f02_invalid_provider_metadata_is_terminal_failure(context, monkeypatch, response):
    login, factory = context
    admin, teacher = login('admin'), login('teacher')
    _, mid = setup_material(admin, teacher)
    configure_stub(monkeypatch, response)
    assert teacher.post('/api/ai/tutor', json={'material_id': mid, 'question': 'How do plants make food?'}).status_code == 502
    with factory() as db:
        assert db.scalar(select(AIEvent)).status == 'validation_error'


def test_f02_unexpected_adapter_error_is_terminal(context, monkeypatch):
    login, factory = context
    admin, teacher = login('admin'), login('teacher')
    _, mid = setup_material(admin, teacher)
    configure_stub(monkeypatch, None)
    def broken(*args):
        raise RuntimeError('synthetic adapter error')
    monkeypatch.setattr('app.ai.call_provider', broken)
    assert teacher.post('/api/ai/tutor', json={'material_id': mid, 'question': 'How do plants make food?'}).status_code == 502
    with factory() as db:
        event = db.scalar(select(AIEvent))
        assert event.status == 'provider_error' and event.error == 'RuntimeError'


@pytest.mark.parametrize('length', ['not-an-integer', '-1', '+12', '1.5', ''])
def test_f03_invalid_lengths_are_client_errors(context, length):
    login, _ = context
    assert login('admin').post('/api/announcements', json={'title': 'Synthetic', 'body': 'Synthetic note'}, headers={'content-length': length}).status_code == 400


def test_f03_header_limit_returns_413(context):
    login, _ = context
    assert login('admin').post('/api/announcements', json={}, headers={'content-length': str(12 * 1024 * 1024)}).status_code == 413


def test_f03_ambiguous_length_headers_rejected(context):
    login, _ = context
    response = login('admin').post('/api/announcements', content=b'{}', headers=[('content-length', '2'), ('content-length', '3')])
    assert response.status_code == 400


def test_f03_actual_fastapi_stream_limit(context):
    login, _ = context
    admin = login('admin')
    chunks = iter([b' ' * (1024 * 1024)] * 12)
    response = admin.post('/api/announcements', content=chunks, headers={'content-type': 'application/json'})
    assert response.status_code == 413


def test_f03_small_stream_without_length_remains_usable(context):
    login, _ = context
    chunks = iter([b'{"title":"Synthetic","body":"A small ', b'synthetic announcement"}'])
    assert login('admin').post('/api/announcements', content=chunks, headers={'content-type': 'application/json'}).status_code == 200


@pytest.mark.parametrize('headers', [[], [(b'content-length', b'1')]])
def test_f03_counts_streamed_bytes_without_trusting_header(headers):
    async def exercise():
        consumed = 0
        sent = []
        async def receiver():
            nonlocal consumed
            consumed += 1
            return {'type': 'http.request', 'body': b'x' * 8, 'more_body': True}
        async def sender(message):
            sent.append(message)
        async def reader(scope, receive, send):
            while (await receive()).get('more_body'):
                pass
        await RequestBodyLimit(reader, max_bytes=10)({'type': 'http', 'headers': headers}, receiver, sender)
        assert sent[0]['status'] == 413 and consumed == 2
    asyncio.run(exercise())


def test_f04_exact_retries_and_unreviewed_edits_do_not_repeat_alerts(context):
    login, factory = context
    admin, teacher, student = login('admin'), login('teacher'), login('student')
    hid = homework(teacher, make_class(admin))
    path = f'/api/homework/{hid}/submit'
    assert student.post(path, json={'answer': 'First draft'}).status_code == 200
    with factory() as db:
        stamp = db.scalar(select(Submission)).submitted_at
    assert student.post(path, json={'answer': 'First draft'}).status_code == 200
    with factory() as db:
        assert db.scalar(select(Submission)).submitted_at == stamp
    assert student.post(path, json={'answer': 'Changed draft before review'}).status_code == 200
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Submission)) == 1
        assert db.scalar(select(func.count()).select_from(Notification).where(Notification.title == 'Homework submitted')) == 1
        sid = db.scalar(select(Submission)).id
    assert teacher.post(f'/api/submissions/{sid}/review', json={'status': 'needs_revision', 'feedback': 'Add the inputs.'}).status_code == 200
    # Same answer after a review is a new actionable revision, not an exact retry.
    assert student.post(path, json={'answer': 'Changed draft before review'}).status_code == 200
    assert student.post(path, json={'answer': 'Changed draft before review'}).status_code == 200
    with factory() as db:
        assert db.scalar(select(func.count()).select_from(Notification).where(Notification.title == 'Homework submitted')) == 2


@pytest.mark.parametrize('language', ['en', 'hi'])
def test_f05_unverified_claims_and_followups_never_reach_tutor_response(language):
    raw = tutor_reply()
    # The structural quotation check alone still accepts contradictory prose.
    validate_grounding(TutorOut.model_validate(raw), CONTENT)
    delivered, _ = process_completion(envelope(raw), 'tutor', CONTENT, language)
    assert raw['answer'] not in delivered.answer
    assert 'freezing' not in delivered.answer
    assert 'ice cubes' not in delivered.follow_up
    assert delivered.source_quote in CONTENT


def test_f05_abstention_does_not_echo_untrusted_prose():
    raw = tutor_reply(insufficient_context=True, source_quote='')
    delivered, _ = process_completion(envelope(raw), 'tutor', CONTENT)
    assert delivered.insufficient_context and delivered.source_quote == ''
    assert 'freezing' not in delivered.answer


def test_f07_missing_short_answer_and_duplicate_cards_rejected():
    pack = pack_payload()
    pack['questions'].pop()
    with pytest.raises(ValidationError):
        LearningPack.model_validate(pack)
    pack = pack_payload()
    pack['flashcards'][1] = pack['flashcards'][0]
    with pytest.raises(ValidationError, match='Duplicate flashcard'):
        LearningPack.model_validate(pack)


@pytest.mark.parametrize('field', ['summary', 'flashcard'])
def test_f07_unsupported_summary_and_card_back_rejected(field):
    pack = pack_payload()
    if field == 'summary':
        pack['summary'] = 'Plants freeze water into food at night.'
    else:
        pack['flashcards'][0]['back'] = 'Plants freeze water into food at night.'
    with pytest.raises(ValueError, match='Unsupported'):
        process_completion(envelope(pack), 'quiz', CONTENT)


def test_f07_full_pack_can_be_edited_and_published_but_unsupported_edit_cannot(context, monkeypatch):
    login, _ = context
    admin, teacher = login('admin'), login('teacher')
    _, mid = setup_material(admin, teacher)
    pack = pack_payload()
    configure_stub(monkeypatch, envelope(pack))
    generated = teacher.post('/api/ai/generate', json={'material_id': mid})
    assert generated.status_code == 201, generated.text
    qid = generated.json()['id']
    invalid = {**pack, 'summary': 'Plants freeze water into food at night.'}
    assert teacher.put(f'/api/quizzes/{qid}', json=invalid).status_code == 422
    assert teacher.get(f'/api/quizzes/{qid}').json()['summary'] == pack['summary']
    pack['title'] = 'A reviewed synthetic learning pack'
    assert teacher.put(f'/api/quizzes/{qid}', json=pack).status_code == 200
    assert teacher.post(f'/api/quizzes/{qid}/publish').status_code == 200
    assert teacher.post(f'/api/quizzes/{qid}/publish').status_code == 200
    assert teacher.put(f'/api/quizzes/{qid}', json=pack).status_code == 409


def test_f07_preexisting_incomplete_draft_cannot_be_published(context):
    from app.arena import write_pack
    from app.models import Quiz, QuizQuestion
    login, factory = context
    admin, teacher = login('admin'), login('teacher')
    cid, mid = setup_material(admin, teacher)
    with factory() as db:
        quiz = Quiz(school_id=1, class_id=cid, material_id=mid, title='Legacy synthetic draft', summary=CONTENT,
                    language='en', model='stub', prompt_version='old-stub', created_by=2)
        db.add(quiz)
        db.flush()
        write_pack(db, quiz, LearningPack.model_validate(pack_payload()))
        db.flush()
        db.delete(db.scalar(select(QuizQuestion).where(QuizQuestion.quiz_id == quiz.id, QuizQuestion.kind == 'short_answer')))
        db.commit()
        qid = quiz.id
    assert teacher.post(f'/api/quizzes/{qid}/publish').status_code == 422
    with factory() as db:
        assert db.get(Quiz, qid).published is False
