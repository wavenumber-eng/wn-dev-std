"""Cross-cutting standard capabilities independent of language profiles."""

from __future__ import annotations

from collections.abc import Callable
from typing import Literal

from wn_dev_std.activity_standard_data import (
    ACTIVITY_APPLICATION_REQUIRED_DOCS,
    ACTIVITY_APPLICATION_RULE_ITEMS,
)
from wn_dev_std.backend_standard_data import (
    BACKEND_INTEGRATION_REQUIRED_DOCS,
    BACKEND_INTEGRATION_RULE_ITEMS,
)
from wn_dev_std.standard_model import (
    STANDARD_VERSION,
    CapabilityName,
    PythonStandard,
    StrictRule,
)
from wn_dev_std.standard_rendering import render_standard_data
from wn_dev_std.typespec_standard_data import (
    TYPESPEC_CONTRACT_REQUIRED_DOCS,
    TYPESPEC_CONTRACT_RULE_ITEMS,
)
from wn_dev_std.web_application_standard_data import (
    LIT_WEB_APPLICATION_REQUIRED_DOCS,
    LIT_WEB_APPLICATION_RULE_ITEMS,
)


def default_typespec_contract_standard() -> PythonStandard:
    """Return the cross-cutting TypeSpec contract-authority standard."""
    return _capability(
        "typespec-contracts",
        TYPESPEC_CONTRACT_RULE_ITEMS,
        TYPESPEC_CONTRACT_REQUIRED_DOCS,
    )


def default_activity_application_standard() -> PythonStandard:
    """Return the platform-neutral activity application standard."""
    return _capability(
        "activity-application",
        ACTIVITY_APPLICATION_RULE_ITEMS,
        ACTIVITY_APPLICATION_REQUIRED_DOCS,
    )


def default_backend_integration_standard() -> PythonStandard:
    """Return the centralized backend-client integration standard."""
    return _capability(
        "backend-integration",
        BACKEND_INTEGRATION_RULE_ITEMS,
        BACKEND_INTEGRATION_REQUIRED_DOCS,
    )


def default_lit_web_application_standard() -> PythonStandard:
    """Return the preferred Lit web-application standard."""
    return _capability(
        "lit-web-application",
        LIT_WEB_APPLICATION_RULE_ITEMS,
        LIT_WEB_APPLICATION_REQUIRED_DOCS,
    )


def default_capability(capability: CapabilityName) -> PythonStandard:
    """Return a cross-cutting standard capability."""
    factories: dict[str, Callable[[], PythonStandard]] = {
        "typespec-contracts": default_typespec_contract_standard,
        "activity-application": default_activity_application_standard,
        "backend-integration": default_backend_integration_standard,
        "lit-web-application": default_lit_web_application_standard,
    }
    try:
        return factories[capability]()
    except KeyError as exc:
        raise ValueError(f"unsupported capability: {capability}") from exc


def render_typespec_contract_standard(output_format: Literal["text", "json"] = "text") -> str:
    """Render the cross-cutting TypeSpec contract standard."""
    return render_standard_data(default_typespec_contract_standard(), output_format)


def render_activity_application_standard(output_format: Literal["text", "json"] = "text") -> str:
    """Render the platform-neutral activity application standard."""
    return render_standard_data(default_activity_application_standard(), output_format)


def render_backend_integration_standard(output_format: Literal["text", "json"] = "text") -> str:
    """Render the centralized backend-client integration standard."""
    return render_standard_data(default_backend_integration_standard(), output_format)


def render_lit_web_application_standard(output_format: Literal["text", "json"] = "text") -> str:
    """Render the preferred Lit web-application standard."""
    return render_standard_data(default_lit_web_application_standard(), output_format)


def render_capability(
    capability: CapabilityName,
    output_format: Literal["text", "json"] = "text",
) -> str:
    """Render a cross-cutting standard capability."""
    return render_standard_data(default_capability(capability), output_format)


def _capability(
    name: CapabilityName,
    rule_items: tuple[tuple[str, str, str], ...],
    required_docs: tuple[str, ...],
) -> PythonStandard:
    return PythonStandard(
        name=name,
        version=STANDARD_VERSION,
        status="initial",
        rules=tuple(StrictRule(*item) for item in rule_items),
        required_files=(),
        required_docs=required_docs,
    )
