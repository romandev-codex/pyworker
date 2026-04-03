# Mock PyWorker

This backend provides a lightweight mock model service for validating Serverless endpoint wiring without running a real model.

## Endpoints

- `/health`: Returns service health.
- `/prompt`: Starts an asynchronous mock job and returns a `prompt_id`.
- `/history`: Returns status and result for a `prompt_id`.

## Behavior

1. `POST /prompt` returns `202` with a generated `prompt_id`.
2. The job completes after `MOCK_PROMPT_DELAY_SECONDS` (default: `10`).
3. `POST /history` with `{"prompt_id": "..."}` returns:
   - `202` while pending
   - `200` when complete
   - `500` on failure

The service stores job history in `workers/mock/history_store.json` so IDs survive restarts.

## Local Run

Install requirements, then run both service and worker in separate terminals:

```bash
python -m workers.mock.service
python -m workers.mock.worker
```

Quick checks:

```bash
curl http://127.0.0.1:3010/health
curl -X POST http://127.0.0.1:3010/prompt
curl -X POST http://127.0.0.1:3010/history -H 'Content-Type: application/json' -d '{"prompt_id":"<id>"}'
```

## Serverless Startup

When `BACKEND=mock`, `start_server.sh` now starts `workers.mock.service`, waits for health, and then launches `workers.mock.worker`.
