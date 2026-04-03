"""Mock model service used by the mock PyWorker backend.

Run locally:
  uvicorn workers.mock.service:app --host 0.0.0.0 --port 3010 --reload

Quick test:
  curl http://127.0.0.1:3010/health
  curl -X POST http://127.0.0.1:3010/prompt
  curl "http://127.0.0.1:3010/history?prompt_id=<prompt-id>"
"""

import asyncio
import json
import os
import uuid
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse

app = FastAPI()

# Persist history on disk so IDs survive reload/restart.
HISTORY_FILE = Path(__file__).with_name("history_store.json")
DEFAULT_DELAY_SECONDS = float(os.environ.get("MOCK_PROMPT_DELAY_SECONDS", "10"))

history_store: dict[str, dict[str, Any]] = {}
history_store_lock = asyncio.Lock()


def load_history_store() -> dict[str, dict[str, Any]]:
    if not HISTORY_FILE.exists():
        return {}

    try:
        with HISTORY_FILE.open("r", encoding="utf-8") as file_obj:
            data = json.load(file_obj)
            if isinstance(data, dict):
                return data
    except Exception:
        pass

    return {}


def save_history_store() -> None:
    with HISTORY_FILE.open("w", encoding="utf-8") as file_obj:
        json.dump(history_store, file_obj, ensure_ascii=True, indent=2)


async def set_prompt_state(prompt_id: str, status: str, result: Any) -> None:
    async with history_store_lock:
        history_store[prompt_id] = {
            "status": status,
            "result": result,
        }
        save_history_store()


async def get_prompt_state(prompt_id: str) -> dict[str, Any] | None:
    async with history_store_lock:
        return history_store.get(prompt_id)


def build_history_response(prompt_id: str, state: dict[str, Any]) -> JSONResponse:
    payload = {
        "prompt_id": prompt_id,
        **state,
    }

    status = state.get("status")
    if status == "completed":
        return JSONResponse(status_code=200, content=payload)
    if status == "pending":
        return JSONResponse(status_code=202, content=payload)
    if status == "failed":
        return JSONResponse(status_code=500, content=payload)

    return JSONResponse(status_code=202, content=payload)


async def resolve_history(prompt_id: str) -> JSONResponse:
    normalized_prompt_id = prompt_id.strip()
    if not normalized_prompt_id:
        raise HTTPException(status_code=400, detail="prompt_id is required")

    state = await get_prompt_state(normalized_prompt_id)
    if state is None:
        raise HTTPException(status_code=404, detail="Prompt ID not found")

    return build_history_response(normalized_prompt_id, state)


@app.on_event("startup")
async def startup_event() -> None:
    global history_store
    history_store = load_history_store()


async def run_prompt_task(prompt_id: str) -> None:
    try:
        # Simulate a long-running model task.
        await asyncio.sleep(DEFAULT_DELAY_SECONDS)
        await set_prompt_state(
            prompt_id,
            "completed",
            f"command finished for {prompt_id}",
        )
    except Exception as exc:
        await set_prompt_state(prompt_id, "failed", str(exc))


def handler(request: Any) -> dict[str, Any]:
    # Minimal mock response contract expected by the worker.
    return {
        "status": "success",
        "output": {
            "text": "mock response",
        },
    }


@app.get("/health")
async def status() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/prompt")
async def prompt(payload: dict[str, Any] | None = None) -> dict[str, Any]:
    return handler(payload or {})


@app.get("/history/{prompt_id}")
async def get_history_path(prompt_id: str) -> JSONResponse:
    return await resolve_history(prompt_id)


@app.get("/history")
async def get_history_query(prompt_id: str) -> JSONResponse:
    return await resolve_history(prompt_id)


@app.post("/history")
async def post_history_query(payload: dict[str, Any]) -> JSONResponse:
    prompt_id = str(payload.get("prompt_id", ""))
    return await resolve_history(prompt_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("MODEL_SERVER_PORT", "3010")),
        reload=os.environ.get("MOCK_SERVICE_RELOAD", "false").lower() == "true",
    )
