# Rythm Phase 1

This repo now uses a small monorepo layout:

- `frontend/`: Vite + React + TypeScript + Tailwind
- `backend/`: FastAPI + SQLAlchemy + MySQL

## Current scope

- local signup, login, logout
- `doctor` and `patient` roles
- protected backend routes
- protected frontend routes
- patient and doctor EHR views
- encounter creation and treatment editing

## Setup

1. Install dependencies:

```bash
npm install
npm run install:backend
```

2. Create env files from the examples:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

3. Update `backend/.env` with your local MySQL credentials and a strong `JWT_SECRET`.

4. Start both apps:

```bash
npm run dev
```

The Python backend creates tables on startup from the SQLAlchemy models. Make sure the
database in `DATABASE_URL` already exists.

## Backend notes

- API base path remains `/api`
- auth uses an `HttpOnly` session cookie
- the frontend contract is unchanged even though the backend is now Python
