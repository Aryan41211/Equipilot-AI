# EquiPilot AI - Validators
# Input validation utilities

import re
from datetime import datetime
from typing import Optional, List


# Common ticker pattern (1-5 uppercase letters, optionally with . or - for special classes)
TICKER_PATTERN = re.compile(r'^[A-Z]{1,5}(?:\.[A-Z]{1,2})?$')


def validate_ticker(ticker: str) -> bool:
    """Validate a ticker symbol format."""
    if not ticker:
        return False
    ticker = ticker.strip().upper()
    return bool(TICKER_PATTERN.match(ticker))


def validate_tickers(tickers: List[str]) -> List[str]:
    """Validate and normalize a list of tickers."""
    valid = []
    for t in tickers:
        t = t.strip().upper()
        if validate_ticker(t):
            valid.append(t)
    return valid


def validate_date_range(
    date_from: Optional[datetime],
    date_to: Optional[datetime],
    max_days: int = 365 * 5,  # 5 years
) -> tuple[bool, Optional[str]]:
    """Validate date range."""
    if date_from and date_to:
        if date_from > date_to:
            return False, "date_from must be before date_to"

        delta = date_to - date_from
        if delta.days > max_days:
            return False, f"Date range cannot exceed {max_days} days"

    if date_to and date_to > datetime.utcnow():
        return False, "date_to cannot be in the future"

    return True, None


def validate_query(query: str, min_length: int = 10, max_length: int = 2000) -> tuple[bool, Optional[str]]:
    """Validate research query."""
    if not query or not query.strip():
        return False, "Query cannot be empty"

    query = query.strip()
    if len(query) < min_length:
        return False, f"Query must be at least {min_length} characters"

    if len(query) > max_length:
        return False, f"Query cannot exceed {max_length} characters"

    return True, None


def sanitize_filename(name: str) -> str:
    """Sanitize a string for use as filename."""
    # Remove invalid characters
    name = re.sub(r'[<>:"/\\|?*]', '', name)
    # Replace spaces with underscores
    name = name.replace(' ', '_')
    # Limit length
    return name[:100]