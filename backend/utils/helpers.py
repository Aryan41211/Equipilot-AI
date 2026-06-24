# EquiPilot AI - Helper Utilities
# Common helper functions

import uuid
from datetime import datetime
from typing import Optional


def generate_request_id() -> str:
    """Generate a unique request ID."""
    return f"req_{uuid.uuid4().hex[:12]}"


def format_currency(value: Optional[float], currency: str = "USD") -> str:
    """Format a number as currency."""
    if value is None:
        return "N/A"

    if currency == "USD":
        if abs(value) >= 1e12:
            return f"${value/1e12:.2f}T"
        elif abs(value) >= 1e9:
            return f"${value/1e9:.2f}B"
        elif abs(value) >= 1e6:
            return f"${value/1e6:.2f}M"
        elif abs(value) >= 1e3:
            return f"${value/1e3:.2f}K"
        else:
            return f"${value:,.2f}"

    return f"{value:,.2f} {currency}"


def format_percentage(value: Optional[float], decimals: int = 2) -> str:
    """Format a number as percentage."""
    if value is None:
        return "N/A"
    return f"{value:.{decimals}f}%"


def format_large_number(value: Optional[float]) -> str:
    """Format large numbers with K/M/B/T suffixes."""
    if value is None:
        return "N/A"

    abs_val = abs(value)
    if abs_val >= 1e12:
        return f"{value/1e12:.2f}T"
    elif abs_val >= 1e9:
        return f"{value/1e9:.2f}B"
    elif abs_val >= 1e6:
        return f"{value/1e6:.2f}M"
    elif abs_val >= 1e3:
        return f"{value/1e3:.2f}K"
    else:
        return f"{value:.2f}"


def truncate_text(text: str, max_length: int = 200, suffix: str = "...") -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def parse_ticker_input(text: str) -> list:
    """Parse comma-separated ticker input."""
    return [t.strip().upper() for t in text.split(",") if t.strip()]


def calculate_processing_time(start: datetime, end: Optional[datetime] = None) -> float:
    """Calculate processing time in seconds."""
    if end is None:
        end = datetime.utcnow()
    return (end - start).total_seconds()