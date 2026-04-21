
from fastapi import FastAPI, HTTPException
import redis
import uuid
import os

app = FastAPI()

r = redis.Redis(
    host=os.environ.get("REDIS_HOST", "redis"),   # Fix #1: was hardcoded "localhost"
    port=int(os.environ.get("REDIS_PORT", 6379)),
)


@app.get("/health")                               # Fix #5: health endpoint was missing
def health():
    r.ping()
    return {"status": "ok"}


@app.post("/jobs")
def create_job():
    job_id = str(uuid.uuid4())
    # lpush + brpop = FIFO queue (push left, pop right)
    r.lpush("jobs_queue", job_id)
    r.hset(f"job:{job_id}", "status", "queued")
    return {"job_id": job_id}


@app.get("/jobs/{job_id}")
def get_job(job_id: str):
    status = r.hget(f"job:{job_id}", "status")
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")  # Fix #9: was returning 200
    return {"job_id": job_id, "status": status.decode()}
