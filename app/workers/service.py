"""Bounded in-process worker for long-running application operations."""

from concurrent.futures import Future
from dataclasses import dataclass
from threading import Lock
from typing import Any, Callable
from uuid import uuid4

from app.reliability import bounded_executor


@dataclass
class WorkerJob:
    """Observable state for one background operation."""

    job_id: str
    operation: str
    status: str = "queued"
    result: dict[str, Any] | None = None
    error: str | None = None


class WorkerService:
    """Run bounded background tasks with explicit job state transitions."""

    def __init__(self, max_workers: int = 4):
        self._executor = bounded_executor(max_workers)
        self._jobs: dict[str, WorkerJob] = {}
        self._futures: dict[str, Future[dict[str, Any]]] = {}
        self._lock = Lock()

    def submit(
        self,
        operation: str,
        task: Callable[[], dict[str, Any]],
    ) -> str:
        """Queue a task and return its job ID immediately."""
        job_id = str(uuid4())
        with self._lock:
            self._jobs[job_id] = WorkerJob(job_id=job_id, operation=operation)
            self._futures[job_id] = self._executor.submit(self._run, job_id, task)
        return job_id

    def get_status(self, job_id: str) -> dict[str, Any]:
        """Return a JSON-safe snapshot of a job."""
        with self._lock:
            job = self._jobs.get(job_id)
            if job is None:
                return {"job_id": job_id, "status": "not_found", "error": "unknown job"}
            return {
                "job_id": job.job_id,
                "operation": job.operation,
                "status": job.status,
                "result": job.result,
                "error": job.error,
            }

    def shutdown(self) -> None:
        """Stop accepting work and wait for queued work to finish."""
        self._executor.shutdown(wait=True, cancel_futures=True)

    def _run(self, job_id: str, task: Callable[[], dict[str, Any]]) -> dict[str, Any]:
        with self._lock:
            self._jobs[job_id].status = "running"
        try:
            result = task()
        except Exception as exc:
            with self._lock:
                self._jobs[job_id].status = "failed"
                self._jobs[job_id].error = str(exc)
            return {"error": str(exc)}
        with self._lock:
            self._jobs[job_id].status = "completed"
            self._jobs[job_id].result = result
        return result
