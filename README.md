# Elevate Solicitation Finder

An internal application for Elevate Project Solutions that helps discover, review, and qualify government contracting opportunities.

## Project Goals

The application will eventually:
- Discover public sector solicitations
- Identify deadlines, mandatory site visits, and pre-bid meetings
- Analyze solicitation documents and summarize project scopes
- Match opportunities with contractors in Elevate's CRM
- Display relevant oppotunities in a searchable dashboard

The application is currently under development.

## Tech Stack

Backend = Python, FastAPI
Frontend = React, TypeScript, Vite
Database = PostgreSQL 17
Local database environment = Docker Compose
Backend testing = pytest
Frontend testing = Vitest
Code quality = Ruff, ESLing, Prettier

## Prereqs

Install the following software:
- Python 3.13
- Node.js and npm
- Docker Desktop
- Git
- Visual Studio Code (recommended, or some other code editor)

Verify your installations:

```bash
python3 --version
node --version
npm --version
docker --version
docker compose version
git --version
```

## Initial Setup

Clone the repo and enter the project directory:

```bash
git clone <YOUR_REPO_URL>
cd elevate-solicitation-finder
```

Replace `<YOUR_REPO_URL>` with the actual GitHub clone URL.

### 1. Configure environment variables

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

If the root `.env.example` does not exist yet, create `.env` manually.

Generate a local database password:

```bash
openssl rand -hex 24
```

Add the generated password to the root `.env`:

```dotenv
POSTGRES_PASSWORD=YOUR_GENERATED_PASSWORD
```
Create the backend environment file:

```bash
cp backend/.env.example backend/.env
```

Set its `DATABASE_URL` using the same password:

```dotenv
DATABASE_URL=postgresql://elevate:YOUR_GENERATED_PASSWORD@localhost:5432/elevate_dev
```

Create the frontend environment file:

```bash
cp frontend/.env.example frontend/.env
```

Ensure it contains:
```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8000
```

NEVER commit real `.env` files or secrets to Git.

### 2. Install backend dependencies

From the project root:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
cd ..
```

### 3. Install frontend dependencies

From the project root:

```bash
cd frontend
npm install
cd ..
```

### 4. Start PostgreSQL

Make sure Docker Desktop is running

From the project root:

```bash
docker compose up -d
docker compose ps
```

Wait until the database service reports a healthy status

## Daily Development Startup

Run the following services in separate Terminal windows

### Terminal 1: PostgreSQL

From the project root:

```bash
docker compose up -d
```

### Terminal 2: FastAPI

```bash
cd backend
source .venv/bin/activate
python3 -m uvicorn app.main:app --reload
```

Backend address:

http://127.0.0.1:8000

Health endpoint:

http://127.0.0.1:8000/health

Interactive API documentation:

http://127.0.0.1:8000/docs

### Terminal 3: React

```bash
cd frontend
npm run dev
```

Frontend address:

http://localhost:5173

The frontend should display the backend connection status

## Running Tests

### Backend

From `backend/` , with the virtual environment activated:

```bash
python3 -m pytest
python3 -m ruff check .
python3 -m ruff format --check .
```

Automatically fix supported linting and formatting issues:

```bash
python3 -m ruff check . --fix
python3 -m ruff format .
```

### Frontend

From `frontend/`:

```bash
npm run lint
npm run format:check
npm run test
npm run build
```

## Stopping the App

Stop FastAPI and React using `Control + C` in their retrospective Terminal windows.

Stop PostgreSQL from the project root:

```bash
docker compose stop
```

To remove the PostgreSQL container while preserving its data:

```bash
docker compose down
```

DO NOT USE `docker compose down -v` unless you intend to delete the local database volume and its data!!

## Troubleshooting

### React cannot connect to FastAPI

1. Confirm FastAPI is running
2. Open http://127.0.0.1:8000/health directly
3. Check `frontend/.env` for the correct API address
4. Restart Vite after changing environment variables
5. Check FastAPI's CORS configuration
6. Open the browser developer console for error details

### Python cannot find the app module

Run backend commands from the `backend/` directory, not `backend/app` or the repo root.

### Docker cannot connect to the engine

Open Docker Desktop and wait for it to finish starting

### Port already in use

Check whether another app is using port 8000, 5173, or 5432.

### Python virtual environment is not active

From `backend/`:

```bash
source .venv/bin/activate
```

## Security Notes

- Do NOT commit `.env` files
- Do NOT place private credentials in `VITE_` variables.
- Store production secrets in the hosting provider's environment settings.
- Keep local development credentials separate from production credentials

## Project Status

Phase 1: Initial development setup [COMPLETE]

Other phases:
Phase 2: Database Design
Phase 3: ESBD Collector
Phase 4: Document Collection
Phase 5: Document Analysis
Phase 6: Qualification Engine
Phase 7: Google Sheets CRM Integration
Phase 8: React Dashboard
Phase 9: Multi User Access
Phase 10: Automation and Monitoring
Phase 11: Cloud Development
Phase 12: Email and Additional Portals
Phase 13: Long Term Improvements