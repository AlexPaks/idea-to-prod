# IdeaToProd - Phase 4

Phase 4 includes:
- `backend`: FastAPI API
- `frontend`: React + Vite + TypeScript app
- `mongodb`: persistent storage for projects
- `.vscode`: optional launch/tasks setup for local development
- mocked workflow orchestration for generation runs

## Project Structure

```text
.
|- backend/
|  |- app/
|  |  |- api/
|  |  |- core/
|  |  |- db/
|  |  |- models/
|  |  |- repositories/
|  |  |- services/
|  |  |- __init__.py
|  |  `- main.py
|  |- .env.example
|  `- requirements.txt
|- frontend/
|  |- src/
|  |  |- App.tsx
|  |  |- App.css
|  |  |- env.d.ts
|  |  `- main.tsx
|  |- .env.example
|  |- index.html
|  |- package.json
|  |- tsconfig.app.json
|  |- tsconfig.json
|  |- tsconfig.node.json
|  `- vite.config.ts
`- .vscode/
   |- launch.json
   |- settings.json
   `- tasks.json
```

## Local Run Steps

1. Start MongoDB (local Docker example)

```powershell
docker run --name ideatoprod-mongo -p 27017:27017 -d mongo:7
```

2. Start backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Backend reads MongoDB settings from environment variables in `backend/.env.example`.

3. Start frontend (in a new terminal)

```powershell
cd frontend
npm install
npm run dev
```

4. Open app
- Frontend: `http://localhost:5173`
- Backend health: `http://localhost:8000/health`

Project API endpoints:
- `POST /api/projects`
- `GET /api/projects`
- `GET /api/projects/{project_id}`

Workflow run API endpoints:
- `POST /api/projects/{project_id}/runs`
- `GET /api/runs/{run_id}`
- `GET /api/projects/{project_id}/runs`

Mock workflow steps:
- `intake`
- `high_level_design`
- `detailed_design`
- `code_generation`
- `test_generation`
- `test_execution`
- `completed`
