# Nexora AI MVP audit

## AI evaluation + teacher demo — current milestone

**Implementation commit:** `56a15169332cf27d1eb7586c997c6e2a6ff0e5ec` — `Prepare teacher-facing demo and synthetic curriculum review pack`. **Starting revision:** `a20bddc`. Verified locally on 6 November 2026. The earlier audit and stabilization results below remain historical snapshots.

### Delivered scope

- Teacher dashboard now shows authorized classes with per-class attendance and pending-review counts. Its links preselect the intended attendance class, open a pending assignment directly for review, and open the existing assignment/material creation dialogs. Pending reviews are prioritized on the overview. Students do not receive staff class-task summaries or other students' pending counts.
- Existing UI, modular monolith, schema and dependencies are preserved. No Knowledge DNA, adaptive learning or new AI product capability was introduced. The dashboard makes disabled AI explicit and prioritizes ordinary classroom tools.
- A fresh local teacher demo contains **3 classes, 18 synthetic learners and 6 pending reviews**. Classes 6 and 8 have saved attendance; Class 7 is ready to mark. Notes, submissions and feedback are synthetic. The seed refuses production, enabled AI, remote databases, nonlocal storage and existing school databases.
- **27 draft questions** cover Classes 6–8: nine per grade, nine each for Science/Mathematics/English, including three Hindi learner questions. Every case has original synthetic source notes, a draft objective/reference answer and a broad framework reference. This does not establish correct textbook/grade mapping.
- [Teacher review pack](../backend/evals/teacher_demo_review/TEACHER_REVIEW_PACK.md), [unscored template](../backend/evals/teacher_demo_review/review_cases.template.jsonl), [demo guide](TEACHER_DEMO_GUIDE.md), screenshots and measured task-entry evidence are committed. The user will arrange the qualified teacher review; no outreach, reviewer identity or approval was fabricated.

### Independent verification and results

| Check | Independently observed result |
| --- | --- |
| Starting-revision backend rerun | **61 passed**, 30.18 s; package consistency passed |
| Starting-revision frontend/browser rerun | Typecheck/build passed; **8 browser tests passed**, 19.9 s, exit 0 |
| Final complete backend suite | **68 passed**, 120.77 s; one existing Starlette TestClient deprecation warning; package consistency passed |
| Final frontend | Typecheck and production build passed; 15 routes generated; build also passed after restoring the ordinary API rewrite |
| Final complete Chromium suite | **9 passed**, reported duration 1.4 min, exit 0; fresh `.audit/teacher-demo-final.db` |
| SQLite migrations | Fresh upgrade/check passed; no schema change introduced |
| Teacher-demo starter | PowerShell syntax/port guard checked; actual starter created a new `.demo/` database, launched the API/development frontend, and passed login/dashboard smoke checks |
| Presentation | Desktop 1440px and mobile 390px captures; three class rows; no observed page errors or horizontal overflow; AI status false |

The new browser regression exercises contextual attendance, direct pending-review opening and both creation shortcuts. New backend tests cover dashboard privacy/actionability, seed guardrails/freshness, 27-case coverage and rejection of an incomplete review template. The existing authorization, PDF, attendance, submissions and disabled-AI suites remain passing.

One new seed test initially inherited the global test `sqlite://` setting and was correctly rejected by the file-only demo guard. Its isolated configuration was corrected; no guard was relaxed. Development screenshot automation needed navigation-aware waiting for first-route compilation and an absolute API URL; the corrected smoke check passed. Starter Ctrl+C teardown was not automatically asserted. Production-browser verification and the local development smoke check are distinct observations.

### Evaluation evidence

The [27-case offline report](../backend/evals/results/teacher-demo-stub.json) uses hand-authored stub outputs and SQLite lexical retrieval. It reports **27/27 labelled spans retrieved**, **0/27 pipeline failures** and **0/27 unexpected outcomes**. All sources are short; this is not a broad retrieval, live-model or adversarial-safety benchmark. The earlier ten negative-fixture cases remain separate regression coverage.

**Factuality, grade suitability and curriculum alignment are all unmeasured**, with null scores and zero reviewed outputs. No qualified teacher review has occurred. The template is explicitly `pending-teacher-review` with blank identity/date and null scores, and is intentionally rejected as a completed reviewed dataset. Completed review scores must bind to the exact source, question, grade/language, objective, reference answer, raw stub and delivered output. The runner does not authenticate a teacher's qualifications and does not equate a zero pipeline-error count with educational approval.

Source/grade mapping is a draft for reviewer confirmation. The [CBSE learning framework](https://cbseacademic.nic.in/cbe/learning-framework.html) was consulted as a broad reference; no official endorsement or current-edition textbook alignment is claimed. Hindi questions currently receive original English source excerpts with Hindi framing; the teacher must assess that accessibility limitation.

### Measured workflow evidence

The [raw workflow measurements](demo/workflow-measurements.json) contain three trials per path, alternating path order in warm local Chromium sessions. Each click/select command counts as one logical interaction. Login, returning to Overview, typing, reading and saving are excluded.

| Task-entry check | Existing manual path | Dashboard shortcut | Manual median | Shortcut median |
| --- | --- | --- | --- | --- |
| Class 7 attendance | 2 interactions | 1 interaction | 247 ms | 191 ms |
| New assignment form | 2 interactions | 1 interaction | 161 ms | 88 ms |
| Waiting submission | 2 interactions | 1 interaction | 175 ms | 194 ms |

All three shortcuts remove one logical navigation action. The review shortcut was slightly slower in this timed sample. **No human teacher time-saving measurement, paper-workflow comparison or daily minutes-saved claim is made.** The guide includes a blank worksheet for an observed teacher session.

### Operational boundaries

`AI_ENABLED=false` was explicit for every demo server, seed and evaluation command. No paid provider, public deployment, production resource or real student data was used. The normal production build rewrite was restored to port 8000 before the separate local demo helper was launched; helper development mode uses local ports 3001/8001 and a fresh `.demo/` database. Development-only generated type-reference imports were restored to their tracked form; Next.js-generated agent guidance was retained.

Unresolved release gates from the stabilization audit still apply: F-05 semantic truth/relevance/age safety, F-06 database tenant defense in depth, PostgreSQL/S3 verification, privacy/retention/deletion, upload isolation, production configuration, backup restoration and real teacher/student usability. This milestone prepares an honest teacher demo and review handover, not an evaluated interactive AI teacher or production readiness clearance.

## Prior stabilization milestone

**Verified 6 November 2026. Implementation commit:** `1ed2bcb2fcb599d99219f4793eab6b23ddf2c1e1` — `Stabilize MVP validation and add offline AI evaluations`. **Parent/baseline:** `633d737`. This report is recorded in a following documentation commit so it can identify the actual implementation hash without a self-referential commit hash.

The original audit below is retained as a **historical snapshot**, including its original counts and open findings. The status in this milestone section supersedes it. The architecture, database schema, dependencies and product UI are preserved. No product features, real student data, deployments, live model calls or paid resources were introduced. `AI_ENABLED=false` remains the runtime default and was explicitly set for both verification servers and the evaluation CLI. Tests exercise provider paths only after replacing the provider boundary with stubs.

### Findings addressed

| Finding | Current status | Actual change and regression evidence |
| --- | --- | --- |
| **F-01** | Fixed | Class names are stripped before length validation. Whitespace-only/too-short normalized names return 422, valid padded names are stored normalized, and duplicate normalized names return 409. API regressions plus a browser test verify rejection and subsequent successful creation in the same form. |
| **F-02** | Fixed for tested adapter/response cases | Pydantic validates the provider envelope, completion state, content and nonnegative strict-integer token counts. Missing/null usage is treated as unavailable, without failing a valid response. Malformed metadata/incomplete output returns 502 with a terminal event; unexpected adapter exceptions are also recorded terminally. Null/valid usage, negative/string/boolean counts, invalid shapes, truncation, timeouts and an unexpected stub exception are covered. Database-outage/crash recovery remains unverified. |
| **F-03** | Fixed | An outer ASGI guard rejects malformed/negative/ambiguous length headers with 400 and oversize declared or actual bodies with 413. It reads and buffers at most 11 MiB of request content before downstream parsing, independently of `Content-Length`. Tests cover absent/misleading headers, incremental byte limits, duplicate headers, a 12 MiB streamed FastAPI request, and valid small streamed requests. The PDF limit remains 10 MiB. This is not a concurrent-load/memory-budget certification. |
| **F-04** | Fixed for tested retry/revision behavior | An exact retry of an unreviewed submission is a no-op, including timestamp and notification. Changing an already-pending draft updates the same submission without another pending-review alert. Resubmitting after `needs_revision` produces one new actionable alert; retrying that resubmission does not. Completed work still rejects changes. Existing submission rows are locked on PostgreSQL; concurrent PostgreSQL behavior is not yet measured. |
| **F-07** | Fixed contract/traceability gaps; semantic review still required | Packs require at least five MCQs, one short answer and two cards with distinct normalized fronts. Summaries/card backs must use source-excerpt sentences. Generate, edit and publication paths validate the complete contract; an incomplete legacy draft cannot newly publish. Regressions also verify rejected edits leave the draft unchanged and a complete pack still edits/publishes successfully. Existing already-published packs are not retroactively revalidated or rewritten. Questions, distractors, relevance and interpretation still require teacher review. |
| **F-05** | Mitigated, **not a semantic factuality clearance** | The tutor no longer serves unverified provider explanations or follow-up claims. It returns an original approved-source excerpt with fixed framing/follow-up, or a fixed abstention. The exact contradictory-answer probe that passes quotation validation is covered in English and Hindi and its generated claim/follow-up are absent from the delivered response. This suppresses unsupported prose; it does not establish that a source is true, relevant, safe or appropriate for a grade. Model-selected evidence and abstention can still be wrong. |
| **F-08** | Test-date issue corrected as verification maintenance | The assignment browser test uses a relative future due date. Full browser runs still deliberately use a fresh seeded database because daily practice attempts are not repeatable on a reused student/database. |

**Tutor/pack trade-off:** source excerpts stay in the source language, including for Hindi questions; Hindi framing is localized but a translation is not treated as verified. Generated tutor explanations are deliberately constrained, not advertised as semantically verified. Summary/card editing is now more restrictive: unsupported paraphrases are rejected. No second model/verifier service, vector database, new dependencies or additional provider calls were added.

### Complete verification results for the implementation commit

| Check | Observed result |
| --- | --- |
| Complete backend suite | **61 passed**, 27.67 s; one existing Starlette/httpx TestClient deprecation warning |
| Backend package consistency | `python -m pip check`: no broken requirements |
| Frontend typecheck | Passed, no TypeScript errors |
| Production frontend build | Passed, all 15 routes generated; also passed again when restoring the normal local API rewrite |
| Complete Chromium E2E suite | **8 passed**, 17.5 s, underlying process exit **0** |
| SQLite Alembic verification | Fresh `upgrade head`, `current` = `0001 (head)`, schema check, downgrade, re-upgrade, schema check all passed; no schema drift/migration added |
| Offline evaluation command | Passed, exit 0; 10 synthetic cases, 3 deliberately failing cases handled as declared, **0 unexpected outcomes** |
| Safety/cleanup | Audit servers used only `.audit/stabilization-browser.db`, local ports 3001/8001 and synthetic accounts; those temporary servers were stopped. The final build's rewrite was restored to `http://127.0.0.1:8000`. No remote Git push occurred. |

Browser coverage retains the full admin → teacher → student attendance flow, notes/homework/submission/review flow, mobile flashcards/short-answer practice, saved five-question challenge, offline cache privacy, disabled AI Studio/Study Buddy, and adds the F-01 form regression. The backend suite retains cross-school/cross-student authorization, PDF access, stale attendance, password/session revocation and malformed AI checks alongside the new finding-specific regressions.

The streamed-body integration test initially exposed downstream middleware reclassifying an oversize exception as a generic 400. The final guard enforces the limit before parsers run; the integration test now receives 413. This was corrected before the final passing suite. No passing intended-behavior claim is based on the earlier failing run.

Local raw logs: `.audit/stabilization-backend-final.txt`, `.audit/stabilization-playwright.txt`, `.audit/stabilization-build.txt`, and `.audit/stabilization-build-restored.txt`. These are ignored machine artifacts. Tracked regression tests and the evaluation JSON preserve reproducible evidence.

### Executable AI evaluation and actual measurements

Run from `backend` with the existing virtualenv:

```powershell
$env:AI_ENABLED = 'false'
..\.venv\Scripts\python.exe -m evals.run --output evals/results/stabilization-stub.json
```

The runner has **no live-provider mode**. It uses the runtime retrieval/output-processing functions and deterministic provider fixtures. It refuses enabled configuration and exits nonzero on unexpected pipeline outcomes or invalid/mismatched review inputs. Output includes prompt version `nexora-v2`, dataset/fixture hashes, delivered synthetic outputs, cohort counts and metric denominators. See [runner documentation](../backend/evals/README.md), [review format](../backend/evals/REVIEW_FORMAT.md), and [committed results](../backend/evals/results/stabilization-stub.json).

| Requested dimension | Actual measured result | What it does not mean |
| --- | --- | --- |
| Factuality | **Unmeasured**: 0 reviewed outputs, score `null` | No teacher score or live-model factuality was invented. Source containment is not factuality. |
| Retrieval | **4/4** labelled reference spans retrieved; reference-span recall **1.0** on SQLite lexical fallback | Only four spans from short synthetic chapters; not a broad retrieval-quality, question-relevance, multilingual retrieval or PostgreSQL benchmark. |
| Grade suitability | **Unmeasured**: 0 reviewed outputs, score `null` | No readability/age/safety conclusion can be inferred from the stub run. |
| Failure rate | **3/10 = 0.30**: intentionally invalid envelope, unsupported quote and simulated timeout | These were deliberate negative fixtures, not an observed 30% failure rate for a model. |
| Unexpected outcome rate | **0/10 = 0.0** | Agreement with hand-authored fixture expectations, not real-world model accuracy or safety. |

No teacher-reviewed file was supplied. `teacher_reviewed.jsonl` is deliberately empty. The runner accepts actual teacher-reviewed **synthetic** cases and requires reviewer/date plus hashes binding the source, question, grade/language, prompt version, raw fixture and delivered response. It aggregates supplied 0–2 factuality/grade scores only after those bindings match. An explicitly simulated reviewer record tests bookkeeping in the unit suite; it is not part of the evaluation dataset/results or evidence of a teacher review. Declared review metadata does not authenticate the reviewer identity.

The committed evaluation JSON is deterministic for unchanged code/data. A report hash and dataset hash are provenance, not proof of correctness. The runtime guard's excerpt-only delivery is a conservative mitigation while semantic evaluation is incomplete.

### Remaining risks and next gates

- **F-06 remains open:** database-level tenant equality/role constraints and PostgreSQL RLS have not been added; API authorization tests pass but direct invalid database writes need defense in depth.
- **F-05 remains a release gate:** source truth, evidence relevance, safe-source selection, correct abstention, grade suitability and substantive Hindi explanations have not been teacher-evaluated. No live model output quality, comprehension benefit, latency or inference-cost accuracy is claimed. Keep AI disabled.
- Actual PostgreSQL row locking/full-text behavior, S3 permissions/encryption, Docker deployment, backup/restore and concurrent-update behavior remain unverified. Verification used SQLite and local files only.
- PDF malware scanning/parser isolation, privacy/consent/retention/deletion operations, production configuration enforcement, proxy/distributed rate limiting and global monetary budgets remain unresolved. The 11 MiB body bound does not replace parser isolation or load testing.
- Existing published packs are frozen and not automatically made compliant with the new excerpt/short-answer contract. A future authorized migration/review policy would be needed for any legacy real deployment; no such production data was touched here.
- No dependency versions changed. Earlier advisory scan results are historical observations, not a new vulnerability scan or a perpetual guarantee.
- The TestClient deprecation warning remains. There was no unrelated refactoring or dependency migration.

**No production or real-student readiness claim is made.** Next work should obtain real teacher-reviewed synthetic cases and verify the intended PostgreSQL/storage/deployment topology privately, under separate authorization, before broadening behavior or enabling a provider.

## Original audit snapshot — before stabilization

**Audit date:** 6 November 2026, Asia/Kolkata.

**Baseline:** local commit `633d737` on `main`.
**Scope:** frontend, FastAPI, migrations/schema, authentication, tenant/student authorization, files, attendance, homework, Arena, AI integration, evaluation design and dependencies.

## Verdict

**The tested local, AI-disabled core workflows work. This is not yet a clearance to use real student data or deploy a school pilot.**

The final backend suite has **22 passing tests**. The final Chromium run has **7 passing E2E tests**. Frontend typecheck, production build, SQLite migration upgrade/downgrade/re-upgrade, and schema-drift checks passed. Both dependency advisory scans returned no known vulnerabilities for their checked dependency sets.

No critical blocker was found in the exercised admin → teacher → student workflows. **No application features, runtime logic, schemas, dependency versions or production resources were changed.** New regression tests, an isolated Playwright configuration, this report, and ignore rules for local audit artifacts were added. Noncritical defects and release blockers below were deliberately left for prioritized follow-up.

## Environment and evidence boundaries

- Windows; Python 3.10.11; Node 22.18.0; Next.js 16.4.5; React 19.3.1; Playwright 1.65.0/Chromium.
- Backend unit/integration tests use fresh in-memory SQLite databases and synthetic School A/School B accounts. They build tables from SQLAlchemy metadata rather than running Alembic.
- Separately, Alembic was exercised on a disposable file database under `.audit/`. The migrated database contains 19 tables including `alembic_version` and is at revision `0001`.
- Browser tests use freshly migrated/seeded `.audit/browser-final.db`, FastAPI at `127.0.0.1:8001`, and the production Next.js server at `localhost:3001`. The existing `backend/nexora.db` was not used for audit browser writes.
- Browser roles: `admin@nexora.demo`, `teacher@nexora.demo`, and `student@nexora.demo`. All accounts, names, assignments, PDF content and answers used in this audit were synthetic.
- Audit API servers explicitly ran with **`AI_ENABLED=false`**. Provider-enabled code paths were exercised only with in-process stubs; all new backend audit tests forbid an unstubbed provider call. No live model inference, paid API, deployment, bucket provisioning or production-resource mutation occurred.
- Local raw records are excluded from Git in `.audit/`: `backend-baseline.txt`, `backend-final.txt`, `frontend-typecheck.txt`, `frontend-build.txt`, `playwright-final.txt`, `npm-audit.json`, `pip-audit.json`, `findings.json` and disposable databases/probe scripts. The tracked tests and this report preserve the intended reproducible checks.

**Verified** below means an executed check or a directly inspected implementation. **Risk/inference** means the code suggests a concern but the target deployment or concurrency scenario was not exercised. **Not verified** is not a passing result.

## Executed checks

| Check | Result | Exact scope/evidence |
| --- | --- | --- |
| Existing backend suite | PASS | `python -m pytest -q`: 10 passed, 6.88 s before audit additions |
| Expanded backend suite | PASS | Same command: **22 passed, 12.39 s**, one Starlette TestClient deprecation warning |
| Python package consistency | PASS | `python -m pip check`: no broken requirements; all **53** locked package versions matched the installed application environment |
| Alembic revision | PASS | `python -m alembic current`: `0001 (head)` |
| Migration lifecycle | PASS, SQLite only | On a disposable empty DB: `upgrade head` → `check` → `downgrade base` → `upgrade head` → `check`; no new upgrade operations detected |
| Migrated constraints | PASS | Inspected unique attendance `(class_id, day, student_id)` and submission `(homework_id, student_id)` constraints |
| Frontend typecheck | PASS | `npm.cmd run typecheck`; also rerun after adding the audit tests |
| Production build | PASS | `npm.cmd run build`: compiled, TypeScript completed, all 15 routes generated |
| Original E2E stories | PASS | Four original browser tests passed on the isolated audit API/database |
| Final full E2E suite | PASS | `npx.cmd playwright test --config playwright.audit.config.ts`: **7 passed, 15.3 s**; underlying Playwright process exit code explicitly captured as **0** |
| JavaScript advisory scan | PASS for known advisories | `npm.cmd audit --json --cache ../.npm-cache`: zero info/low/moderate/high/critical entries; registry metadata described a 135-dependency tree |
| Python advisory scan | PASS for known advisories | Isolated `pip-audit` 2.10.1, `--no-deps --disable-pip -r backend/requirements.lock.txt`: all **53** locked entries returned empty vulnerability lists; exit 0 |
| Sensitive offline caching | PASS in tested browser | Service-worker cache contained only `/offline.html` and `/icon.svg`; offline navigation showed the public fallback |

A first expanded-test run had **21 passes and one incorrect test expectation**: it expected School B's audit list to be empty after creating two School B accounts. The application correctly recorded those actions. The test now asserts that the returned rows belong to School B's actor; no application fix was needed. Early PowerShell output-file setup also needed the audit directory created before logging. These were harness issues, not application failures.

## Complete workflows verified

### Admin → teacher → student attendance

The browser admin signed in, created a synthetic class, selected Meera Iyer as teacher and Aarav Mehta/Diya Kapoor as students. The teacher signed in in a separate browser context, chose that class, marked Diya absent, reviewed the roll-call summary and confirmed. The student signed in separately, selected the class and saw their own `present` status. The student page did not contain Diya's name. This exercised UI → Next.js `/api` rewrite → authenticated FastAPI handler → migrated database → response → student UI.

Backend checks separately verified both students' own statuses, rejection of student roster access, a required correction reason, correction audit creation, and a stale version returning **409 without replacing a newer saved roll call**. Exactly two attendance rows remained for two students. This was sequential optimistic-concurrency testing; simultaneous PostgreSQL row locking was **not** tested.

### Notes, assignments and review

A teacher saved text notes as a draft, approved them, created an assignment, and a student saw the approved lesson and submitted written work. The teacher reviewed the submission and marked it complete; the student then saw the feedback in the browser.

API tests also exercised genuine generated PDF upload, byte-for-byte authorized download, private draft handling, revision/resubmission and rejection of changes after a teacher marks work complete.

### Arena and AI-disabled behavior

With AI disabled, a student completed all five MCQs in the seeded teacher-authored quiz, received server-checked feedback, saved the attempt and saw **5 / 5** in personal practice history. The 390px mobile test opened navigation, entered Arena, flipped a flashcard, wrote short-answer practice and revealed its source-backed sample explanation without horizontal overflow on that page.

Teacher attendance, notes, assignments, analytics, notifications and studio pages remained accessible. Studio generation was visibly unavailable and disabled. Study Buddy explained that no provider was connected and disabled the ask button. Request listeners observed **no quiz-generation or tutor calls** in those disabled-mode checks. No page errors were observed by listeners in the added teacher-page and full-quiz tests.

## Authorization and negative-test matrix

| Scenario | Verified behavior | Limits |
| --- | --- | --- |
| Anonymous PDF request | **401** | Tested through FastAPI TestClient, not a public CDN |
| Student downloads a draft PDF | **404** | A real stored PDF existed |
| Other-school administrator downloads approved PDF | **404** | Tested before and after publication |
| Unenrolled same-school student downloads approved PDF | **403**; material omitted from their list | Intentional denial; record existence is distinguishable by status |
| Direct guessed `/uploads/...` URL | **404** | Local storage is not statically mounted |
| Foreign-school teacher/student list school A classes/materials/homework/quizzes | Empty lists | Added accounts belonged to synthetic School B |
| Foreign-school attendance/detail/material/homework/tutor access | **404** on tested role-permitted handlers | Not exhaustive for every endpoint/HTTP verb |
| Foreign-school account/member IDs in class creation | **404** | Existing test coverage |
| Student lists another student's submissions or reviews work | **403** | Teacher-only routes deny the action |
| Student injects peer `student_id` into submission JSON | Ignored; one row saved for authenticated student | Extra fields are ignored by current Pydantic input model |
| Repeated homework submit | Both accepted before completion, **one row updated**, latest answer retained | Intended overwrite behavior, not rejection/idempotent notification behavior; concurrent posts untested |
| Submit after teacher completion | **409** | Sequential test |
| Peer accesses student's notification | Absent from peer list; mark-read request **404** | Own notice remained scoped |
| Student quiz answers before attempt | Answer key absent from ordinary quiz-detail payload | Practice/check endpoints intentionally reveal feedback; not an exam system |
| Repeated same-day quiz attempt | **409** | Existing backend test; concurrent/different-quiz daily races untested |
| Missing CSRF / disallowed Origin | **403** | Explicit Origin mismatch tested; missing Origin remains allowed if session/CSRF are valid |
| Expired or logged-out session | **401** | Token replay after logout rejected |
| Change password | Incorrect old password **400**; correct change revoked second session | Other student's session still worked |
| Production cookie mode | `Secure`, `HttpOnly`, `SameSite=Lax` present | Tested in an HTTPS TestClient origin; no real TLS deployment tested |
| AI disabled even with dummy credentials | Status not configured, generation **503**, provider not reached | No live credentials were used |
| Malformed JSON/response envelope/invalid answer keys/duplicates/unsupported quotes | Tested cases rejected or returned **502**, with safe failure metadata | Does not imply every malformed provider shape is handled; see F-02 |
| Simulated provider read timeout | **502**, recorded `ReadTimeout` | Stubbed exception, not a real upstream timeout measurement |

## Confirmed defects and design limitations

Priority is for follow-up, not a claim that changes were authorized in this audit. **P0:** core blocker or demonstrated critical exposure; **P1:** required before real-student/AI/multi-school release; **P2:** next hardening/correctness work; **P3:** maintenance.

| ID | Priority | Finding and exact evidence | Location / recommended action |
| --- | --- | --- | --- |
| F-01 | P2 | Creating `{"name":"  ","grade":3}` returned **201** and stored an empty class name. Length validation runs before `.strip()`. | `backend/app/routes.py:93`, `schemas.py:29`; validate normalized, nonblank inputs before persistence. Left unchanged. |
| F-02 | P2; before enabling AI | A stubbed structurally valid tutor response with `"usage": null` returned **500** and left `AIEvent.status='pending'`. `usage.get(...)` raises uncaught `AttributeError`. | `backend/app/ai.py:72`; validate the provider envelope/usage and mark every completed failure terminal. Left unchanged because AI-disabled core flows are unaffected. |
| F-03 | P2 | A synthetic request with nonnumeric `Content-Length` returned **500** due to unguarded integer conversion. | `backend/app/main.py:26`; reject malformed length as a client error and enforce actual streamed-body limits. Proxy acceptance of malformed lengths was not tested. |
| F-04 | P2 | Two sequential homework posts retained one submission but created **two teacher notifications**. Repeated clicks/retries therefore duplicate alerts. | `backend/app/learning.py:121`; define notification/resubmission semantics or idempotency. No claim of duplicate submission rows. |
| F-05 | P1 before child-facing AI | A factually contradictory tutor answer passed `validate_grounding` when it included a genuine source sentence. This is a deterministic-validator probe, **not a live-model hallucination result**. | `backend/app/ai.py:37`; add semantic factuality/entailment, abstention and age/safety evaluation before enabling tutoring. Quotation containment alone cannot establish correctness. |
| F-06 | P1 before broader multi-school operation | The migrated SQLite schema accepted a School B **student** enrolled into a School A class by a direct DB write, with `PRAGMA foreign_keys=1`. FK existence checks do not enforce matching school IDs or member roles. Normal class-creation APIs rejected foreign-school IDs in tests. | `backend/app/models.py`, migration `0001`; add defense in depth through reviewed tenant constraints/RLS/import validation. This is not evidence of an API authorization bypass. |
| F-07 | P2 | `LearningPack` requires at least five MCQs but no short-answer item, despite the generation prompt requesting one. Existing stub-pack tests demonstrate that MCQ-only packs validate. Summaries/flashcards have length checks but no evidence/semantic validation. | `backend/app/schemas.py:86`, `ai.py`; define and evaluate the complete pack contract. Teacher review currently carries the quality burden. |
| F-08 | P2 | The browser assignment test fixes the due date to **2026-12-20**; it will become invalid as a future date after that day. A full class-quiz browser test also needs a fresh database because attempts are limited per day. | `frontend/tests/school.spec.ts:142`, `tests/audit.spec.ts`; use relative dates and isolated seed fixtures in a later test-harness improvement. |

None of these findings was silently fixed or represented as passing intended behavior. Disposable probes are recorded in `.audit/findings.json`. **No P0 issue was observed within the tested scope; this is not proof that no P0 exists.**

## Security and real-student data readiness

**Verified safeguards:** Argon2 password hashes; random opaque session tokens stored as hashes; server-side role/class/school policy; CSRF on authenticated writes; production secure-cookie flag; student-scoped submissions/attendance/attempts; authenticated PDF downloads with random object names; API `Cache-Control: no-store` on tested downloads; React text rendering rather than injected AI HTML; public-only offline cache; no automatic AI calls in disabled mode. The inspected tutor request does not add profile emails/account metadata or conversation history. Tests confirmed Hindi request selection and absence of the synthetic student's email in the captured provider payload.

**Real student data should not yet be introduced.** The following are release risks or unverified operational controls:

- **P1 — PostgreSQL and storage verification:** Docker's daemon is unavailable. Actual PostgreSQL locks/full-text ranking, PostgreSQL migrations, S3 authorization/encryption/region settings and backup restoration were not exercised. Local SQLite/local-file success does not certify those paths.
- **P1 — PDF processing:** signature/type/size/page/text limits work in the tested cases, but there is no malware quarantine or isolated parser. Parsing is synchronous inside an async route; extracted-text length is checked after extraction. A compressed/complex hostile PDF could consume excessive resources. No hostile-load exploit was executed.
- **P1 — deployment defaults and secrets:** configuration defaults to development, SQLite and local files; there is no production startup validation requiring HTTPS, approved storage or encryption. Configuration files are ignored, examples contain no live keys, and a narrow key-pattern scan found no matches in app/source/docs. This was not a comprehensive historical secret scan.
- **P1 — privacy operations:** consent/authorization records, retention automation, deletion/export tooling, expired-session cleanup, incident ownership and verified backups are not implemented as tested operational systems. Existing documents describe manual procedures. Chat text can still contain personal information, and enabling AI sends the supplied question/source to the configured provider; no PII filter or provider-retention guarantee is enforced by the code.
- **P1 — limiter topology:** request limiting is per-process and keyed by direct client IP. A Next.js proxy can pool school users into one apparent IP; replicas multiply allowances. The 15-login/minute and 300-request/minute behavior was inspected, not load-tested. AI request counts use user-row locking on PostgreSQL, not a global monetary budget. No provider spend cap was configured or tested.
- **P2 — data integrity and concurrency:** simultaneous attendance, homework-submit/review and different-quiz daily-attempt races remain unverified. Unique row constraints are present, but homework has no optimistic version check; stale writes/reviews may conflict under concurrency.
- **P2 — bounded reporting and UI:** attendance history is limited to 1,000 rows; dashboard homework is the first six by due date, including old assignments. Several lists are unpaginated. A student enrolled in multiple classes gets one unspecific first attendance status on the overview. These are inspected design limitations, not tested full-year behavior.
- **P2 — browser hardening:** security headers exist, but a full CSP/HSTS/TLS/host-policy review, accessibility audit, low-end Android test, cross-browser run and slower-network/load test were not performed. Development docs/OpenAPI remain configured by defaults; production ingress policy needs separate review.

There is no assertion here of legal compliance, production security or the safety of an actual school deployment.

## AI evaluation review

**Present:** a versioned system prompt (`nexora-v1`); Pydantic contracts; answer-option validation; exact-text duplicate checks; normalized source-quotation containment; failure/latency/cost metadata; private editable draft packs and teacher publication; six synthetic JSONL evaluation cases; and a proposed human 0/1/2 rubric. Cases include English/Hindi, insufficient context, prompt injection, a young learner and uncertainty. All six are explicitly **synthetic-unreviewed**.

**Missing measurements and execution infrastructure:**

| Dimension | Current evidence | Measurement needed before claims of AI quality |
| --- | --- | --- |
| Factuality / groundedness | Structural/citation tests only; F-05 demonstrates a false acceptance | Teacher-labelled entailment/factual-error rates, unsupported-claim rate, confidence/abstention precision and recall |
| Retrieval quality | Selected-chapter lexical/FTS implementation inspected; PostgreSQL branch not run | Recall@k/MRR on labelled evidence, answerability coverage, cross-language retrieval and source-truncation coverage |
| Pack completeness and novelty | Exact duplicates/options checked; MCQ-only packs accepted | Short-answer/card/summary coverage, semantic near-duplicate rate, ambiguity and answer-key validity |
| Grade and language suitability | Grade/language fields sent; one mocked Hindi interaction | Teacher assessment across Classes 1–10, subjects and both languages; Hindi fluency and age/readability scoring |
| Child safety / prompt injection | Prompt instructions and one unexecuted dataset case | Adversarial refusal/leakage tests, personal-data solicitation checks, unsafe-content outcomes and human review |
| Learning usefulness | Follow-up text is required, not assessed | Appropriate follow-up and scaffolding scores; authorized learner-comprehension measurement, not an inference from generated prose |
| Reliability and costs | Events record latency/estimated cost; F-02 can leave pending events | Success/failure rates by model/prompt, p50/p95 latency, token/cost accuracy, timeout/truncation and malformed-envelope rates |
| Reproducibility / regressions | Model/prompt labels saved | Executable evaluation runner, versioned labelled dataset, persisted results/diffs, reviewer/date, regression thresholds and CI gate |

The JSONL cases are not wired into an automated quality run. No teacher review, live English/Hindi output quality, real model latency, inference-cost accuracy, prompt-injection success rate or learner outcome was measured in this audit. No paid calls were made to obtain those measurements.

## Dependency review

`npm audit` and `pip-audit` found **zero known advisories**, not zero possible defects or malicious packages. Scans used the online registry/PyPI advisory services and sent package names/versions, not school records or project source. Scope and limitations follow the [npm audit documentation](https://docs.npmjs.com/auditing-package-dependencies-for-security-vulnerabilities/) and [PyPA pip-audit documentation](https://github.com/pypa/pip-audit).

Python locked entries matched installed versions. The lock has version pins but no artifact hashes. The Docker image uses an unpinned base-image digest, and production requirements also include test/dev utilities. `npm ls --depth=0` reported two extraneous optional native/WASM packages (`@emnapi/runtime`, `@img/sharp-wasm32`), both also represented in the lock; a clean CI `npm ci` would be stronger reproducibility evidence than this existing install. Container OS vulnerabilities, package signatures/provenance and all future advisory updates were outside the scan. No dependency upgrades or `audit fix` commands were run.

The backend suite emits a Starlette warning that its httpx TestClient path is deprecated. It does not fail current tests; address it in a separately tested dependency/tooling update.

## Prioritized follow-up

1. **Before real-student pilots:** establish the privacy/retention/deletion/support process; verify HTTPS and secure configuration, private storage, backup restore, database tenant defenses, upload isolation and realistic deployment rate limiting. Run the actual PostgreSQL/S3 paths in an authorized private environment.
2. **Before enabling any model:** repair provider-envelope/error-event handling (F-02); create teacher-reviewed factuality/safety/retrieval evaluations and an executable regression gate; configure an approved provider, its data policy and spending limits only after explicit approval. Keep `AI_ENABLED=false` meanwhile.
3. **Next correctness work:** reject blank normalized inputs (F-01), handle malformed request lengths (F-03), define repeated-submission alert behavior (F-04), enforce intended learning-pack completeness (F-07), and replace date-sensitive/shared-state test fixtures (F-08).
4. **Before scaling:** measure concurrent updates, proxy/replica limits, pagination/report completeness, performance, mobile accessibility and cross-browser behavior. Prefer evidence-driven changes over refactoring the architecture now.

## Reproduction

From the repository, with the existing application virtualenv/dependencies installed:

```powershell
# API suite: synthetic in-memory databases, no production resources
Set-Location backend
$env:AI_ENABLED = 'false'
..\.venv\Scripts\python.exe -m pytest -q
..\.venv\Scripts\python.exe -m pip check

# Disposable migration/browser DB; choose a NEW unused local filename each full run.
$env:DATABASE_URL = 'sqlite:///C:/path/to/Nexora/.audit/your-new-audit.db'
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m alembic current
..\.venv\Scripts\python.exe -m alembic check
..\.venv\Scripts\python.exe -m app.seed
$env:FRONTEND_ORIGIN = 'http://localhost:3001'
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8001
```

In separate frontend terminals:

```powershell
Set-Location frontend
$env:API_INTERNAL_URL = 'http://127.0.0.1:8001'
npm.cmd run typecheck
npm.cmd run build
npm.cmd run start -- --port 3001

# Run from another frontend terminal after both services are ready.
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD/../.playwright"
npx.cmd playwright test --config playwright.audit.config.ts
npm.cmd audit --json --cache ../.npm-cache
```

Create the `.audit` directory before using its paths. Do not reuse an actual school database. The downgrade check was performed only on the separate disposable migration DB, before browser seeding; **never run a downgrade on a school database as an audit check**. After isolated browser verification, restore the normal frontend build with `API_INTERNAL_URL=http://127.0.0.1:8000` rather than leaving its rewrite pointed at an audit-only API.

For the Python advisory scan, an isolated tool virtualenv was used so application dependencies were not changed:

```powershell
# Run from repository root; these public package/advisory operations are free.
python -m venv .audit/tools
.\.audit\tools\Scripts\python.exe -m pip install --no-cache-dir pip-audit
.\.audit\tools\Scripts\python.exe -m pip_audit --no-deps --disable-pip -r backend/requirements.lock.txt --cache-dir .audit/pip-audit-cache --format json
```
