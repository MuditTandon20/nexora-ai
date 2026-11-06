# Review status: NOT REVIEWED

The template is intentionally incomplete and invalid as a reviewed dataset until a qualified teacher supplies their actual review. `pending-teacher-review` is an explicit placeholder, never a completed review. No scores or identities have been invented.

Share TEACHER_REVIEW_PACK.md for offline review. Transfer only actual completed scores, reviewer pseudonym and date into a COPY of the template, then change that completed case status to `teacher-reviewed`. Keep curriculum alignment null if it has not been assessed. Run `python -m evals.run --cases path/to/completed-copy.jsonl --responses evals/teacher_demo_stubs.json --output path/to/reviewed-report.json` from backend. The runner verifies all hashes and rejects incomplete provenance.
