---
id: 001
title: StoreLite IMS Constitution Ratification
stage: constitution
date: 2025-12-07
surface: agent
model: claude-opus-4-5-20251101
feature: none
branch: master
user: system
command: /sp.constitution
labels: ["constitution", "project-setup", "tdd", "storelite"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
  - .specify/memory/constitution.md
tests:
  - N/A (constitution document, no code tests)
---

## Prompt

write the constitution for our project, project name: "StoreLite IMS** – Simple Inventory & Billing System"  @"IMS Simple Inventory & Billing System .md" this is my project file in this file I'll define step by step implementation phase, backend we will used python version 12+ and initilizaitng project using UV command for database we will use neon postgress sql. and front end we will use next js latest version. for agent we will use openai agent sdk and agetn UI we use Openai chatkit sdk. I've define in short, if any other opurtunity you can find in the docs you will definitly use it. but most importanat every backend and frontend code in saperate folde, andevery backend logic user TDD (test driven developemnt) approach. TDD is very important for backend, console, fast api, agent, mcp, agent connects to UI (chatkit UI). all test pass to the TDD approach. the test passing ration is 80%

## Response snapshot

Created constitution v1.0.0 for StoreLite IMS with 8 core principles:

1. **Separation of Concerns (NON-NEGOTIABLE)** - Backend/frontend in separate directories
2. **Test-Driven Development (NON-NEGOTIABLE)** - Red-Green-Refactor with 80% coverage
3. **Phased Implementation** - 6-phase progression from Console to ChatKit
4. **Database-First Design** - Neon PostgreSQL as single source of truth
5. **Contract-First APIs** - Pydantic schemas, OpenAPI docs
6. **Local-First Development** - Local MCP, Gemini-lite model, no hosted tools
7. **Simplicity Over Abstraction** - YAGNI, minimal complexity
8. **Observability by Default** - Structured logging, error context

Technology stack defined:
- Backend: Python 3.12+, uv, SQLAlchemy 2.x, FastAPI, pytest, FastMCP, OpenAI Agents SDK
- Frontend: Next.js 14+, Tailwind CSS, ChatKit SDK
- Database: Neon PostgreSQL (items, bills, bill_items tables)

Project structure established with `backend/` and `frontend/` directories.

## Outcome

- Impact: Initial constitution ratified, establishing all project governance and technical principles
- Tests: N/A (governance document)
- Files: .specify/memory/constitution.md (created)
- Next prompts: /sp.specify for Phase 1 feature specification, project initialization with uv
- Reflection: User emphasized TDD importance; captured as NON-NEGOTIABLE principle with explicit 80% threshold

## Evaluation notes (flywheel)

- Failure modes observed: None
- Graders run and results (PASS/FAIL): N/A (manual review required)
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Validate constitution gates work in /sp.plan command
