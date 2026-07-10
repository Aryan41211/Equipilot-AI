from __future__ import annotations

from typing import Optional


def coerce_max_report_length(
    value: int | float | str | None,
    *,
    default: int = 5000,
    min_value: int = 1000,
    max_value: int = 10000,
    step: int = 500,
) -> int:
    """
    UI-independent helper to normalize max_report_length into an allowed integer bucket.

    Prefer using UI widget ranges, but keep this defensive to preserve behavior.
    """
    try:
        if value is None:
            return default
        ivalue = int(float(value))
    except Exception:
        return default

    if ivalue < min_value:
        ivalue = min_value
    if ivalue > max_value:
        ivalue = max_value

    # Snap to step grid (best-effort).
    if step and step > 1:
        remainder = (ivalue - min_value) % step
        if remainder != 0:
            ivalue = ivalue - remainder
            if ivalue < min_value:
                ivalue = min_value

    return ivalue


def parse_tickers_csv(value: str | None, *, upper: bool = True) -> Optional[list[str]]:
    """
    Parse comma-separated tickers into list[str] or None.

    Pure function; no backend-specific validation.
    """
    if not value:
        return None

    tickers = [t.strip() for t in value.split(",") if t.strip()]
    if not tickers:
        return None

    if upper:
        tickers = [t.upper() for t in tickers]

    return tickers


def looks_like_ticker(value: str, *, max_len: int = 12) -> bool:
    """
    Best-effort heuristic used by the sidebar for deciding whether to pass tickers.

    Matches previous sidebar behavior:
      normalized = value.strip().upper()
      normalized.replace(".", "", 1).isalnum() and len(normalized) <= 12
    """
    normalized = (value or "").strip().upper()
    return normalized.replace(".", "", 1).isalnum() and len(normalized) <= max_len
