# IdeaToProd — Implementation Roadmap

## Vision

IdeaToProd is a full-stack platform that accepts a software idea, runs a staged generation workflow, produces design artifacts and code artifacts, verifies them with tests, and later can deploy the generated project.

Initial implementation target:
- Frontend: React + Vite + TypeScript
- Backend: FastAPI
- Database: MongoDB
- Local development: VS Code
- First workflow mode: mocked orchestration
- Later workflow mode: real agent-based orchestration

---

## Product goals

### Primary goals
- Let a user create a project from an idea
- Let a user start a generation run
- Show workflow progress clearly
- Store artifacts per run
- Generate local output files per run
- Run real tests on generated output
- Prepare architecture for future LLM + MCP integrations

### Non-goals for MVP
- Full auth/teams/billing
- Production-grade deployment engine
- Real Jira/GitHub/Google Drive integrations in the first milestone
- Complex multi-user permissions

---

## Technical architecture

### Frontend
- React
- Vite
- TypeScript
- React Router
- Tailwind
- Small API client layer

### Backend
- FastAPI
- Pydantic
- Service-oriented architecture
- Repository abstraction
- Async MongoDB integration

### Data
- MongoDB
- Collections planned:
  - projects
  - workflow_runs
  - artifacts
  - execution_events
  - generated_files_metadata

### Workflow
- Start with mocked orchestration
- Later replace with real multi-agent workflow
- Future target:
  - HL design agent
  - detailed design agent
  - code generation agent
  - test generation agent
  - test execution agent
  - optional deploy agent

---

## Development phases

### Phase 1 — Full-stack bootstrap
Goal:
- Create React + FastAPI monorepo
- Verify frontend can call backend health endpoint

Success criteria:
- Backend `/health` works
- Frontend shows backend connection status

### Phase 2 — Projects domain
Goal:
- Add project creation, list, and detail pages
- Add backend project endpoints

Success criteria:
- Can create a project from UI
- Can list and view projects

### Phase 3 — MongoDB integration
Goal:
- Persist projects in MongoDB

Success criteria:
- Projects survive backend restart

### Phase 4 — Workflow runs
Goal:
- Add workflow run model and mocked orchestration stages

Success criteria:
- Can start a run
- Run moves through mocked stages automatically

### Phase 5 — Artifacts
Goal:
- Add artifact model and artifact viewer in UI

Success criteria:
- Each run creates readable artifacts
- User can inspect them in UI

### Phase 6 — Service boundaries
Goal:
- Refactor mocked workflow into structured services

Success criteria:
- Separate services exist for each stage
- Orchestrator still works end-to-end

### Phase 7 — Real-time updates
Goal:
- Add WebSocket progress updates

Success criteria:
- Run page updates in real time

### Phase 8 — Generated output files
Goal:
- Create real local output files for each run

Success criteria:
- Generated files exist on disk
- UI can browse and view them

### Phase 9 — Real test execution
Goal:
- Execute pytest against generated output

Success criteria:
- Platform runs tests
- UI shows pass/fail and logs

### Phase 10 — Real design generation
Goal:
- Replace mocked design artifacts with LLM-generated outputs

### Phase 11 — GitHub integration
Goal:
- Create repository and push generated output

### Phase 12 — Template-based code generation
Goal:
- Add app templates and structured generation strategy

### Phase 13 — Separate test generation model
Goal:
- Generate tests with a different model/provider than code generation

### Phase 14 — Repair loop
Goal:
- On failed tests, route to repair step and re-run

### Phase 15 — Deployment
Goal:
- Deploy generated apps to a selected target platform

---

## Core data models

### Project
Fields:
- id
- name
- idea
- status
- created_at
- updated_at

### WorkflowRun
Fields:
- id
- project_id
- status
- current_step
- steps
- created_at
- updated_at

### Artifact
Fields:
- id
- project_id
- run_id
- artifact_type
- title
- content
- created_at

### GeneratedFileMetadata
Fields:
- id
- project_id
- run_id
- relative_path
- file_type
- size
- created_at

### ExecutionEvent
Fields:
- id
- run_id
- event_type
- step_name
- payload
- created_at

---

## Backend architecture rules

1. Keep API schemas separate from DB models
2. Use repository abstractions for data access
3. Keep workflow orchestration separate from API routes
4. Keep stage services separate from orchestrator
5. Store generated files under a run-scoped workspace
6. Add logging for every workflow stage transition
7. Keep code ready for future MCP and model integrations

---

## Frontend architecture rules

1. Separate pages, components, api client, and types
2. Avoid large all-in-one components
3. Mirror backend DTOs in frontend types
4. Keep loading and error states explicit
5. Add route structure early
6. Build UI around project → run → artifacts/files/test results

---

## Testing strategy by phase

### Backend
- Start with endpoint smoke tests
- Add service tests as services appear
- Add repository tests after Mongo integration
- Add workflow tests for mocked orchestration
- Add local execution tests for generated files/test runner

### Frontend
- Manual testing first
- Add component tests later if needed
- Prioritize end-to-end manual verification in MVP

---

## Local development workflow

For each phase:
1. Create a Git branch
2. Ask Codex for only that phase
3. Run backend
4. Run frontend
5. Execute phase checklist
6. Fix issues before continuing
7. Commit
8. Move to next phase

Suggested branch naming:
- `phase-01-bootstrap`
- `phase-02-projects`
- `phase-03-mongodb`
- `phase-04-runs`
- `phase-05-artifacts`
- `phase-06-services`
- `phase-07-realtime`
- `phase-08-generated-files`
- `phase-09-test-runner`

---

## Definition of done for MVP

The MVP is done when:
- A user can create a project from an idea
- A user can start a generation workflow
- The UI shows workflow progress
- The system creates artifacts
- The system creates real local output files
- The system runs real tests against the generated output
- The UI shows test results and logs

---

## Future integrations

Planned future integrations:
- OpenAI / Anthropic / Gemini
- GitHub
- Jira
- Google Drive
- Playwright
- Deployment provider

These integrations should be added through clean service adapters, not directly inside API routes.