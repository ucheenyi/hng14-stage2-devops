import redis
import time
import os
import signal

r = redis.Redis(
    host=os.environ.get("REDIS_HOST", "redis"),   # Fix #2: was hardcoded "localhost"
    port=int(os.environ.get("REDIS_PORT", 6379)),
)

stop = False                                       # Fix #11: signal was imported but never used


def handle_sigterm(sig, frame):
    global stop
    stop = True


signal.signal(signal.SIGTERM, handle_sigterm)


def process_job(job_id):
    print(f"Processing job {job_id}", flush=True)
    time.sleep(2)  # simulate work
    r.hset(f"job:{job_id}", "status", "completed")
    print(f"Done: {job_id}", flush=True)


while not stop:
    job = r.brpop("jobs_queue", timeout=5)         # must match key used in api/main.py
    if job:
        _, job_id = job
        process_job(job_id.decode())
