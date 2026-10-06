# HireDesk

Applicant tracking for small companies. FastAPI + PostgreSQL backend (`backend/`), Next.js frontend (`frontend/`).

## Local development

See `AGENTS.md` for the Docker dev environment used here.

## Deployment (Vercel)

One Vercel project serves both halves, wired by the root `vercel.json`:

- `frontend` (Next.js) answers every request except `/api/*`.
- `backend` (FastAPI, `backend/app/main.py`) answers `/api/*`, with the `/api` prefix stripped before the request reaches FastAPI — its routes are `/jobs`, `/interviews`, … with no prefix.

To deploy:

1. Import this GitHub repository into Vercel (production branch `main`).
2. Set the environment variables below.
3. Run the migrations once against the production database — the build does not do it:
   `cd backend && DATABASE_URL=postgresql+psycopg://... alembic upgrade head`

| Variable | Service | Notes |
| --- | --- | --- |
| `DATABASE_URL` | backend | Hosted PostgreSQL, `postgresql+psycopg://…`. Required. |
| `JWT_SECRET` | backend | Required, 32+ characters. |
| `CLOUDINARY_CLOUD_NAME`, `CLOUDINARY_API_KEY`, `CLOUDINARY_API_SECRET` | backend | Required by the public application form (CV upload); it answers 503 without them. |
| `CORS_ORIGINS` | backend | Comma-separated origins. Not needed for the single-project setup, where the API is same-origin. |
| `RESEND_API_KEY`, `EMAIL_FROM` | backend | Optional: without a key interview emails are skipped. |
| `NEXT_PUBLIC_API_URL` | frontend | `/api` for this single-project setup. |

Notes:

- Migration `0001` creates the `btree_gist` extension, so the database user must be allowed to create extensions.
- In Resend sandbox mode, email only reaches the account's verified sender until a domain is verified.
