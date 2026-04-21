#!/bin/bash
# integration-test.sh - Full stack integration test
set -e

TIMEOUT=120
POLL_INTERVAL=5
FRONTEND_URL="http://localhost:3000"

echo "==> Starting integration test"

# Wait for frontend to be healthy
echo "==> Waiting for frontend health..."
elapsed=0
until curl -sf "$FRONTEND_URL/health" > /dev/null 2>&1; do
    if [ "$elapsed" -ge "$TIMEOUT" ]; then
        echo "ERROR: Frontend did not become healthy within ${TIMEOUT}s"
        exit 1
    fi
    echo "    Waiting... ${elapsed}s elapsed"
    sleep "$POLL_INTERVAL"
    elapsed=$((elapsed + POLL_INTERVAL))
done
echo "==> Frontend is healthy"

# Submit a job
echo "==> Submitting job..."
RESPONSE=$(curl -sf -X POST "$FRONTEND_URL/submit" \
    -H "Content-Type: application/json")
echo "    Response: $RESPONSE"

JOB_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")
echo "==> Job submitted: $JOB_ID"

# Poll until completed
echo "==> Polling for completion..."
elapsed=0
while true; do
    if [ "$elapsed" -ge "$TIMEOUT" ]; then
        echo "ERROR: Job did not complete within ${TIMEOUT}s"
        exit 1
    fi

    STATUS=$(curl -sf "$FRONTEND_URL/status/$JOB_ID" | \
        python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
    echo "    Status after ${elapsed}s: $STATUS"

    if [ "$STATUS" = "completed" ]; then
        echo "==> Job completed successfully!"
        exit 0
    fi

    sleep "$POLL_INTERVAL"
    elapsed=$((elapsed + POLL_INTERVAL))
done
