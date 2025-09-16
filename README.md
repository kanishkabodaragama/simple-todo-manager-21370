# Project Repository

This repository contains a simple Todo application.

## Backend (FastAPI)

- Location: `simple-todo-manager-21370/todo_backend`
- Run locally:
  - Create and configure environment variables using `.env.example`.
  - Install dependencies from `requirements.txt`.
  - Start the app:
    - `python -m src.api` (runs uvicorn with default host/port)
    - Or run via a process manager: `uvicorn src.api.main:app --host 0.0.0.0 --port 8000`
- API Docs (when running): `/docs` (Swagger UI) and `/openapi.json`.

### Endpoints

- `GET /` Health check
- `GET /websocket-usage` WebSocket future usage notes
- `GET /todos` List todos (optional: `completed`, `skip`, `limit`)
- `POST /todos` Create todo (TodoCreate)
- `GET /todos/{id}` Get a todo
- `PUT /todos/{id}` Update a todo (TodoUpdate)
- `DELETE /todos/{id}` Delete a todo
- `DELETE /todos?confirm=true` Bulk delete all todos

### Supabase

- Not used at runtime in this basic implementation.
- See `todo_backend/assets/supabase.md` for integration guidance.