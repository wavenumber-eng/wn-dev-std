"""Plan closeout assessment and explicit temporary-file removal."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from wn_dev_std.plan_hygiene import PlanCatalog, PlanRecord
from wn_dev_std.plan_reader import PlanReadContext

_READINESS_FAILURE_SUFFIXES = (
    ": all steps are done but plan is still active",
    ": all exit criteria are met but plan is still active",
)


class PlanCloseoutError(RuntimeError):
    """Raised when plan closeout cannot be safely assessed or applied."""


@dataclass(frozen=True, slots=True)
class PlanCloseoutAssessment:
    """Closeout readiness and the exact temporary files in scope."""

    plan_id: str
    root: Path
    plan_path: Path
    log_paths: tuple[Path, ...]
    step_count: int
    exit_criterion_count: int
    blockers: tuple[str, ...]

    @property
    def ready(self) -> bool:
        """Return whether the plan metadata is ready for closeout."""
        return not self.blockers


def assess_plan_closeout(context: PlanReadContext, plan_id: str) -> PlanCloseoutAssessment:
    """Assess whether a plan can be removed from the active plan catalog."""
    catalog = context.catalog
    plan = _required_plan(catalog, plan_id)
    unexpected_failures = _unexpected_catalog_failures(catalog.failures, plan.relative_path)
    if unexpected_failures:
        raise PlanCloseoutError("plan catalog is not compliant: " + "; ".join(unexpected_failures))

    blockers = _plan_state_blockers(plan)
    blockers.extend(_dependent_plan_blockers(catalog, plan_id))
    return PlanCloseoutAssessment(
        plan_id=plan_id,
        root=catalog.root,
        plan_path=_checked_catalog_path(catalog.root, plan.relative_path),
        log_paths=_plan_log_paths(catalog, plan_id),
        step_count=len(plan.steps),
        exit_criterion_count=len(plan.exit_criteria),
        blockers=tuple(blockers),
    )


def delete_closed_plan(assessment: PlanCloseoutAssessment) -> tuple[Path, ...]:
    """Delete the exact plan and attached log files after a ready assessment."""
    if not assessment.ready:
        raise PlanCloseoutError("plan is not ready for closeout")
    paths = (*assessment.log_paths, assessment.plan_path)
    _preflight_closeout_paths(assessment.root, paths)
    for path in paths:
        try:
            path.unlink()
        except OSError as exc:
            raise PlanCloseoutError(f"could not delete closeout file: {path}: {exc}") from exc
    return paths


def _required_plan(catalog: PlanCatalog, plan_id: str) -> PlanRecord:
    plan = next((item for item in catalog.plans if item.plan_id == plan_id), None)
    if plan is None:
        raise PlanCloseoutError(f"plan not found: {plan_id}")
    return plan


def _unexpected_catalog_failures(failures: tuple[str, ...], plan_path: str) -> tuple[str, ...]:
    return tuple(failure for failure in failures if not _is_readiness_failure(failure, plan_path))


def _is_readiness_failure(failure: str, plan_path: str) -> bool:
    return failure.startswith(f"{plan_path}:") and any(
        failure.endswith(suffix) for suffix in _READINESS_FAILURE_SUFFIXES
    )


def _plan_state_blockers(plan: PlanRecord) -> list[str]:
    blockers: list[str] = []
    if plan.status != "active":
        blockers.append(f"plan status must be active; currently {plan.status}")
    unfinished_steps = [step.step_id for step in plan.steps if step.status != "done"]
    if unfinished_steps:
        blockers.append("steps not done: " + ", ".join(unfinished_steps))
    unmet_criteria = [
        criterion.criterion_id for criterion in plan.exit_criteria if criterion.status != "met"
    ]
    if unmet_criteria:
        blockers.append("exit criteria not met: " + ", ".join(unmet_criteria))
    return blockers


def _dependent_plan_blockers(catalog: PlanCatalog, plan_id: str) -> list[str]:
    dependents = sorted(plan.plan_id for plan in catalog.plans if plan_id in plan.depends_on)
    if not dependents:
        return []
    return ["dependent plans still reference this plan: " + ", ".join(dependents)]


def _plan_log_paths(catalog: PlanCatalog, plan_id: str) -> tuple[Path, ...]:
    return tuple(
        _checked_catalog_path(catalog.root, log.relative_path)
        for log in catalog.logs
        if log.plan_id == plan_id
    )


def _checked_catalog_path(root: Path, relative_path: str) -> Path:
    resolved_root = root.resolve()
    path = resolved_root / relative_path
    try:
        path.resolve().relative_to(resolved_root)
    except (OSError, ValueError) as exc:
        raise PlanCloseoutError(f"closeout path escapes project root: {relative_path}") from exc
    return path


def _preflight_closeout_paths(root: Path, paths: tuple[Path, ...]) -> None:
    resolved_root = root.resolve()
    for path in paths:
        try:
            path.resolve().relative_to(resolved_root)
        except (OSError, ValueError) as exc:
            raise PlanCloseoutError(f"closeout path escapes project root: {path}") from exc
        if not path.exists():
            raise PlanCloseoutError(f"closeout file does not exist: {path}")
        if not path.is_file():
            raise PlanCloseoutError(f"closeout path is not a file: {path}")
