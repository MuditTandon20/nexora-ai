"""Offline-only AI pipeline evaluation. No network provider or paid mode exists."""
import argparse
import hashlib
import json
from datetime import date
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.ai import PROMPT_VERSION, process_completion, retrieve
from app.config import settings

HERE = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def normalize(value):
    return ' '.join(value.casefold().split())


class Review(BaseModel):
    reviewer_id: str = Field(min_length=1)
    reviewed_at: date
    source_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    response_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    context_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    delivered_sha256: str = Field(pattern=r'^[0-9a-f]{64}$')
    factuality: int = Field(strict=True, ge=0, le=2)
    grade_suitability: int = Field(strict=True, ge=0, le=2)


class Case(BaseModel):
    id: str = Field(min_length=1)
    data_origin: Literal['synthetic'] = 'synthetic'
    grade: int = Field(ge=1, le=10)
    language: Literal['en', 'hi']
    source: str = Field(min_length=20, max_length=60000)
    question: str = Field(min_length=3, max_length=1000)
    review_status: Literal['synthetic-unreviewed', 'teacher-reviewed']
    gold_evidence: list[str] = Field(default_factory=list)
    must_refuse: bool = False
    expected_failure: bool = False
    review: Review | None = None

    @model_validator(mode='after')
    def labelled(self):
        if (self.review_status == 'teacher-reviewed') != (self.review is not None):
            raise ValueError('Teacher-reviewed cases require review provenance and scores; unreviewed cases must not supply teacher scores')
        if any(not evidence.strip() or normalize(evidence) not in normalize(self.source) for evidence in self.gold_evidence):
            raise ValueError('Gold evidence must occur in this case source')
        return self


def load_cases(paths):
    cases = []
    ids = set()
    for path in paths:
        for number, line in enumerate(Path(path).read_text(encoding='utf-8').splitlines(), 1):
            if not line.strip():
                continue
            try:
                case = Case.model_validate_json(line)
                if case.id in ids:
                    raise ValueError('Duplicate case ID')
            except ValueError as exc:
                raise ValueError(f'Invalid dataset entry {path}:{number}: {exc}') from exc
            ids.add(case.id)
            cases.append(case)
    if not cases:
        raise ValueError('At least one evaluation case is required')
    return cases


def review_context(case):
    return {'source': case.source, 'question': case.question, 'grade': case.grade,
            'language': case.language, 'prompt_version': PROMPT_VERSION}


def stub_provider(entry):
    if entry.get('error') == 'timeout':
        raise TimeoutError('Synthetic provider timeout')
    if 'raw' in entry:
        return entry['raw']
    return {'choices': [{'message': {'content': json.dumps(entry['response'], ensure_ascii=False)}}],
            'usage': entry.get('usage')}


def human_scores(rows, dimension):
    values = [row[dimension] for row in rows]
    return {'status': 'measured_on_reviewed_stub_outputs' if values else 'unmeasured',
            'reviewed_outputs': len(values), 'mean_score_0_to_2': sum(values) / len(values) if values else None}


def evaluate(cases, responses):
    """Measure fixture/pipeline behavior; never infer a teacher score from text."""
    engine = create_engine('sqlite://')
    records, reviews = [], []
    try:
        with Session(engine) as db:
            for case in cases:
                if case.id not in responses:
                    raise ValueError(f'Missing stub response for {case.id}')
                entry = responses[case.id]
                if case.review:
                    if (case.review.source_sha256 != digest(case.source) or case.review.response_sha256 != digest(entry)
                            or case.review.context_sha256 != digest(review_context(case))):
                        raise ValueError(f'Review does not match the exact source/response fixture for {case.id}')
                retrieved = retrieve(db, case.source, case.question)
                hits = sum(normalize(e) in normalize(retrieved) for e in case.gold_evidence)
                row = {'id': case.id, 'cohort': case.review_status, 'retrieval_hits': hits,
                       'retrieval_gold_spans': len(case.gold_evidence), 'failed': False,
                       'expected_failure': case.expected_failure, 'abstained': None,
                       'delivery_evidence_only': None, 'error_type': None}
                try:
                    result, _ = process_completion(stub_provider(entry), 'tutor', retrieved, case.language)
                    row['abstained'] = result.insufficient_context
                    row['delivery_evidence_only'] = result.insufficient_context or (result.source_quote in retrieved and result.source_quote in result.answer)
                    # Store synthetic delivered output for review, not inferred truth labels.
                    row['delivered'] = result.model_dump()
                except Exception as exc:
                    row['failed'], row['error_type'] = True, type(exc).__name__
                if case.review:
                    if row['failed'] or case.review.delivered_sha256 != digest(row['delivered']):
                        raise ValueError(f'Review does not match the delivered output for {case.id}')
                    reviews.append(case.review.model_dump())
                row['unexpected_outcome'] = (row['failed'] != case.expected_failure or
                    (not row['failed'] and row['abstained'] != case.must_refuse))
                records.append(row)
    finally:
        engine.dispose()
    spans = sum(r['retrieval_gold_spans'] for r in records)
    failures = sum(r['failed'] for r in records)
    unexpected = sum(r['unexpected_outcome'] for r in records)
    teacher_count = sum(c.review_status == 'teacher-reviewed' for c in cases)
    return {'schema_version': 1, 'provider': 'offline-stub-v1', 'prompt_version': PROMPT_VERSION,
            'dataset_sha256': digest([c.model_dump(mode='json') for c in cases]), 'responses_sha256': digest(responses),
            'case_count': len(cases), 'cohorts': {'synthetic_unreviewed': len(cases) - teacher_count, 'teacher_reviewed': teacher_count},
            'metrics': {'factuality': human_scores(reviews, 'factuality'),
                        'grade_suitability': human_scores(reviews, 'grade_suitability'),
                        'retrieval': {'backend': 'SQLite lexical fallback', 'reference_spans': spans,
                                      'retrieved_reference_spans': sum(r['retrieval_hits'] for r in records),
                                      'reference_span_recall': sum(r['retrieval_hits'] for r in records) / spans if spans else None},
                        'failure_rate': failures / len(cases), 'failures': failures,
                        'unexpected_outcome_rate': unexpected / len(cases), 'unexpected_outcomes': unexpected},
            'limitations': ['Stub/pipeline measurements are not live model quality measurements.',
                'Factuality and grade scores are aggregated only from explicitly supplied, hash-bound human annotations.',
                'Review metadata is declared provenance; the runner does not authenticate a reviewer identity.',
                'Reference-span retrieval and evidence-only delivery do not establish semantic truth or question relevance.',
                'Expected malformed/timeout fixtures count in failure_rate; inspect unexpected_outcome_rate separately.',
                'No teacher-reviewed cohort means human dimensions are null, not zero or perfect.'],
            'records': records}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', nargs='+', type=Path, default=[HERE / 'cases.jsonl', HERE / 'teacher_reviewed.jsonl'])
    parser.add_argument('--responses', type=Path, default=HERE / 'stub_responses.json')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    if settings().ai_enabled:
        parser.error('Offline evaluations require AI_ENABLED=false')
    try:
        report = evaluate(load_cases(args.cases), json.loads(args.responses.read_text(encoding='utf-8')))
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding='utf-8')
    print(json.dumps({'cases': report['case_count'], 'cohorts': report['cohorts'], 'metrics': report['metrics']}, ensure_ascii=False))
    return 1 if report['metrics']['unexpected_outcomes'] else 0


if __name__ == '__main__':
    raise SystemExit(main())
