import time

import pytest

from app.health import readiness_health_check
from app.models import HealthStatus
from app.reliability import RetryPolicy, run_with_retry, run_with_timeout
from app.workers.service import WorkerService


def test_retry_policy_retries_then_returns():
    attempts = 0

    def operation():
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ValueError("temporary")
        return "ready"

    assert run_with_retry(
        operation,
        RetryPolicy(max_retries=2, initial_delay_seconds=0, max_delay_seconds=0),
        sleep=lambda _: None,
    ) == "ready"
    assert attempts == 3


def test_timeout_and_readiness_failure():
    with pytest.raises(TimeoutError):
        run_with_timeout(lambda: time.sleep(0.05), 0.001)
    result = readiness_health_check([lambda: HealthStatus("ollama", False, "offline")])
    assert not result.healthy
    assert "ollama" in result.detail


def test_worker_reports_failed_job():
    worker = WorkerService(1)
    try:
        job_id = worker.submit("test", lambda: (_ for _ in ()).throw(ValueError("bad")))
        for _ in range(100):
            status = worker.get_status(job_id)
            if status["status"] in {"completed", "failed"}:
                break
            time.sleep(0.005)
        assert status["status"] == "failed"
        assert status["error"] == "bad"
    finally:
        worker.shutdown()