# Render Deployment Guide

This repository is configured to run on Render with all production credentials supplied via Render Environment Variables.

## Required Environment Variables

Configure these values in the Render dashboard for the backend service:

- `DATABASE_URL`
- `REDIS_URL`
- `JWT_SECRET`
- `JWT_REFRESH_SECRET`
- `GROQ_API_KEY`
- `SUPABASE_URL` (optional)
- `SUPABASE_ANON_KEY` (optional)
- `SUPABASE_SERVICE_ROLE_KEY` (optional)
- `ENVIRONMENT=production`
- `DEBUG=false`

## Backend Service Setup

1. Create a new Web Service in Render.
2. Connect your GitHub repository.
3. Use Python 3.12 for the backend service.
4. Set the build command to:

```bash
pip install -r requirements.txt
```

5. Set the start command to:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

6. Make sure `env_file` is not used in production. All secrets must come from Render Environment Variables.

## Frontend Service Setup (Optional)

If you deploy the frontend separately as a static site or web service:

- Use Node 20 or later.
- Set the build command to:

```bash
npm ci
npm run build
```

- Set the publish directory to `frontend/dist`.
- Set `VITE_API_URL` in Render environment variables to your backend endpoint.

## Secure Configuration Notes

- `GROQ_API_KEY` is loaded directly from environment variables in `backend/app/config.py`.
- The app uses Pydantic settings and fails fast when required secrets are missing.
- `JWT_SECRET` and `JWT_REFRESH_SECRET` are required for authentication.
- `ENVIRONMENT` should be `production` in Render, so secure cookies and middleware behave correctly.

## Verification

- Confirm backend starts successfully with `uvicorn`.
- Confirm `/health` returns a healthy response.
- Confirm `GROQ_API_KEY` is not stored in repository files.
- Confirm `.env.example` contains no real secrets.
