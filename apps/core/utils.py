"""Utility helpers for CivicFlow platform."""

import os
import random
import string
from datetime import datetime
from django.utils import timezone


def generate_complaint_reference():
    """
    Generate unique human-readable complaint reference number:
    Format: CF-YYYYMMDD-XXXX (e.g., CF-20260910-K8P2)
    """
    date_str = timezone.now().strftime("%Y%m%d")
    chars = string.ascii_uppercase + string.digits
    # Remove ambiguous characters like 0, O, 1, I
    cleaned_chars = chars.translate(str.maketrans('', '', '0O1I'))
    random_code = ''.join(random.choices(cleaned_chars, k=4))
    return f"CF-{date_str}-{random_code}"


def sanitize_filename(instance, filename):
    """
    Clean and build secure upload path for attachments.
    Stores as uploads/{model_name}/{year}/{month}/{uuid}_{filename}
    """
    ext = os.path.splitext(filename)[1].lower()
    clean_name = "".join([c for c in os.path.splitext(filename)[0] if c.isalnum() or c in ('-', '_')]).strip()
    if not clean_name:
        clean_name = "evidence"
    timestamp = timezone.now().strftime("%Y%m%d%H%M%S")
    random_str = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    model_dir = instance.__class__.__name__.lower()
    return os.path.join('uploads', model_dir, timezone.now().strftime("%Y/%m"), f"{clean_name}_{timestamp}_{random_str}{ext}")


def format_duration(seconds):
    """Convert seconds into human-readable hours and minutes string."""
    if seconds is None:
        return "N/A"
    is_negative = seconds < 0
    total_sec = abs(int(seconds))
    hours = total_sec // 3600
    minutes = (total_sec % 3600) // 60
    prefix = "-" if is_negative else ""
    if hours > 24:
        days = hours // 24
        remaining_hours = hours % 24
        return f"{prefix}{days}d {remaining_hours}h"
    return f"{prefix}{hours}h {minutes}m"
