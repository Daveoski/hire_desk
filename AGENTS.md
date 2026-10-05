# HireDesk — Base44 dev environment notes

## Running here

- `docker compose -f docker-compose.base44.yml up -d --build` starts everything:
  `db` (postgres:16), `migrate` (one-shot `alembic upgrade head`), `backend`
  (uvicorn --reload on :8000), `frontend` (next dev on :3000).
- The repo is bind-mounted into the app services; edits hot-reload. Dependency
  changes (requirements.txt / package-lock.json) need a rebuild / re-install.

## Non-obvious quirks

- The root `pyproject.toml` + `uv.lock` + `src/hiredesk_official/` + root `main.py`
  exist only for Vercel's root service. Local dev runs the backend directly from
  `backend/` (`uvicorn app.main:app`), NOT via uv — `backend/requirements.txt`
  is the authoritative dep list for this environment.
- `backend/app/core/config.py` points its `.env` file at `backend/.env`, but real
  env vars take precedence; secrets arrive via `/run/base44/app.env` (compose
  `env_file`). `DATABASE_URL` and `CORS_ORIGINS` are set inline in compose.
- Alembic must run from the `backend/` directory (`alembic.ini` there,
  `prepend_sys_path = .`). The initial migration needs the `btree_gist` Postgres
  extension — it creates it itself.
- Auth is a Bearer token kept in a zustand store (localStorage), NOT cookies.
  The frontend calls the API cross-origin (`NEXT_PUBLIC_API_URL`, public port
  8000), so `CORS_ORIGINS` on the backend must include the preview origin
  (`https://3000-$BASE44_PUBLIC_HOST_SUFFIX`).
- Next.js gates dev assets/HMR by origin: `next.config.ts` adds
  `allowedDevOrigins` from `BASE44_PUBLIC_HOST_SUFFIX`. Keep both env vars in
  compose when the sandbox host changes.
- Frontend deps: `npm ci` runs only when `node_modules/.package-lock.json` is
  missing or older than `package-lock.json` (bind-mounted repo dir).

## Pipeline behaviour (interviews, notifications, screening)

- Interview events (scheduled / cancelled / completed-by-scorecard) email the
  interviewer plus the job's hiring manager and every company admin
  (`app/interviews/notifications.py`, sent with Resend background tasks).
- Google Calendar sync is optional: needs `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
  and `GOOGLE_REDIRECT_URI` (set in compose from `BASE44_PUBLIC_HOST_SUFFIX`).
  A user connects via `/calendar/google/authorize` -> Google -> `/calendar/google/callback`
  (state is a short-lived JWT). Scheduled interviews are pushed to the scheduler's
  calendar with the interviewer as attendee; cancelling deletes the event. All
  sync failures are logged, never raised.
- Screening (stage moves into or out of `screen`, incl. rejecting at `screen`)
  is restricted to the job's hiring manager; a company admin may screen only a
  job that has no hiring manager (`ensure_screener` in `candidates/service.py`).
- Migrations are hand-written in `backend/alembic/versions/` (0001, 0002...).

## Verifying

- `curl http://localhost:8000/health` → `{"status":"ok"}` (also proves DB).
- `curl http://localhost:3000/` → the landing page HTML.
- Backend logs: `docker compose -f docker-compose.base44.yml logs backend`.
