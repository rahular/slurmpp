# slurm++

A centralized, role-aware dashboard for Slurm HPC clusters. Designed for both **researchers** (job submission, personal analytics) and **cluster admins** (utilization heatmaps, per-user efficiency).

## What makes it different

| Feature | slurm++ | Slurm-web | Grafana stack |
|---------|---------|-----------|---------------|
| Job submission UI | ✅ | ❌ | ❌ |
| Historical analytics | ✅ | ❌ | ✅ (complex) |
| Fairshare visualization | ✅ | ❌ | partial |
| Single-command setup | ✅ | ❌ | ❌ |
| No Prometheus/Redis needed | ✅ | ❌ | ❌ |
| Multi-role (user + admin) | ✅ | admin only | admin only |

## Quick Start

```bash
git clone <repo>
cd slurm++
cp .env.example .env
# Edit .env: set JWT_SECRET_KEY and SLURM_INTERFACE

docker compose up -d

# First-time: create admin user
docker compose exec backend python -m app.cli create-admin admin yourpassword
```

Open http://localhost — log in and start using it.

## Architecture

```
nginx:80
  ├── /api/*  →  FastAPI backend:8000
  └── /*      →  React SPA (Vite build)

Backend
  ├── FastAPI (async)
  ├── SQLite (via aiosqlite + SQLAlchemy 2.0)
  ├── APScheduler (background polling)
  └── SlurmClient
       ├── REST adapter  →  slurmrestd HTTP API  (preferred)
       └── CLI adapter   →  squeue / sinfo / sacct / sbatch (fallback)
```

## Configuration

All config is via environment variables (see `.env.example`).

### Slurm connection

| Variable | Values | Description |
|----------|--------|-------------|
| `SLURM_INTERFACE` | `auto` / `rest` / `cli` | `auto` probes REST, falls back to CLI |
| `SLURM_REST_URL` | URL | slurmrestd endpoint (if using REST) |
| `SLURM_REST_TOKEN` | JWT | Token for slurmrestd auth |

### Authentication

| Variable | Values | Description |
|----------|--------|-------------|
| `AUTH_BACKEND` | `local` / `ldap` | `local` stores users in SQLite |
| `LDAP_URL` | URL | LDAP server (if using LDAP) |
| `LDAP_ADMIN_GROUP_DN` | DN | Members get admin role |

### First run (local auth)

```bash
# Option 1: via API (only works when no users exist)
curl -X POST http://localhost/auth/setup \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "yourpassword"}'

# Option 2: via CLI
docker compose exec backend python -m app.cli create-admin admin yourpassword

# Option 3: via Makefile
make setup-admin
```

## Development

```bash
make setup          # install backend + frontend deps
make dev-backend    # uvicorn with --reload on :8000
make dev-frontend   # vite dev server on :5173 (proxies /api to :8000)
make test           # run pytest
make lint           # mypy + tsc
```

## Features

### Dashboard
- Cluster stats cards (nodes, CPUs, running/pending jobs)
- Node grid — color-coded by state (idle/alloc/down/drain) with hover details
- Auto-refreshes every 15 seconds

### Jobs
- Filterable/paginated table with URL-synced filters (`?state=RUNNING&partition=gpu`)
- Job detail: metadata, resource info, output log streaming (SSE)
- Actions: Cancel, Hold, Requeue, Signal — context-sensitive by job state

### Job Submission (key differentiator)
3-step wizard:
1. **Resources** — partition (with node counts), nodes/CPUs/GPUs/memory/walltime
2. **Script** — bash editor (CodeMirror 6) with live `#SBATCH` header preview + env vars
3. **Review & Submit** — final preview before sending

### Analytics (user view)
- CPU-hours / GPU-hours over time (area chart, 7d/30d/90d)
- Fairshare factor gauge with warning when below 25%
- Burn rate: CPU-hours/day and GPU-hours/day
- Per-partition efficiency breakdown

### Admin view
- Cluster utilization heatmap (day × hour)
- Per-user usage table: jobs, CPU-hours, GPU-hours, efficiency

## Deployment on a real cluster

The backend needs access to Slurm tools. For **CLI adapter**, mount the relevant paths:

```yaml
# docker-compose.yml backend service
volumes:
  - /etc/slurm:/etc/slurm:ro
  - /var/run/munge:/var/run/munge:ro
```

For **REST adapter**, configure slurmrestd and set `SLURM_REST_URL` + `SLURM_REST_TOKEN`.

## Roadmap

- [ ] OIDC/Keycloak SSO
- [ ] Job array support (expand tasks in detail view)
- [ ] GPU utilization per job (nvidia-smi integration)
- [ ] Saved job templates ("My Scripts" library)
- [ ] Email/webhook notifications on job completion
- [ ] Multi-cluster support
- [ ] `pip install slurmpp-server` (bundled frontend)
