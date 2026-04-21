# hng14-stage2-devops

A containerised job-processing system with four services: frontend (Node.js), api (Python/FastAPI), worker (Python), and redis.

---

## Prerequisites

| Tool | Minimum version |
|------|----------------|
| Docker | 24.x |
| Docker Compose v2 | bundled with Docker Desktop |
| Git | any |

Verify your setup:

    docker --version
    docker compose version

---

## Bring the stack up from scratch

    # 1. Clone
    git clone https://github.com/ucheenyi/hng14-stage2-devops.git
    cd hng14-stage2-devops

    # 2. Create env file
    cp .env.example .env

    # 3. Build and start everything
    docker compose up --build -d

    # 4. Confirm all services are healthy
    docker compose ps

Expected output - all four services show healthy:

    NAME                               STATUS
    hng14-stage2-devops-api-1          Up (healthy)
    hng14-stage2-devops-frontend-1     Up (healthy)
    hng14-stage2-devops-redis-1        Up (healthy)
    hng14-stage2-devops-worker-1       Up (healthy)

---

## Open the dashboard

Visit http://localhost:3000 and click **Submit New Job**. The status updates to `completed` within ~2 seconds.

---

## Verify the API directly

    curl http://localhost:3000/health
    # {"status":"ok"}

    curl -X POST http://localhost:3000/submit
    # {"job_id":"<uuid>"}

    curl http://localhost:3000/status/<uuid>
    # {"job_id":"<uuid>","status":"completed"}

---

## Stop the stack

    docker compose down        # stop, keep volumes
    docker compose down -v     # stop and delete volumes (full reset)

---

## Run unit tests locally

    cd api
    pip install -r requirements.txt pytest pytest-cov httpx
    pytest tests/ -v --cov=. --cov-report=term-missing

---

## CI/CD Pipeline

Stages run in strict order - failure in any stage blocks all subsequent stages:

    lint -> test -> build -> security-scan -> integration-test -> deploy

| Stage | What it does |
|-------|-------------|
| lint | flake8 (Python), eslint (JS), hadolint (Dockerfiles) |
| test | pytest with mocked Redis; uploads coverage XML artifact |
| build | Builds all 3 images tagged with git SHA + latest; pushes to local registry service container |
| security-scan | Trivy scans all images; fails on CRITICAL CVEs; uploads SARIF artifact |
| integration-test | Full stack up, submits real job, polls until completed, tears down |
| deploy | SSH rolling update on main branch pushes only - new container must pass health check within 60s |

### Deploy secrets required (Settings > Secrets > Actions)

| Secret | Value |
|--------|-------|
| DEPLOY_HOST | Production server IP or hostname |
| DEPLOY_USER | SSH username |
| DEPLOY_KEY | Private SSH key |

---

## Project structure

    .
    ├── api/
    │   ├── main.py
    │   ├── requirements.txt
    │   ├── Dockerfile
    │   └── tests/
    │       └── test_main.py
    ├── worker/
    │   ├── worker.py
    │   ├── requirements.txt
    │   └── Dockerfile
    ├── frontend/
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
