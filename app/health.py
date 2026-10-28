"""Dependency health primitives used by future API and worker entry points."""

import logging
from collections.abc import Callable, Iterable

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


def readiness_health_check(checks: Iterable[HealthCheck]) -> HealthStatus:
    """Aggregate dependency checks into a readiness result."""
    statuses = run_health_checks(checks)
    unhealthy = [status.name for status in statuses if not status.healthy]
    if unhealthy:
        return HealthStatus(
            name="readiness",
            healthy=False,
            detail=f"unhealthy dependencies: {', '.join(unhealthy)}",
        )
    return HealthStatus(name="readiness", healthy=True, detail="dependencies ready")
