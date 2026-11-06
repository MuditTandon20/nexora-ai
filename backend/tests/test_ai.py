import json
import pytest
from pydantic import ValidationError
from app.ai import validate_grounding, retrieve
from app.schemas import LearningPack, TutorOut
from app.models import AIEvent
from sqlalchemy import select
from test_foundation import make_class
from test_learning import CONTENT


def pack_payload():
    return {'title':'Plants in the sunlight', 'summary':'Plants make food using energy captured from sunlight.',
            'questions':[{'kind':'mcq','question':f'In practice example {i}, how do plants make food?',
                          'options':['Photosynthesis','Freezing','Melting','Digestion'], 'answer':'Photosynthesis',
                          'explanation':'Plants make their own food through photosynthesis.',
                          'source_quote':'Plants make their own food through photosynthesis.', 'topic':'Photosynthesis'} for i in range(5)],
            'flashcards':[{'front':'How do plants make food?','back':'Through photosynthesis.'},
                          {'front':'What captures sunlight?','back':'Chlorophyll.'}]}


def test_output_contract_and_evidence():
    pack = LearningPack.model_validate(pack_payload())
    validate_grounding(pack, CONTENT)
    pack.questions[0].source_quote = 'Plants eat rocks to grow faster.'
    with pytest.raises(ValueError,match='Unsupported'):
        validate_grounding(pack, CONTENT)
    duplicate = pack_payload()
    duplicate['questions'][1] = duplicate['questions'][0]
    with pytest.raises(ValidationError,match='Duplicate'):
        LearningPack.model_validate(duplicate)
    invalid = pack_payload()
    invalid['questions'][0]['answer'] = 'Not an option'
    with pytest.raises(ValidationError):
        LearningPack.model_validate(invalid)
    refusal = TutorOut(answer='This chapter does not contain enough information to answer.',source_quote='',follow_up='Can you ask your teacher for the next chapter?',insufficient_context=True)
    validate_grounding(refusal, CONTENT)


def test_ai_stays_disabled_even_with_credentials(context, monkeypatch):
    login, factory = context
    admin, teacher = login('admin'), login('teacher')
    _, mid = setup_material(admin, teacher)
    from app.config import settings
    cfg = settings()
    monkeypatch.setattr(cfg, 'ai_enabled', False)
    for key,value in [('llm_base_url','https://provider.test/v1'),('llm_api_key','test-key'),('llm_model','test-model')]:
        monkeypatch.setattr(cfg, key, value)
    def forbidden(*args, **kwargs):
        pytest.fail('Disabled AI must never call a model provider')
    monkeypatch.setattr('app.ai.call_provider', forbidden)
    assert teacher.get('/api/ai/status').json()['configured'] is False
    assert teacher.post('/api/ai/generate',json={'material_id':mid}).status_code == 503
    with factory() as db:
        assert db.scalar(select(AIEvent)) is None


def setup_material(admin, teacher):
    cid = make_class(admin)
    mid = teacher.post('/api/materials',json={'class_id':cid,'subject_id':1,'title':'Plants and light','content':CONTENT,'approved':True}).json()['id']
    return cid, mid


def test_ai_provider_validation_publish_and_private_results(context, monkeypatch):
    login, factory = context
    admin, teacher, student, peer = [login(n) for n in ['admin','teacher','student','peer']]
    cid, mid = setup_material(admin, teacher)
    from app.config import settings
    cfg = settings()
    monkeypatch.setattr(cfg, 'ai_enabled', True)
    for key,value in [('llm_base_url','https://provider.test/v1'),('llm_api_key','unit-test-key'),('llm_model','test-model')]:
        monkeypatch.setattr(cfg,key,value)
    monkeypatch.setattr('app.ai.call_provider',lambda *a,**k: {'choices':[{'message':{'content':json.dumps(pack_payload())}}], 'usage':{'prompt_tokens':100,'completion_tokens':200}})
    generated = teacher.post('/api/ai/generate',json={'material_id':mid})
    assert generated.status_code == 201, generated.text
    qid = generated.json()['id']
    assert student.get(f'/api/quizzes/{qid}').status_code == 404
    assert teacher.post(f'/api/quizzes/{qid}/publish').status_code == 200
    detail = student.get(f'/api/quizzes/{qid}').json()
    assert 'answer' not in detail['questions'][0]
    answers = {q['id']:'Photosynthesis' for q in detail['questions']}
    attempt = student.post(f'/api/quizzes/{qid}/attempts',json={'mode':'class','answers':answers})
    assert attempt.status_code == 201, attempt.text
    assert attempt.json()['score'] == 5
    assert student.post(f'/api/quizzes/{qid}/attempts',json={'mode':'class','answers':answers}).status_code == 409
    assert peer.get('/api/arena').json()['completed_challenges'] == 0
    assert student.get('/api/analytics').status_code == 403
    assert teacher.get('/api/analytics').json()['topics'][0]['correct'] == 5
    with factory() as db:
        event = db.scalar(select(AIEvent))
        assert event.status == 'success'
        assert event.prompt_version == 'nexora-v1'


def test_ai_malformed_response_logs_failure_and_missing_config(context, monkeypatch):
    login, factory = context
    admin, teacher = login('admin'), login('teacher')
    _,mid = setup_material(admin, teacher)
    assert teacher.post('/api/ai/generate',json={'material_id':mid}).status_code == 503
    from app.config import settings
    cfg=settings()
    monkeypatch.setattr(cfg, 'ai_enabled', True)
    for key,value in [('llm_base_url','https://provider.test/v1'),('llm_api_key','unit-test-key'),('llm_model','test-model')]:
        monkeypatch.setattr(cfg,key,value)
    monkeypatch.setattr('app.ai.call_provider',lambda *a,**k: {'choices':[{'message':{'content':'not JSON'}}]})
    assert teacher.post('/api/ai/generate',json={'material_id':mid}).status_code == 502
    with factory() as db:
        assert db.scalar(select(AIEvent)).status == 'validation_error'
    monkeypatch.setattr(cfg,'ai_daily_limit',1)
    assert teacher.post('/api/ai/generate',json={'material_id':mid}).status_code == 429


def test_tutor_grounding_language_and_no_profile_metadata(context, monkeypatch):
    login, factory = context
    admin, teacher, student = login('admin'), login('teacher'), login('student')
    _, mid = setup_material(admin, teacher)
    from app.config import settings
    cfg = settings()
    monkeypatch.setattr(cfg, 'ai_enabled', True)
    for key, value in [('llm_base_url','https://provider.test/v1'),('llm_api_key','test-key'),('llm_model','test-model')]:
        monkeypatch.setattr(cfg,key,value)
    captured = []
    def provider(_, payload):
        captured.append(payload)
        reply = {'answer':'पौधे प्रकाश संश्लेषण से भोजन बनाते हैं।',
                 'source_quote':'Plants make their own food through photosynthesis.',
                 'follow_up':'पौधे अपना भोजन कैसे बनाते हैं?', 'insufficient_context':False}
        return {'choices':[{'message':{'content':json.dumps(reply)}}]}
    monkeypatch.setattr('app.ai.call_provider',provider)
    answer = student.post('/api/ai/tutor',json={'material_id':mid,'language':'hi','question':'पौधे भोजन कैसे बनाते हैं?'})
    assert answer.status_code == 200, answer.text
    content = json.loads(captured[0]['messages'][1]['content'])
    assert content['language'] == 'Hindi'
    assert 'student@test.in' not in json.dumps(captured)
    assert set(content) == {'task','grade','language','source','question','output_schema'}
    with factory() as db:
        event = db.scalar(select(AIEvent))
        assert event.feature == 'tutor' and event.status == 'success'
    bad = {'answer':'Plants eat rocks, as this chapter says.', 'source_quote':'Plants eat rocks for food.',
           'follow_up':'What kind of rocks do they eat?', 'insufficient_context':False}
    monkeypatch.setattr('app.ai.call_provider',lambda *a,**k:{'choices':[{'message':{'content':json.dumps(bad)}}]})
    assert student.post('/api/ai/tutor',json={'material_id':mid,'question':'What do plants eat?'}).status_code == 502
