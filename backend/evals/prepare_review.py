"""Produce an offline, printable synthetic teacher-review pack and unscored template."""
import argparse
import json
from pathlib import Path
from app.config import settings
from .run import HERE, digest, evaluate, load_cases, review_context


def prepare(cases, responses, output_dir):
    if any(c.review_status != 'synthetic-unreviewed' for c in cases):
        raise ValueError('Preparation expects unreviewed synthetic cases; it must not overwrite completed reviews')
    report = evaluate(cases, responses)
    rows = {r['id']: r for r in report['records']}
    text = ['# Nexora AI — teacher review pack', '',
            '**Status: synthetic draft; no teacher approval or student use.**', '',
            'The proposed grades and curriculum mapping need a qualified teacher to confirm them. Sources and draft answers are original synthetic teaching notes, not copied textbook passages or verified AI outputs.', '',
            'Broad framework reference: https://cbseacademic.nic.in/cbe/learning-framework.html . This is not confirmation of a textbook edition or a grade-level mapping. Three Hindi questions currently retain English source excerpts; assess their accessibility explicitly.', '',
            '## Review instructions', '',
            'Review the learner question, source notes and actual delivered response. Score factuality, age/grade suitability and curriculum alignment independently: 0 = fails; 1 = needs correction/adaptation; 2 = meets the criterion. Leave all scores blank until reviewed. Check both whether a claim is true and whether it answers this question.', '',
            'The tutor currently returns excerpts with fixed framing. The draft reference answer is hand-authored for discussion, not a model result. Neither source matching nor a high retrieval score proves correctness or usefulness. Confirm the exact textbook/edition and learning outcome used by your school.', '',
            'Write corrections and a suggested explanation that a learner could understand. Do not include real student information. Record a reviewer pseudonym and actual review date in the companion template only after reviewing.', '',
            '## Coverage', '', '| ID | Proposed class | Subject | Topic |', '| --- | --- | --- |']
    templates = []
    for case in cases:
        text.append(f'| {case.id} | {case.grade} | {case.subject} | {case.topic} |')
    for case in cases:
        row = rows[case.id]
        if row['failed']:
            raise ValueError(f'Cannot prepare a scored delivered-output review for failed case {case.id}')
        text += ['', f'## {case.id} — Class {case.grade}, {case.subject}', '',
                 f'**Topic:** {case.topic}', f'**Draft learning objective:** {case.learning_objective}', '',
                 f'**Learner question ({case.language}):** {case.question}', '',
                 '**Synthetic source notes:**', '', '> ' + case.source.replace('\n', '\n> '), '',
                 '**Draft reference answer — not teacher verified:** ' + (case.reference_answer or 'Not supplied'), '',
                 '**Actual delivered response from the offline stub pipeline:**', '',
                 '> ' + row['delivered']['answer'].replace('\n', '\n> '), '',
                 '**Teacher review (leave blank until completed):**', '',
                 '- Factuality (0/1/2): ____', '- Age/grade suitability (0/1/2): ____',
                 '- Curriculum alignment (0/1/2): ____', '- Exact textbook/edition/outcome: ____',
                 '- Corrections / suggested explanation: ____', '- Reviewer pseudonym and actual review date: ____', '',
                 '---']
        payload = case.model_dump(mode='json')
        payload['review_status'] = 'pending-teacher-review'
        payload['review'] = {'reviewer_id': '', 'reviewed_at': '', 'source_sha256': digest(case.source),
                             'response_sha256': digest(responses[case.id]), 'context_sha256': digest(review_context(case)),
                             'delivered_sha256': digest(row['delivered']), 'factuality': None,
                             'grade_suitability': None, 'curriculum_alignment': None}
        templates.append(payload)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / 'TEACHER_REVIEW_PACK.md').write_text('\n'.join(text) + '\n', encoding='utf-8')
    (output_dir / 'review_cases.template.jsonl').write_text(''.join(json.dumps(c, ensure_ascii=False) + '\n' for c in templates), encoding='utf-8')
    (output_dir / 'README.md').write_text('# Review status: NOT REVIEWED\n\nThe template is intentionally incomplete and invalid as a reviewed dataset until a qualified teacher supplies their actual review. `pending-teacher-review` is an explicit placeholder, never a completed review. No scores or identities have been invented.\n\nShare TEACHER_REVIEW_PACK.md for offline review. Transfer only actual completed scores, reviewer pseudonym and date into a COPY of the template, then change that completed case status to `teacher-reviewed`. Keep curriculum alignment null if it has not been assessed. Run `python -m evals.run --cases path/to/completed-copy.jsonl --responses evals/teacher_demo_stubs.json --output path/to/reviewed-report.json` from backend. The runner verifies all hashes and rejects incomplete provenance.\n', encoding='utf-8')
    return {'cases': len(cases), 'reviewed_cases': 0, 'output_dir': str(output_dir)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cases', type=Path, default=HERE / 'teacher_demo_cases.jsonl')
    parser.add_argument('--responses', type=Path, default=HERE / 'teacher_demo_stubs.json')
    parser.add_argument('--output-dir', type=Path, default=HERE / 'teacher_demo_review')
    args = parser.parse_args(argv)
    if settings().ai_enabled:
        parser.error('Preparation requires AI_ENABLED=false')
    try:
        result = prepare(load_cases([args.cases]), json.loads(args.responses.read_text(encoding='utf-8')), args.output_dir)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    print(json.dumps(result))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
