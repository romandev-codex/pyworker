import os

from vastai import BenchmarkConfig, HandlerConfig, LogActionConfig, Worker, WorkerConfig

# Keep defaults compatible with Vast runtime and local execution.
os.environ.setdefault("UNSECURED", "true")
WORKER_PORT = int(os.environ.get("WORKER_PORT", "3000"))
os.environ.setdefault("WORKER_PORT", str(WORKER_PORT))
os.environ.setdefault("CONTAINER_ID", "0")
os.environ.setdefault("REPORT_ADDR", "https://run.vast.ai")
os.environ.setdefault("PUBLIC_IPADDR", "0.0.0.0")
os.environ.setdefault("USE_SSL", "false")
os.environ.setdefault(f"VAST_TCP_PORT_{WORKER_PORT}", str(WORKER_PORT))

MODEL_SERVER_URL = os.environ.get("MODEL_SERVER_URL", "http://127.0.0.1")
MODEL_SERVER_PORT = int(os.environ.get("MODEL_SERVER_PORT", "3010"))
MODEL_LOG_FILE = os.environ.get("MODEL_LOG_FILE", "/var/log/portal/model.log")
MODEL_HEALTHCHECK_ENDPOINT = os.environ.get("MODEL_HEALTHCHECK_ENDPOINT", "/health")

# Vast requires benchmark data on at least one handler.
BENCHMARK_DATASET = [{"input": {"prompt": "benchmark"}}]

MODEL_LOAD_LOG_MSG = [
    "Uvicorn running on",
]

MODEL_ERROR_LOG_MSGS = [
    "Traceback (most recent call last):",
    "ERROR:",
]

MODEL_INFO_LOG_MSGS = [
    "Mock service",
]

worker_config = WorkerConfig(
    model_server_url=MODEL_SERVER_URL,
    model_server_port=MODEL_SERVER_PORT,
    model_log_file=MODEL_LOG_FILE,
    model_healthcheck_url=MODEL_HEALTHCHECK_ENDPOINT,
    handlers=[
        HandlerConfig(
            route="/health",
            allow_parallel_requests=True,
            max_queue_time=10.0,
        ),
        HandlerConfig(
            route="/prompt",
            allow_parallel_requests=True,
            max_queue_time=10.0,
            benchmark_config=BenchmarkConfig(dataset=BENCHMARK_DATASET),
            workload_calculator=lambda _: 1.0,
        ),
        HandlerConfig(
            route="/history",
            allow_parallel_requests=True,
            max_queue_time=10.0,
            workload_calculator=lambda _: 1.0,
        ),
    ],
    log_action_config=LogActionConfig(
        on_load=MODEL_LOAD_LOG_MSG,
        on_error=MODEL_ERROR_LOG_MSGS,
        on_info=MODEL_INFO_LOG_MSGS,
    ),
)

Worker(worker_config).run()
