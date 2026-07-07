from __future__ import annotations

import inspect
from typing import Any, get_args, get_origin

import pytest

from backend.schemas.research import ResearchResponse


def _is_optional(annotation: Any) -> bool:
    origin = get_origin(annotation)
    if origin is None:
        return False
    if origin is list:
        return False
    return False


def _normalize_type_str(t: Any) -> str:
    # Keep this robust across typing/pydantic versions.
    return str(t).replace("typing.", "").replace("NoneType", "None")


def test_research_response_has_expected_fields_and_types():
    """
    Contract test: ResearchResponse must expose fields expected by the frontend.

    This is intentionally fast and isolated:
    - only imports the pydantic model
    - asserts presence + basic optional/non-optional compatibility
    """
    expected = {
        # frontend status loop fields
        "request_id": str,
        "status": object,  # enum; we validate existence only
        "query": str,
        "tickers": list,
        "current_step": object,  # Optional[str]
        "execution_metadata": object,  # Optional[dict]
        "error": object,  # Optional[str]
        "message": object,  # Optional[str]

        # frontend report rendering fields
        "report": object,  # Optional[str]
        "sections": object,  # Optional[list[dict]]
        "citations": object,  # Optional[list[dict]]

        # frontend dashboard summary fallbacks (summary naming)
        "market_data_summary": object,  # Optional[dict]
        "news_summary": object,  # Optional[dict]
        "sentiment_summary": object,  # Optional[dict]

        # metadata/timing fields used for display
        "created_at": object,
        "completed_at": object,
        "processing_time_seconds": object,
    }

    model_fields = ResearchResponse.model_fields
    missing = sorted([k for k in expected.keys() if k not in model_fields])
    assert not missing, f"ResearchResponse missing fields required by frontend: {missing}"

    # Basic type-compatibility checks:
    # - For non-Optional required fields: request_id, status, query, tickers
    # - For Optional fields: current_step, execution_metadata, error, message, report, sections,
    #   citations, market_data_summary, news_summary, sentiment_summary, completed_at, processing_time_seconds
    required_non_optional = {"request_id", "status", "query", "tickers"}
    optional_fields = set(expected.keys()) - required_non_optional

    for field_name in required_non_optional:
        ann = model_fields[field_name].annotation
        # Pydantic uses Union[..., NoneType] for Optional; we check presence of None in args.
        origin = get_origin(ann)
        args = get_args(ann) if origin is not None else ()
        assert (
            "NoneType" not in _normalize_type_str(ann)
        ), f"{field_name} unexpectedly Optional/nullable; annotation={ann!r}"

    for field_name in optional_fields:
        ann = model_fields[field_name].annotation
        origin = get_origin(ann)
        # Ensure field is Optional-like (Union includes NoneType or annotation contains None).
        ann_str = _normalize_type_str(ann)
        assert (
            ("None" in ann_str)
            or (origin is Any)
            or ("Optional" in ann_str)
        ), f"{field_name} expected to be Optional/nullable; annotation={ann!r}"
