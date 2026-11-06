# Adding a teacher-reviewed synthetic case

No actual teacher-reviewed cases have been supplied. `teacher_reviewed.jsonl` is intentionally empty. Do not copy the simulated review metadata in unit tests into this dataset or claim a teacher has reviewed it.

1. Ask an authorized teacher to review a **synthetic** source, learner question, grade/language, selected evidence, and the actual delivered response from the offline runner. Never add real student data.
2. Add the case to `teacher_reviewed.jsonl` and a corresponding stub entry to a responses JSON file. Cases require `id`, `data_origin: "synthetic"`, `grade`, `language`, `source`, `question`, `gold_evidence`, and `review_status: "teacher-reviewed"`.
3. Record a pseudonymous `reviewer_id` and real `reviewed_at` date. Score delivered-output `factuality` and `grade_suitability` from 0 (fails) to 2 (meets the rubric). These scores must be provided by the reviewer, never generated from lexical overlap.
4. Add the hashes below under a `review` object. The runner rejects missing provenance or a changed source, question, grade, language, prompt, raw fixture, or delivered response. Hashes use the runner's `digest()` function (SHA-256 of canonical JSON), **not raw-file hashing**.

```python
from evals.run import digest, review_context, stub_provider
from app.ai import process_completion, retrieve

# case is a validated case during preparation, before attaching its final review.
# Use the SAME SQLite retrieval path as the runner for the delivered hash.
retrieved = retrieve(db, case.source, case.question)
delivered, _ = process_completion(stub_provider(entry), 'tutor', retrieved, case.language)
review_fields = {
    'source_sha256': digest(case.source),
    'context_sha256': digest(review_context(case)),
    'response_sha256': digest(entry),
    'delivered_sha256': digest(delivered.model_dump()),
}
```

The final `review` object also needs `reviewer_id`, `reviewed_at`, `factuality`, and `grade_suitability`. A failed provider response is a failure-rate case, not a successfully delivered response to grade. Review metadata is declared provenance: the runner cannot authenticate reviewer identities. Keep an independently approved review record outside the repository if the school requires one.

Teacher-demo cases also bind subject, topic, proposed learning objective, framework reference and draft reference answer in the context hash. An optional `curriculum_alignment` score uses the same 0–2 scale; leave it null when it has not been assessed. A null value is excluded from the measured denominator, not treated as zero or as approval. The generated review template starts at `pending-teacher-review` and must be completed from an actual review before changing its status.

Factuality rubric: 0 = contradicts/unsupported; 1 = partially supported or misleading; 2 = correct in the reviewed context. Grade rubric: 0 = unsuitable; 1 = needs adaptation; 2 = understandable and appropriate for the specified class/language. A source quotation is not automatically a score of 2 in either dimension.
