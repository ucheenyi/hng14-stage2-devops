# FIXES.md — Bug Report

Every issue found in the original source, documented with file, line number, problem description, and fix applied.

---

## Fix #1 — Hardcoded Redis host in API (CRITICAL)

- **File:** `api/main.py`, Line 8
- **Problem:** `redis.Redis(host="localhost", port=6379)` — `localhost` resolves to the container itself inside Docker. The API container cannot reach the Redis container this way; the connection will always fail at runtime.
- **Fix:** Changed to read from environment variables:
```python
  r = redis.Redis(
      host=os.environ.get("REDIS_HOST", "redis"),
      port=int(os.environ.get("REDIS_PORT", 6379))
  )
```

---

## Fix #2 — Hardcoded Redis host in Worker (CRITICAL)

- **File:** `worker/worker.py`, Line 6
- **Problem:** Same as Fix #1 — `redis.Redis(host="localhost", port=6379)` hardcoded. The worker will fail to connect to Redis inside Docker.
- **Fix:** Changed to read from environment variables:
```python
  r = redis.Redis(
      host=os.environ.get("REDIS_HOST", "redis"),
      port=int(os.environ.get("REDIS_PORT", 6379))
  )
```

---

## Fix #3 — Hardcoded API URL in Frontend (CRITICAL)

- **File:** `frontend/app.js`, Line 6
- **Problem:** `const API_URL = "http://localhost:8000"` — `localhost` inside the frontend container points to itself, not the API container. All job submissions and status checks will fail with a connection refused error.
- **Fix:** Changed to read from environment variable:
```js
  const API_URL = process.env.API_URL || "http://api:8000";
```

---

## Fix #4 — Real `.env` file committed to repository (SECURITY/CRITICAL)

- **File:** `api/.env`
- **Problem:** A `.env` file containing `REDIS_PASSWORD=supersecretpassword123` and `APP_ENV=production` was committed directly into the repository. This is a severe security violation — credentials in git history are compromised permanently.
- **Fix:**
  1. Deleted `api/.env` from the repository.
  2. Added `.env` and `api/.env` to `.gitignore`.
  3. Created `.env.example` at the repo root with placeholder values for all required variables.
  4. The `REDIS_PASSWORD` defined in the `.env` was also never actually used by `main.py` or `worker.py` — the Redis client was instantiated with no password argument at all, meaning the `.env` was dead configuration. Both files now use `os.environ.get()` consistently.

---

## Fix #5 — API has no `/health` endpoint (CRITICAL for Docker healthcheck)

- **File:** `api/main.py`
- **Problem:** No `/health` endpoint exists. Docker `HEALTHCHECK` and `depends_on: condition: service_healthy` in Compose both require a working health route. Without it, all dependent services would never start.
- **Fix:** Added a `/health` endpoint:
```python
  @app.get("/health")
  def health():
      r.ping()
      return {"status": "ok"}
```

---

## Fix #6 — Frontend has no `/health` endpoint

- **File:** `frontend/app.js`
- **Problem:** No `/health` route exists on the Express server. The Docker `HEALTHCHECK` instruction and the integration test both require a health endpoint.
- **Fix:** Added:
```js
  app.get('/health', (req, res) => res.json({ status: 'ok' }));
```

---

## Fix #7 — API not binding to `0.0.0.0`

- **File:** `api/main.py` (startup / Dockerfile CMD)
- **Problem:** The FastAPI app has no explicit host binding configured. Without `--host 0.0.0.0`, uvicorn defaults to `127.0.0.1`, making the API unreachable from other containers or the Docker bridge network.
- **Fix:** Dockerfile CMD explicitly passes `--host 0.0.0.0`:
```dockerfile
  CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Fix #8 — Queue key mismatch between API and Worker

- **File:** `api/main.py` Line 12, `worker/worker.py` Line 13
- **Problem:** The API pushes job IDs with `r.lpush("job", job_id)` (key: `"job"`). The worker reads with `r.brpop("job", timeout=5)` (key: `"job"`). These match — however, the API uses `lpush` (push to LEFT / head) while the worker uses `brpop` (pop from RIGHT / tail). This is actually correct FIFO queue behaviour — but only accidentally. It is documented here as a notable pattern to make explicit.
- **Fix:** No functional change needed. Added a comment in both files to make the FIFO queue contract explicit and intentional.

---

## Fix #9 — `get_job` returns 200 on missing job instead of 404

- **File:** `api/main.py`, Lines 18–21
- **Problem:**
```python
  if not status:
      return {"error": "not found"}
```
  This returns HTTP 200 with an error body. Any HTTP client or integration test checking the status code will not detect the error. The frontend's polling logic also silently breaks on a missing job.
- **Fix:** Changed to raise a proper 404:
```python
  from fastapi import HTTPException
  ...
  if not status:
      raise HTTPException(status_code=404, detail="Job not found")
```

---

## Fix #10 — No `package-lock.json` / missing `npm ci` support

- **File:** `frontend/package.json`
- **Problem:** No `package-lock.json` is present. The Dockerfile uses `npm ci` for reproducible installs, which requires a lockfile. Without it, `npm ci` fails entirely.
- **Fix:** Generated `package-lock.json` by running `npm install` locally and committed the lockfile. The Dockerfile now runs `npm ci` reliably.

---

## Fix #11 — Worker has no graceful shutdown handling

- **File:** `worker/worker.py`
- **Problem:** `signal` is imported but never used. The worker runs an infinite `while True` loop with no signal handler. When Docker sends `SIGTERM` on container stop, the worker is killed mid-job, potentially leaving a job stuck in `queued` state permanently.
- **Fix:** Added a SIGTERM handler that sets a stop flag:
```python
  import signal
  stop = False
  def handle_sigterm(sig, frame):
      global stop
      stop = True
  signal.signal(signal.SIGTERM, handle_sigterm)

  while not stop:
      ...
```

---

## Summary Table

| # | File | Line | Category | Severity |
|---|------|------|----------|----------|
| 1 | `api/main.py` | 8 | Hardcoded `localhost` for Redis | CRITICAL |
| 2 | `worker/worker.py` | 6 | Hardcoded `localhost` for Redis | CRITICAL |
| 3 | `frontend/app.js` | 6 | Hardcoded `localhost` for API URL | CRITICAL |
| 4 | `api/.env` | — | Secrets committed to repository | SECURITY |
| 5 | `api/main.py` | — | Missing `/health` endpoint | HIGH |
| 6 | `frontend/app.js` | — | Missing `/health` endpoint | HIGH |
| 7 | Dockerfile CMD | — | uvicorn binding to 127.0.0.1 | HIGH |
| 8 | `api/main.py` / `worker/worker.py` | 12/13 | Queue direction documented | LOW |
| 9 | `api/main.py` | 18–21 | Wrong HTTP status on missing job | MEDIUM |
| 10 | `frontend/` | — | Missing `package-lock.json` | MEDIUM |
| 11 | `worker/worker.py` | — | No graceful SIGTERM handling | MEDIUM |