# Nexora AI — teacher-facing local demo

**Synthetic school only. AI remains disabled.** The demo is designed to show the everyday attendance, materials and feedback workflows before seeking an authorized school pilot.

## Open the demo

After the dependency setup in the root README, close any previous demo using ports 3001/8001. From the repository root:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/start-teacher-demo.ps1
```

Open **http://localhost:3001/login**. The helper creates a fresh local database under `.demo/` each time; it does not erase or reuse existing school records. It starts FastAPI and Next.js locally, forces `AI_ENABLED=false`, and uses no model, hosting or storage subscription. Press Ctrl+C in that terminal to stop it. Do not run multiple Nexora sessions on localhost simultaneously; cookies are shared by hostname.

| Role | Account | Demo password |
| --- | --- | --- |
| Teacher | teacher@nexora.demo | NexoraDemo!2026 |
| Administrator | admin@nexora.demo | NexoraDemo!2026 |
| Student | student@nexora.demo | NexoraDemo!2026 |

There are **3 classes, 18 synthetic learners and 6 submissions waiting for review**. Class 7 starts with attendance unmarked; Classes 6 and 8 show saved attendance. All names, notes and work are fabricated demonstration records. The seed refuses production, enabled AI, remote databases, nonlocal storage or an existing school database.

## Suggested five-minute walkthrough

1. **Orient:** sign in as teacher. “Today’s classes” shows each class, its attendance state and pending submissions. The header labels the synthetic demo.
2. **Attendance:** choose “Mark attendance” beside Class 7. The correct class is already selected. Everyone starts present; tap an absence, review the totals, then confirm. Reopening a saved roll call requires a correction reason to change it.
3. **Feedback:** return to Overview. Open “Friction around you” from the waiting-review list. The existing submission-review dialog opens directly. Read one answer, add feedback and mark complete or request revision. The count updates when returning to Overview.
4. **Create homework:** choose “Create an assignment” on Overview. The form opens immediately; choose class/subject, give clear instructions and a due date, then share. Use synthetic content only.
5. **Share notes:** choose “Share study material”. The draft form opens immediately. Write a short lesson or upload a readable PDF, then review and approve it. Sign in as the demo student in a separate browser profile to see published notes and their own work.
6. **Set expectations:** AI status remains off. Existing teacher-authored practice is available in Arena. Study Buddy is still a constrained source-excerpt prototype, not an evaluated interactive teacher.

## Observed interaction measurements

The [raw benchmark](demo/workflow-measurements.json) ran three trials per path on a local Chromium session, alternating path order. A click or `selectOption` command counts as one logical interaction. Setup/login, typing, saving and reading time are excluded.

| Task-entry point | Existing manual navigation | Dashboard shortcut | Manual median | Shortcut median |
| --- | --- | --- | --- | --- |
| Open Class 7 attendance | 2 interactions | 1 interaction | 247 ms | 191 ms |
| Open new assignment form | 2 interactions | 1 interaction | 161 ms | 88 ms |
| Open a waiting submission | 2 interactions | 1 interaction | 175 ms | 194 ms |

**Measured finding:** each shortcut removes one navigation/selection action. The review shortcut was slightly slower in this small timed sample. These timings are not statistically controlled teacher measurements and do not establish daily minutes saved or improvement over paper processes.

For a teacher usability session, record this blank worksheet rather than estimating a benefit:

| Task | Teacher baseline time | Nexora time | Errors/help needed | Teacher comment |
| --- | --- | --- | --- | --- |
| Mark a class’s attendance | ___ | ___ | ___ | ___ |
| Create and share homework | ___ | ___ | ___ | ___ |
| Read and return feedback | ___ | ___ | ___ | ___ |

Agree a consistent task and student count, observe both methods, include correction/reading time and repeat across teachers before making a time-saving claim.

## Teacher evaluation handover

Share [the 27-question review pack](../backend/evals/teacher_demo_review/TEACHER_REVIEW_PACK.md). It contains nine questions each for Classes 6, 7 and 8; nine each in Science, Mathematics and English; and three Hindi learner questions. Source notes, reference answers and learning objectives are synthetic drafts. The [CBSE learning framework](https://cbseacademic.nic.in/cbe/learning-framework.html) is a broad reference; the reviewer must confirm the exact school textbook/edition and grade mapping.

The user will arrange the qualified teacher review. No review has been performed or attributed to a teacher. Use the companion template only after actual scores, reviewer pseudonym and date are supplied; its current `pending-teacher-review` entries and null scores intentionally fail reviewed-dataset validation. The runner binds completed reviews to the exact case and delivered output using hashes.

## Verification and limitations

Independent baseline: **61 backend tests / 8 browser tests**, typecheck and build passed. After this milestone: **68 backend tests / 9 browser tests**, typecheck and production build passed. The new tests cover authorized class-task summaries, student privacy, demo guardrails, question coverage, unscored template rejection and the dashboard task links.

The 27-case offline stub run retrieved **27/27 reference spans** and had **0 unexpected outcomes**. All passages are short; this is not a broad retrieval benchmark or a live-model quality result. **Factuality, age/grade suitability and curriculum alignment remain unmeasured** pending teacher review. See [the machine report](../backend/evals/results/teacher-demo-stub.json).

PostgreSQL/S3 behavior, privacy/retention/deletion operations, upload isolation, deployment hardening, child-safety evaluation and real classroom usability remain release gates from [the audit](NEXORA_MVP_AUDIT.md). Do not introduce real student data or enable a model during this demo.

Preview artifacts: [desktop](demo/teacher-desktop.png), [mobile](demo/teacher-mobile.png).

## Reproduce the offline evidence

```powershell
Set-Location backend
$env:AI_ENABLED = 'false'
..\.venv\Scripts\python.exe -m pytest -q
..\.venv\Scripts\python.exe -m evals.run --cases evals/teacher_demo_cases.jsonl --responses evals/teacher_demo_stubs.json --output evals/results/teacher-demo-stub.json
..\.venv\Scripts\python.exe -m evals.prepare_review
```

For the full browser suite, migrate a NEW disposable database, run `python -m app.demo`, point the API/production frontend at local ports 8001/3001, then run `npx.cmd playwright test --config playwright.audit.config.ts`. Full runs need fresh data because practice attempts are limited per day. Do not point tests at an actual school.

To rerun the nonmutating task-entry benchmark against a fresh running teacher demo:

```powershell
Set-Location frontend
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD/../.playwright"
node scripts/measure-teacher-demo.mjs
```
