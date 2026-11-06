# Verification record

Verified locally on 6 November 2026 using Windows, Python 3.10.11, Node 22.18.0, Next.js 16.4.5 and Chromium through Playwright. Database: SQLite. All names and learning records were synthetic.

| Check | Result | Evidence |
| --- | --- | --- |
| Backend API/security/AI tests | **10 passed** | `python -m pytest -q`, 6.13 seconds in the final run |
| TypeScript | **Passed** | `npm run typecheck`, no type errors |
| Production frontend build | **Passed** | All 15 routes generated; no build failures |
| Browser workflows | **4 passed** | Playwright, 18.3 seconds in the final run |
| Schema drift | **Passed** | `alembic check`: no new upgrade operations |
| Fresh database migration | **Passed** | Upgrade → downgrade → upgrade → schema check against a disposable SQLite database |
| Desktop/mobile render | **Passed basic inspection** | 1440px desktop and 390px mobile screenshots; no page errors or horizontal overflow in the inspected dashboard |
| Offline privacy | **Passed** | Browser cache limited to public offline page and icon; no API or authenticated-page cache |
| Free-mode guard | **Passed** | AI stays disabled even with credentials and never reaches the mocked provider |
| Local health latency | **Measured, not a load test** | 10 sequential local health requests: median 2.7 ms, maximum 35.1 ms; database connectivity included |

## Browser stories verified

1. An administrator signs in, creates a class with a teacher and two students; the teacher selects it, marks one absence, confirms; the student sees their own present status and no peer's name.
2. A teacher writes draft notes and approves them, creates homework; a student sees the notes and submits written work; the teacher reviews and marks complete; the student sees the feedback.
3. At 390px width, a student opens navigation, enters Arena, chooses an approved pack and flips a flashcard without horizontal overflow. An additional passing run verifies writing a short practice response and revealing its source-backed sample explanation.
4. Offline navigation shows the public offline fallback. Cache inspection confirms student information is not stored for offline use.

Backend tests additionally cover correction reasons/version conflicts, revoked sessions, CSRF, class/tenant authorization, private submission visibility, revision/resubmission, genuine PDF upload/download with randomized storage paths, AI JSON/answer/evidence validation, Hindi request configuration, metadata privacy, usage limits, publication and private server-scored attempts.

## Scope and remaining checks

No public deployment, live model inference, paid hosting, paid storage or messaging service was used. Provider tests are mocked. The live application defaults to `AI_ENABLED=false`.

Docker's daemon is unavailable on this machine. PostgreSQL row locks/full-text behavior and the Docker image remain unverified in an actual PostgreSQL deployment. S3 integration is implemented but has not been tested against a live bucket. The current API limiter is process-local. PDF parsing lacks malware scanning and isolation. These are documented pilot gates rather than production-readiness claims.

The AI dataset is synthetic and not teacher-reviewed. No factual quality, safety pass rate or learning-comprehension result is claimed from mocked tests. Real English/Hindi evaluations and teacher review remain necessary after approval of an appropriate provider.

Basic mobile inspection is not a full accessibility audit or a low-cost Android/slower-network performance assessment. HTTPS/proxy configuration, backup restoration, retention automation, consent, private staging and operational monitoring must be validated before authorized school pilots.

One dependency warning is present: the installed Starlette version deprecates its httpx-backed TestClient path. Tests pass; assess the recommended replacement on a future tested dependency update.

Preview artifacts: [desktop dashboard](screenshots/teacher-desktop.png), [mobile dashboard](screenshots/teacher-mobile.png).
