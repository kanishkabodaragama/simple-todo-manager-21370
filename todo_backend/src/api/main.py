import os
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import FastAPI, HTTPException, Path, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse

# App-level OpenAPI metadata and tags for better documentation
openapi_tags = [
    {
        "name": "health",
        "description": "Service health and metadata endpoints",
    },
    {
        "name": "todos",
        "description": "CRUD operations for managing todo items",
    },
    {
        "name": "websocket",
        "description": "Real-time interfaces documentation and usage notes",
    },
]

app = FastAPI(
    title="Todo Backend API",
    description=(
        "A simple FastAPI backend that provides REST endpoints for CRUD "
        "operations on todo items. Designed for integration with a Flutter frontend. "
        "Follows a modern, clean style aligned with the project style guide."
    ),
    version="1.0.0",
    openapi_tags=openapi_tags,
)

# CORS configuration - allow all by default; adjust for production using env vars
allowed_origins = os.getenv("BACKEND_CORS_ORIGINS", "*")
allow_origins_list = [o.strip() for o in allowed_origins.split(",")] if allowed_origins else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Configuration / Environment variables (placeholders for Supabase integration) ---
# Note: Do not hardcode secrets. Orchestrator will populate .env; request values from user if needed.
SUPABASE_URL = os.getenv("SUPABASE_URL")  # Required if/when Supabase integration is implemented
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")  # Required if/when Supabase integration is implemented

# For this task, we will use in-memory storage for todos to keep the backend simple and self-contained.
# A production implementation can swap this with a persistence layer or Supabase integration.

# --- Data Models ---


class TodoBase(BaseModel):
    """Base fields shared across create and update models."""
    title: str = Field(..., description="Short title of the todo item", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Detailed description of the todo item", max_length=2000)
    completed: bool = Field(False, description="Whether the todo is completed")
    due_date: Optional[datetime] = Field(None, description="Optional due date for the todo (ISO 8601)")


class TodoCreate(TodoBase):
    """Payload model used for creating a new todo."""
    pass


class TodoUpdate(BaseModel):
    """Payload model used for updating an existing todo. All fields optional."""
    title: Optional[str] = Field(None, description="Short title of the todo item", min_length=1, max_length=200)
    description: Optional[str] = Field(None, description="Detailed description of the todo item", max_length=2000)
    completed: Optional[bool] = Field(None, description="Whether the todo is completed")
    due_date: Optional[datetime] = Field(None, description="Optional due date for the todo (ISO 8601)")


class Todo(TodoBase):
    """Full representation of a todo item."""
    id: str = Field(..., description="Unique identifier (UUID string) for the todo")
    created_at: datetime = Field(..., description="Creation timestamp (UTC)")
    updated_at: datetime = Field(..., description="Last update timestamp (UTC)")


# --- In-memory data store ---
# Keyed by id
_TODOS: Dict[str, Todo] = {}


def _now_utc() -> datetime:
    """Internal helper to get current UTC datetime without timezone info for consistency."""
    return datetime.utcnow()


# PUBLIC_INTERFACE
@app.get("/", tags=["health"], summary="Health Check", description="Verifies that the service is alive and responsive.")
def health_check():
    """Simple health check endpoint.

    Returns:
        JSON with a simple message and service status.
    """
    return {"message": "Healthy", "status": "ok", "version": app.version}


# PUBLIC_INTERFACE
@app.get(
    "/websocket-usage",
    tags=["websocket"],
    summary="WebSocket Usage Notes",
    description=(
        "This project currently does not expose WebSocket endpoints. "
        "If real-time updates are needed, add a WebSocket endpoint like `/ws/todos` and "
        "broadcast changes. Document connection parameters, payload shape, and events."
    ),
    operation_id="websocket_usage_notes",
)
def websocket_usage_notes():
    """Documentation helper route for WebSocket usage and future expansion."""
    return {
        "websocket_supported": False,
        "notes": "No WebSocket endpoints implemented. This route exists for API docs completeness.",
        "future_example": {
            "endpoint": "/ws/todos",
            "events": ["created", "updated", "deleted"],
            "payload_example": {"event": "created", "data": {"id": "uuid", "title": "Task"}},
        },
    }


# PUBLIC_INTERFACE
@app.get(
    "/todos",
    response_model=List[Todo],
    tags=["todos"],
    summary="List Todos",
    description="Returns a paginated list of todos with optional filtering by completion status.",
)
def list_todos(
    completed: Optional[bool] = Query(None, description="Filter todos by completion status"),
    skip: int = Query(0, ge=0, description="Number of items to skip"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of items to return"),
):
    """List todos with optional filtering and pagination.

    Args:
        completed: Optional filter for completion status.
        skip: Pagination offset.
        limit: Pagination limit (max 200).

    Returns:
        A list of Todo objects.
    """
    items = list(_TODOS.values())
    if completed is not None:
        items = [t for t in items if t.completed == completed]
    # Sort by created_at descending for a modern UX feel
    items.sort(key=lambda t: t.created_at, reverse=True)
    return items[skip : skip + limit]


# PUBLIC_INTERFACE
@app.post(
    "/todos",
    response_model=Todo,
    status_code=201,
    tags=["todos"],
    summary="Create Todo",
    description="Creates a new todo item and returns the created object.",
)
def create_todo(payload: TodoCreate):
    """Create a new todo.

    Args:
        payload: TodoCreate model containing the todo details.

    Returns:
        The created Todo object.
    """
    todo_id = str(uuid.uuid4())
    now = _now_utc()
    todo = Todo(
        id=todo_id,
        title=payload.title,
        description=payload.description,
        completed=payload.completed,
        due_date=payload.due_date,
        created_at=now,
        updated_at=now,
    )
    _TODOS[todo_id] = todo
    return todo


# PUBLIC_INTERFACE
@app.get(
    "/todos/{todo_id}",
    response_model=Todo,
    tags=["todos"],
    summary="Get Todo",
    description="Retrieves a single todo by its ID.",
)
def get_todo(
    todo_id: str = Path(..., description="The UUID of the todo to retrieve"),
):
    """Get a todo by id.

    Args:
        todo_id: The id of the todo.

    Returns:
        The Todo object.

    Raises:
        HTTPException 404 if not found.
    """
    todo = _TODOS.get(todo_id)
    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")
    return todo


# PUBLIC_INTERFACE
@app.put(
    "/todos/{todo_id}",
    response_model=Todo,
    tags=["todos"],
    summary="Update Todo",
    description="Replaces fields of an existing todo. Use PATCH semantics via PUT with partial payload using TodoUpdate.",
)
def update_todo(
    payload: TodoUpdate,
    todo_id: str = Path(..., description="The UUID of the todo to update"),
):
    """Update a todo.

    Args:
        payload: TodoUpdate model containing fields to modify.
        todo_id: The id of the todo to update.

    Returns:
        The updated Todo object.

    Raises:
        HTTPException 404 if not found.
    """
    existing = _TODOS.get(todo_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Todo not found")

    data = existing.model_dump()
    # Only update provided fields
    update_fields = payload.model_dump(exclude_unset=True)
    data.update({k: v for k, v in update_fields.items() if v is not None})
    data["updated_at"] = _now_utc()

    updated = Todo(**data)
    _TODOS[todo_id] = updated
    return updated


# PUBLIC_INTERFACE
@app.delete(
    "/todos/{todo_id}",
    tags=["todos"],
    summary="Delete Todo",
    description="Deletes a todo by ID and returns a confirmation message.",
)
def delete_todo(
    todo_id: str = Path(..., description="The UUID of the todo to delete"),
):
    """Delete a todo by id.

    Args:
        todo_id: The id of the todo to delete.

    Returns:
        A JSON confirmation message.

    Raises:
        HTTPException 404 if not found.
    """
    if todo_id not in _TODOS:
        raise HTTPException(status_code=404, detail="Todo not found")
    del _TODOS[todo_id]
    return JSONResponse(status_code=200, content={"message": "Todo deleted", "id": todo_id})


# PUBLIC_INTERFACE
@app.delete(
    "/todos",
    tags=["todos"],
    summary="Bulk Delete Todos",
    description="Deletes all todos. Useful for tests or resetting state.",
)
def delete_all_todos(confirm: bool = Query(False, description="Must be true to confirm deletion of all todos")):
    """Delete all todos (dangerous operation).

    Args:
        confirm: Must be true, otherwise the request is rejected.

    Returns:
        A JSON message with count of deleted items.

    Raises:
        HTTPException 400 if confirm is not true.
    """
    if not confirm:
        raise HTTPException(status_code=400, detail="Set confirm=true to delete all todos")
    count = len(_TODOS)
    _TODOS.clear()
    return {"message": "All todos deleted", "count": count}
