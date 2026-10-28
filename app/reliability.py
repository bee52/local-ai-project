"""Bounded retry, timeout, request-context, and concurrency primitives."""

from collections.abc import Callable, Iterable
from concurrent.futures import Future, ThreadPoolExecutor, TimeoutError
from contextvars import ContextVar
from dataclasses import dataclass
import logging
import time
from typing import TypeVar
from uuid import uuid4


logger = logging.getLogger(__name__)
Result = TypeVar("Result")
_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


@dataclass(frozen=True)
class RetryPolicy:
    """Limits transient retries and their exponential backoff."""

    max_retries: int = 2
    initial_delay_seconds: float = 0.25
    max_delay_seconds: float = 5.0
    retryable_exceptions: tuple[type[BaseException], ...] = (Exception,)


def run_with_retry(
    operation: Callable[[], Result],
    policy: RetryPolicy | None = None,
    sleep: Callable[[float], None] = time.sleep,
) -> Result:
    """Run an operation with bounded exponential backoff."""
    active_policy = policy or RetryPolicy()
    if active_policy.max_retries < 0:
        raise ValueError("max_retries must not be negative")
    for attempt in range(active_policy.max_retries + 1):
        try:
            return operation()
        except active_policy.retryable_exceptions as exc:
            if attempt == active_policy.max_retries:
                raise
            delay = min(
                active_policy.initial_delay_seconds * (2**attempt),
                active_policy.max_delay_seconds,
            )
            logger.warning(
                "Retrying failed operation",
                extra={"attempt": attempt + 1, "delay_seconds": delay},
            )
            sleep(delay)
    raise RuntimeError("retry loop exited unexpectedly")


def run_with_timeout(
    operation: Callable[[], Result],
    timeout_seconds: float,
    executor: ThreadPoolExecutor | None = None,
) -> Result:
    """Run a synchronous operation with a bounded wait time."""
    if timeout_seconds <= 0:
        raise ValueError("timeout_seconds must be greater than zero")
    owns_executor = executor is None
    active_executor = executor or ThreadPoolExecutor(max_workers=1)
    future: Future[Result] = active_executor.submit(operation)
    try:
        return future.result(timeout=timeout_seconds)
    except TimeoutError as exc:
        future.cancel()
        raise TimeoutError(
            f"operation exceeded {timeout_seconds} second timeout"
        ) from exc
    finally:
        if owns_executor:
            active_executor.shutdown(wait=False, cancel_futures=True)


def new_request_id() -> str:
    """Create and bind a request ID for the current execution context."""
    request_id = str(uuid4())
    _request_id.set(request_id)
    return request_id


def get_request_id() -> str | None:
    """Return the request ID bound to the current execution context."""
    return _request_id.get()


class RequestMetrics:
    """Capture elapsed time and outcome for one operation."""

    def __init__(self, operation: str):
        self.operation = operation
        self.started_at = time.perf_counter()
        self.elapsed_seconds: float | None = None

    def finish(self, success: bool) -> float:
        """Finish the measurement and emit a structured completion event."""
        self.elapsed_seconds = time.perf_counter() - self.started_at
        logger.info(
            "Operation completed",
            extra={
                "operation": self.operation,
                "elapsed_seconds": self.elapsed_seconds,
                "success": success,
            },
        )
        return self.elapsed_seconds


def bounded_executor(max_workers: int) -> ThreadPoolExecutor:
    """Create an explicitly bounded executor for embedding or worker tasks."""
    if max_workers < 1:
        raise ValueError("max_workers must be at least one")
    return ThreadPoolExecutor(max_workers=max_workers)
