# Enterprise Asset Management System

Greenfield EAM/CMMS built with **FastAPI + SQLAlchemy + PostgreSQL** and a **React** frontend. Implements the full canonical data model from the approved plan: assets, unified work orders, service requests, preventive maintenance, parts/inventory, purchase orders, meters, personnel, projects/budgets, webhooks, and custom fields.

## Architecture

```
enterprise-eam/
├── backend/           # FastAPI REST API (OpenAPI at /docs)
│   ├── app/
│   │   ├── models/    # SQLAlchemy 2.0 — all 9 domain areas
│   │   ├── schemas/   # Pydantic v2 DTOs
│   │   ├── routers/v1/
│   │   ├── services/  # PM queue, webhooks
│   │   └── common/    # Auth, pagination, custom fields, audit
│   ├── alembic/
│   └── seed.py
├── apps/web/          # React + TanStack Query + React Router
├── docker-compose.yml
└── .env.example
```

## Quick Start

### 1. Start PostgreSQL

```bash
docker compose up -d db
```

### 2. Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
# Python 3.14: use compatibility flag if needed
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 pip install -r requirements.txt

cp ../.env.example .env   # or set DATABASE_URL
python seed.py            # create tables + demo data
uvicorn app.main:app --reload --port 8000
```

Or for local dev without Docker:

```bash
USE_SQLITE=1 python seed.py
USE_SQLITE=1 uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 3. Frontend

```bash
cd apps/web
cp .env.example .env
npm install
npm run dev
```

UI: http://localhost:5173

### Demo credentials

| Role      | Email               | Password    |
|-----------|---------------------|-------------|
| Admin     | admin@eam.demo      | admin123    |
| Planner   | planner@eam.demo    | planner123  |
| Technician| tech@eam.demo       | tech123     |
| Requester | requester@eam.demo  | requester123|

## API Modules

| Module | Prefix | Features |
|--------|--------|----------|
| Auth | `/v1/auth` | JWT login, API keys |
| Organization | `/v1/organizations`, `/v1/sites`, `/v1/locations` | Hierarchy, cost centers, projects, budgets |
| Lookups | `/v1/lookups/{code}` | Reference data |
| Assets | `/v1/assets` | CRUD, relationships, warranties, attachments, history |
| Work Orders | `/v1/work-orders` | Unified CM/PM/GENERAL, search, complete, assignments, parts, comments |
| Service Requests | `/v1/service-requests` | Submit, convert to WO, decline |
| PM | `/v1/pm-queue`, `/v1/asset-tasks` | Task library, checklists, test points, auto-generate WOs |
| Parts | `/v1/parts` | Inventory, adjustments, asset links |
| Purchase Orders | `/v1/purchase-orders` | Create, receive (updates stock) |
| Meters | `/v1/meter-readings` | Readings, history, batch update, PM trigger |
| Personnel | `/v1/personnel` | Staff/contractor, trainings, security groups |
| Webhooks | `/v1/webhooks` | Subscriptions, delivery logs |
| Reports | `/v1/reports/summary` | Dashboard KPIs |

## Design Decisions

- **Unified WorkOrder** with `type`: CORRECTIVE | PREVENTIVE | GENERAL
- **Dual ID**: UUID primary key + user-facing `number`
- **Soft deletes** via `deleted_at` + `row_version` optimistic concurrency
- **Custom fields**: `CustomFieldDefinition` + `CustomFieldValue` (use `?customFields=true`)
- **Partial updates**: `fields_to_update` array on PUT bodies
- **Pagination**: `page`, `page_size` → `PaginatedResponse`
- **PM scheduler**: APScheduler runs every 15 minutes
- **Webhooks**: Sync HTTP dispatch on asset/WO/SR events

## Docker (full stack)

```bash
docker compose up --build
```

## Core Workflows

1. **Asset → PM task → PM work order**: Create asset task with due date → appears in PM queue → `POST /v1/pm-queue/generate`
2. **Service request → Work order**: `POST /v1/service-requests/{id}/convert-to-work-order`
3. **Meter reading → PM evaluation**: `PUT /v1/meter-readings/batch/by-asset`
4. **Purchase order → Stock**: `PUT /v1/purchase-orders/{id}/receive`

## Python 3.14 Note

If `pip install` fails on pydantic-core, use:

```bash
PYO3_USE_ABI3_FORWARD_COMPATIBILITY=1 pip install -r requirements.txt
```

Or use Python 3.12/3.13 in production.
