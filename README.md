# Nexora AI

**Less Admin. More Teaching. Better Learning.**

A school productivity MVP for Classes 1–10. Built as a Next.js/TypeScript frontend and a Python/FastAPI modular monolith, with SQLAlchemy, Alembic, PostgreSQL, private PDF storage and a configurable AI provider. Local setup also supports SQLite so you can try the full core workflow without provisioning services.

This is working pilot software, **not a claim of production readiness**. Demo names and records are synthetic. Nothing has been deployed publicly, and setup makes no paid AI requests.

## What works

- Administrator creates school-issued accounts, creates classes with teachers/students, publishes announcements and reads audit activity.
- Teacher marks attendance with all students initially present, reviews before saving, corrects with a reason and exports history. Unique database records and stale-version checks prevent accidental overwrite.
- Student sees only their own attendance and submissions. Teachers see only assigned classes; administrators stay inside their school.
- Teachers upload readable PDFs or write lessons, review drafts and approve them. Downloads pass through authenticated authorization checks. Approved lessons notify students.
- Teachers create homework; students submit written answers; teachers request revision or mark complete with feedback. Upcoming deadlines and review events appear in notifications.
- AI learning studio generates structured chapter-grounded MCQs, short answers, flashcards and summaries; teachers edit and approve a stored pack before publishing.
- Study Buddy retrieves from an approved chapter, explains in English/Hindi and quotes supporting evidence. Conversations are not persisted by Nexora.
- Arena has a five-question daily challenge, class quizzes, instant server-checked feedback, personal completion history and participation/improvement badges. No public individual rankings or punitive streaks.
- Teacher analytics show attendance trends, assignment completion and aggregate practice accuracy by topic.

AI requires school-approved provider credentials. Without them, the application clearly says AI is unavailable; teacher-authored demo quizzes and ordinary school workflows work normally.

**Free local mode is the default.** `AI_ENABLED=false` prevents provider calls even if credentials are supplied. Keep it disabled until you explicitly approve a provider and any costs. No hosting, paid storage, messaging or AI subscription is required for the local demo.

## Run locally on Windows

Prerequisites: Python 3.10+ (3.12 recommended), Node 22+, npm. In PowerShell use `npm.cmd` if execution policy blocks `npm.ps1`.

From this folder:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --no-cache-dir -r backend/requirements.lock.txt
Copy-Item backend/.env.example backend/.env
Copy-Item frontend/.env.example frontend/.env.local
Set-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe -m app.seed
Set-Location ../frontend
npm.cmd ci --cache ../.npm-cache
```

Start the API in one terminal:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Start the frontend in another terminal:

```powershell
Set-Location frontend
npm.cmd run dev
```

Open **http://localhost:3000**. Use localhost consistently: cookies and the origin check depend on the frontend origin. Alternatively set `FRONTEND_ORIGIN=http://127.0.0.1:3000` in `backend/.env` and use that URL. The Next server proxies `/api` to FastAPI, so there are no cross-site cookies or browser-visible API secrets.

After setup, `powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1` starts both services and stops the API when the frontend exits.

| Role | Demo email | Password |
| --- | --- | --- |
| Administrator | admin@nexora.demo | NexoraDemo!2026 |
| Teacher | teacher@nexora.demo | NexoraDemo!2026 |
| Student | student@nexora.demo | NexoraDemo!2026 |

The seeded class is **Class 6 · A** with one teacher, six synthetic students, approved science notes, homework, historical attendance and a teacher-authored quiz. Seeding never runs automatically and refuses to run in production.

## Try the first vertical slice

1. Sign in as admin. Open **School & people → Create class**. Select a teacher and at least one student.
2. Sign in as teacher in a separate browser profile. Open **Attendance**, choose that class/date, tap any absences, then **Review & save → Confirm & save attendance**.
3. Sign in as student. Open **Attendance**, choose that class and see the student's own saved status. Other students' records and the roster are not available.
4. Try **Study materials → Add study material**, save a draft and approve it. Create an assignment, submit as student, then review as teacher.

## Repository

```text
frontend/src/app/       landing, login and role-aware workspace routes
frontend/src/components/  accessible Radix dialogs and shared workspace
frontend/tests/        Playwright browser workflows
backend/app/           auth, access policy, school, learning, AI and Arena modules
backend/migrations/    frozen Alembic schema migrations
backend/tests/         API, isolation and AI contract tests
backend/evals/         synthetic AI evaluation cases and review rubric
docs/                  architecture, privacy, deployment and verification notes
scripts/               local startup
```

## Verify

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m pytest -q
..\.venv\Scripts\python.exe -m alembic check
Set-Location ../frontend
npm.cmd run typecheck
npm.cmd run build
$env:PLAYWRIGHT_BROWSERS_PATH = "$PWD/../.playwright"
npx.cmd playwright install chromium
npm.cmd run test:e2e
```

Browser tests expect both services running and demo data seeded. They create synthetic classes/lessons/homework in the demo database; run against a disposable demo environment. Never point them at a school pilot database.

Health: `/api/health`. Interactive API documentation in development: http://127.0.0.1:8000/api/docs.

See [architecture](docs/architecture.md), [AI evaluation](backend/evals/README.md), [deployment](docs/deployment.md), [privacy and pilot readiness](docs/privacy-and-pilot.md), and [verification](docs/verification.md).
