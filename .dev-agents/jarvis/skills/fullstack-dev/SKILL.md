---
name: fullstack-dev
description: Full-stack development guide for building production-grade web applications with Next.js 15 + FastAPI + SQLAlchemy + Redis. Use this skill whenever Jarvis needs to implement features, design APIs, create database models, build React components, write Celery workers, fix bugs, or perform any frontend/backend development work. Covers architecture patterns, code quality standards, and VibeArtifact-specific patterns like the IR system and snapshot mechanism.
---

# Full-Stack Development Skill

This skill provides a systematic approach to full-stack development in the VibeArtifact tech stack. It covers the complete development lifecycle from requirement analysis to implementation, ensuring code quality, architectural consistency, and maintainability.

## Tech Stack Quick Reference

| Layer | Technology | Key Libraries |
|-------|-----------|---------------|
| Frontend | Next.js 15 + React + TypeScript | App Router, Server Components, TanStack Query |
| API | FastAPI + Python 3.12 | Pydantic v2, SQLAlchemy 2, Alembic |
| Worker | Celery + Python 3.12 | Redis broker, task chains |
| Database | PostgreSQL | SQLAlchemy 2 ORM, Alembic migrations |
| Cache/Queue | Redis | caching, pub/sub, distributed locks |

## Development Workflow

### 1. Understand Before Coding

Before writing any code, build a mental model of what exists:

- **Read related code first** — Find 3 similar implementations in the codebase using Grep/Glob. Understand the patterns before introducing new ones.
- **Check the data model** — Understand which SQLAlchemy models are involved and how they relate.
- **Trace the request flow** — For API work, trace from route handler through service layer to database. For frontend, trace from component through hooks to API calls.
- **Identify integration points** — What other modules depend on or are affected by your change?

### 2. Implementation Sequence

Follow a consistent order to avoid rework:

```
Database Model (if needed)
    -> Alembic Migration
        -> Service/Repository Layer
            -> API Route Handler
                -> Frontend API Hook
                    -> React Component
                        -> Integration Verification
```

Not every task touches every layer. Skip layers that don't need changes, but maintain the sequence for layers that do.

### 3. Code Quality Standards

#### Chinese Comments (Mandatory)

All comments must be in Chinese. This is a hard project rule.

```python
# Correct
# Calculate user activity score based on recent 30-day login frequency
def calc_activity_score(user_id: int) -> float:
    """
    Calculate user activity score.

    Parameters:
        user_id: User ID

    Returns:
        Activity score between 0-100
    """
    pass
```

```typescript
// Correct
/** Fetch project list and handle pagination */
function useProjects(page: number) {
  // ...
}
```

**Rules:**
- Comments go on a **separate line above** the code, never at the end of a line
- Module top: describe what this module is responsible for
- Class: describe its purpose
- Function: describe functionality, parameter meanings, return value
- Key logic: explain **why**, not what
- Skip comments for obvious assignments and imports

#### Code Style

- Follow existing patterns in the codebase — match naming, imports, formatting
- Single responsibility per function/class
- No clever tricks; choose the boring, obvious solution
- Handle errors at system boundaries (user input, external APIs), trust internal code

---

## Frontend Development (Next.js 15 + React)

### App Router Conventions

```
apps/web/src/
├── app/                    # Routes (App Router)
│   ├── (auth)/            # Route groups
│   ├── layout.tsx         # Root layout
│   └── page.tsx           # Home page
├── components/            # Shared components
│   ├── ui/               # Base UI components
│   └── features/         # Feature-specific components
├── hooks/                 # Custom React hooks
├── lib/                   # Utilities and config
├── services/             # API client functions
└── types/                # TypeScript type definitions
```

### Component Patterns

**Server Components** (default in Next.js 15):
- Use for data fetching, static content, SEO-critical pages
- Cannot use hooks, event handlers, or browser APIs
- Prefer `async/await` for data loading

**Client Components** (add `'use client'` directive):
- Use for interactive UI, form handling, state management
- Keep client components as leaf nodes — push interactivity down, keep layout on the server

**Component Structure:**
```tsx
'use client'

import { useState } from 'react'

/** Project card component displaying project basic info and status */
interface ProjectCardProps {
  project: Project
  onSelect?: (id: string) => void
}

export function ProjectCard({ project, onSelect }: ProjectCardProps) {
  // Hooks at the top
  const [isExpanded, setIsExpanded] = useState(false)

  // Handlers
  const handleClick = () => onSelect?.(project.id)

  // Render
  return (
    <div onClick={handleClick}>
      {/* ... */}
    </div>
  )
}
```

### Data Fetching

- **Server side**: Use `fetch` in Server Components or Route Handlers
- **Client side**: Use TanStack Query (React Query) for caching, mutations, and optimistic updates
- API client functions live in `services/` — one file per API domain

### Styling

- Follow the design system established by Ella's design specs
- Use CSS Modules or Tailwind (whichever the project uses) — check existing components
- CSS variables for theme tokens (colors, spacing, typography)

---

## Backend Development (FastAPI + Python)

### Project Structure

```
services/api/api_app/
├── routes/               # API route handlers (thin layer)
├── services/             # Business logic
├── repositories/         # Database access layer
├── models/               # SQLAlchemy ORM models
├── schemas/              # Pydantic request/response schemas
├── deps/                 # Dependency injection
└── core/                 # Config, security, exceptions
```

### API Design Principles

**Route handlers should be thin** — they validate input (via Pydantic), call service functions, and return responses. Business logic lives in services.

```python
"""
Project route handler module.
Provides CRUD API endpoints for projects.
"""

from fastapi import APIRouter, Depends
from .schemas import ProjectCreate, ProjectResponse
from .services import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])

@router.post("/", response_model=ProjectResponse)
async def create_project(
    data: ProjectCreate,
    service: ProjectService = Depends()
):
    """Create a new project"""
    return await service.create(data)
```

**Pydantic Schemas** — Separate input and output schemas. Use `model_config` for ORM mode.

```python
"""
Project Pydantic schemas.
Define request/response data structures for the project API.
"""

from pydantic import BaseModel, ConfigDict

class ProjectCreate(BaseModel):
    """Project creation request schema"""
    name: str
    description: str | None = None

class ProjectResponse(BaseModel):
    """Project response schema"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
```

### SQLAlchemy 2 Patterns

**Model Definition:**
```python
"""
Project ORM model.
Maps to the projects table, stores project metadata and configuration.
"""

from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .base import Base, TimestampMixin

class Project(Base, TimestampMixin):
    """Project entity, the top-level container for user work"""
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text, default=None)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"))

    # Relationships
    owner: Mapped["User"] = relationship(back_populates="projects")
```

**Async Session Pattern:**
```python
from sqlalchemy.ext.asyncio import AsyncSession

async def get_project(session: AsyncSession, project_id: int) -> Project | None:
    """Query a single project by ID"""
    return await session.get(Project, project_id)
```

### Alembic Migrations

When adding or modifying models:

```bash
# Generate migration after model changes
cd services/api && alembic revision --autogenerate -m "add projects table"

# Apply migration
alembic upgrade head

# Rollback one version
alembic downgrade -1
```

Migration files must include Chinese comments explaining what changed and why.

### Celery Workers

```python
"""
Project generation worker task module.
Handles async project build tasks dispatched from the API.
"""

from celery import shared_task

@shared_task(bind=True, max_retries=3)
def generate_project(self, project_id: int):
    """
    Async task to generate project artifacts.

    Parameters:
        project_id: ID of the project to generate
    """
    try:
        # Task implementation
        pass
    except Exception as exc:
        # Retry with exponential backoff
        self.retry(exc=exc, countdown=2 ** self.request.retries)
```

### Redis Patterns

- **Caching**: Use for frequently read, rarely changed data. Set TTL.
- **Distributed Lock**: Use for concurrent access control (e.g., snapshot operations).
- **Task Queue**: Celery broker — no direct interaction needed.

---

## Bug Fixing Methodology

1. **Reproduce** — Confirm the bug exists. Get the exact steps, inputs, and expected vs. actual behavior.
2. **Locate** — Use Grep to search for related code. Trace the execution path from entry point to failure.
3. **Understand** — Read the surrounding code. Understand why it was written this way before changing it.
4. **Fix minimally** — Change only what's needed. Don't refactor, don't "improve" adjacent code.
5. **Verify** — Confirm the fix resolves the issue and doesn't break anything else.

---

## VibeArtifact Architecture Patterns

These patterns are specific to this project. Reference them when working on related modules.

### IR (Intermediate Representation) System

IR is the core data structure. All Agents collaborate indirectly through IR using a blackboard pattern.

- **IR Tree**: Hierarchical structure representing generated project artifacts (pages, components, APIs, DB schemas)
- **IROperation**: Atomic operations on the IR tree (add/modify/delete nodes). LLMs output high-level business structures; Translators convert these to IROperations.
- **IR Projection**: Read-only views of the IR tree for specific consumers (e.g., code generator sees code nodes, doc generator sees doc nodes)

When implementing IR-related code, follow the type system defined in `packages/py/ir_core/`.

### Snapshot Mechanism

- **Full physical snapshots**: Each snapshot is a complete copy of the IR tree state
- **Subtree-level Lease Lock**: Concurrent access control at the subtree granularity, not the whole tree
- **Snapshot-Aware Tree Conversation**: Each conversation session is bound to a snapshot branch

When working with snapshots, always acquire the appropriate lease lock before modification, and release it in a `finally` block.

### Agent Collaboration

- All Agents are the same LLM with different prompt configurations (not a multi-model cluster)
- Agents communicate through the IR system, never directly
- Each Agent reads IR projections relevant to its role and writes IROperations

---

## Error Handling

### Python (FastAPI)

```python
from fastapi import HTTPException

# Use HTTPException for client errors
raise HTTPException(status_code=404, detail="Project not found")

# Use custom exceptions for domain errors
class ProjectLimitExceeded(Exception):
    """Raised when user exceeds project creation limit"""
    pass
```

### TypeScript (Next.js)

```typescript
// API call error handling - centralize in service layer
async function fetchProject(id: string): Promise<Project> {
  const res = await fetch(`/api/projects/${id}`)
  if (!res.ok) {
    throw new ApiError(res.status, await res.text())
  }
  return res.json()
}
```

Don't over-handle errors. Let unexpected errors bubble up to global handlers. Only catch errors you can meaningfully recover from.

---

## Checklist Before Completion

- [ ] Code follows existing patterns in the codebase
- [ ] All comments are in Chinese, on separate lines above code
- [ ] Database changes have corresponding Alembic migration
- [ ] API endpoints have Pydantic schemas for input validation and output serialization
- [ ] No security vulnerabilities introduced (injection, XSS, auth bypass)
- [ ] Changes are minimal — only what was requested
