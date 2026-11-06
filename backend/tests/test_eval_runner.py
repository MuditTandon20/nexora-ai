"""Review fixtures test bookkeeping, not actual teacher endorsements or model quality."""
import json
import pytest
from evals.run import Case, HERE, digest, evaluate, load_cases, main, review_context, stub_provider
from app.ai import process_completion


def test_offline_runner_reports_missing_reviews_without_inventing_quality(monkeypatch):
    monkeypatch.setattr('app.ai.call_provider', lambda *args: pytest.fail('No live provider allowed'))
    cases = load_cases([HERE / 'cases.jsonl', HERE / 'teacher_reviewed.jsonl'])
    responses = json.loads((HERE / 'stub_responses.json').read_text(encoding='utf-8'))
    report = evaluate(cases, responses)
    assert report['case_count'] == 10
    assert report['cohorts']['teacher_reviewed'] == 0
    assert report['metrics']['factuality']['mean_score_0_to_2'] is None
    assert report['metrics']['grade_suitability']['status'] == 'unmeasured'
    assert report['metrics']['failures'] == 3
    assert report['metrics']['unexpected_outcomes'] == 0
    assert report['metrics']['retrieval']['reference_span_recall'] == 1
    assert evaluate(cases, responses) == report


def test_review_scores_are_bound_to_actual_fixture_not_inferred():
    # Simulated provenance for testing aggregation only; never bundled into measured results.
    source = 'Roots take water from soil. Plants need sunlight to grow.'
    entry = {'response': {'answer': 'Roots take water from soil.', 'source_quote': 'Roots take water from soil.',
                           'follow_up': 'Where do roots find water?', 'insufficient_context': False}}
    payload = {'id': 'simulated-review-test', 'grade': 2, 'language': 'en', 'source': source, 'question': 'What do roots do?',
               'review_status': 'teacher-reviewed', 'gold_evidence': ['Roots take water from soil.'],
               'review': {'reviewer_id': 'SIMULATED-TEST-REVIEWER-NOT-A-TEACHER', 'reviewed_at': '2026-11-06',
                          'source_sha256': digest(source), 'response_sha256': digest(entry),
                          'context_sha256': digest({'source': source, 'question': 'What do roots do?', 'grade': 2, 'language': 'en', 'prompt_version': 'nexora-v2'}),
                          'delivered_sha256': digest(process_completion(stub_provider(entry), 'tutor', source)[0].model_dump()),
                          'factuality': 1, 'grade_suitability': 2}}
    case = Case.model_validate(payload)
    report = evaluate([case], {case.id: entry})
    assert report['metrics']['factuality']['mean_score_0_to_2'] == 1
    assert report['metrics']['grade_suitability']['mean_score_0_to_2'] == 2
    with pytest.raises(ValueError, match='does not match'):
        evaluate([case], {case.id: {**entry, 'usage': None}})
    with pytest.raises(ValueError, match='does not match'):
        evaluate([case.model_copy(update={'grade': 10})], {case.id: entry})


def test_missing_review_metadata_cannot_be_counted_as_reviewed():
    with pytest.raises(ValueError, match='provenance'):
        Case.model_validate({'id': 'fake-review', 'grade': 2, 'language': 'en', 'source': 'Roots take water from soil.',
                             'question': 'What do roots do?', 'review_status': 'teacher-reviewed'})


def test_runner_catches_duplicate_ids_and_missing_responses(tmp_path):
    line = (HERE / 'cases.jsonl').read_text(encoding='utf-8').splitlines()[0]
    path = tmp_path / 'duplicate.jsonl'
    path.write_text(line + '\n' + line, encoding='utf-8')
    with pytest.raises(ValueError, match='Duplicate'):
        load_cases([path])
    with pytest.raises(ValueError, match='Missing stub'):
        evaluate(load_cases([HERE / 'cases.jsonl']), {})


def test_runner_exits_nonzero_on_unexpected_pipeline_failure(tmp_path):
    cases = load_cases([HERE / 'cases.jsonl'])[:1]
    report = evaluate(cases, {cases[0].id: {'raw': {}}})
    assert report['metrics']['unexpected_outcomes'] == 1
    cases_path = tmp_path / 'cases.jsonl'
    cases_path.write_text(cases[0].model_dump_json() + '\n', encoding='utf-8')
    responses = tmp_path / 'responses.json'
    responses.write_text(json.dumps({cases[0].id: {'raw': {}}}), encoding='utf-8')
    assert main(['--cases', str(cases_path), '--responses', str(responses), '--output', str(tmp_path / 'report.json')]) == 1


def test_runner_refuses_enabled_configuration(monkeypatch):
    from app.config import settings
    monkeypatch.setattr(settings(), 'ai_enabled', True)
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 2
