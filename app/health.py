"""Dependency health primitives used by future API and worker entry points."""

from collections.abc import Callable, Iterable
import logging

from app.models import HealthStatus


logger = logging.getLogger(__name__)
HealthCheck = Callable[[], HealthStatus]


def run_health_checks(checks: Iterable[HealthCheck]) -> tuple[HealthStatus, ...]:
    """Run checks independently so one unavailable dependency cannot hide others."""
    statuses: list[HealthStatus] = []
    for check in checks:
        try:
            statuses.append(check())
        except Exception as exc:
            logger.exception("Health check failed", extra={"check": check.__name__})
            statuses.append(
                HealthStatus(
                    name=check.__name__,
                    healthy=False,
                    detail=str(exc),
                )
            )
    return tuple(statuses)


def process_health_check() -> HealthStatus:
    """Return a liveness result without contacting external services."""
    return HealthStatus(name="process", healthy=True, detail="process is running")
