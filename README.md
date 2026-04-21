# hng14-stage2-devops

A containerised job-processing system with four services: frontend (Node.js), api (Python/FastAPI), worker (Python), and redis.

---

## Prerequisites

| Tool | Minimum version |
|------|----------------|
| Docker | 24.x |
| Docker Compose v2 | bundled with Docker Desktop |
| Git | any |

```bash
docker --version
docker compose version
```

---

## Bring the stack up from scratch

```bash
# 1. Clone
git clone https://github.com/ucheenyi/hng14-stage2-devops.git
cd hng14-stage2-devops

# 2. Create env file (defaults work for local dev)
cp .env.example .env

# 3. Build and start everything
docker compose up --build -d

# 4. Confirm all services are healthy
docker compose ps
```

Expected — all four services show **healthy**:
```
NAME                STATUS
stage2-redis-1      Up X seconds (healthy)
stage2-api-1        Up X seconds (healthy)
stage2-worker-1     Up X seconds (healthy)
stage2-frontend-1   Up X seconds (healthy)
```

### 5. Open the dashboard

Visit **http://localhost:3000** — click **Submit New Job**. The status updates to `completed` within ~2 seconds.

---

## Verify the API directly

```bash
curl http://localhost:8000/health
# {"status":"ok"}

curl -X POST http://localhost:8000/jobs
# {"job_id":"<uuid>"}

curl http://localhost:8000/jobs/<uuid>
# {"job_id":"<uuid>","status":"completed"}
```

---

## Stop the stack

```bash
docker compose down        # stop, keep volumes
docker compose down -v     # stop, delete volumes (full reset)
```

---

## Run unit tests locally

```bash
cd api
pip install -r requirements.txt pytest pytest-cov httpx
pytest tests/ -v --cov=. --cov-report=term-missing
```

---

## CI/CD Pipeline

Stages run in strict order — failure in any stage blocks all subsequent stages:

```
lint → test → build → security-scan → integration-test → deploy
```

| Stage | What it does |
|-------|-------------|
| **lint** | flake8 (Python), eslint (JS), hadolint (Dockerfiles) |
| **test** | pytest with mocked Redis; uploads coverage XML artifact |
| **build** | Builds all 3 images tagged with git SHA + latest; pushes to local registry service container |
| **security-scan** | Trivy scans all images; fails on CRITICAL CVEs; uploads SARIF artifact |
| **integration-test** | Full stack up, submits real job, polls until completed, tears down |
| **deploy** | SSH rolling update on main branch pushes only — new container must pass health check within 60s |

### Deploy secrets (Settings → Secrets → Actions)

| Secret | Value |
|--------|-------|
| `DEPLOY_HOST` | Production server IP or hostname |
| `DEPLOY_USER` | SSH username |
| `DEPLOY_KEY` | Private SSH key |

---

## Project structure

```
.
├── api/                    # FastAPI service
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/test_main.py
├── worker/                 # Queue consumer
│   ├── worker.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/               # Express UI
│   ├── app.js
│   ├── package.json
│   ├── .eslintrc.json
│   ├── Dockerfile
│   └── views/index.html
├── .github/workflows/ci.yml
├── docker-compose.yml
├── .env.example
├── .gitignore
├── FIXES.md
└── README.md
```
