"""Utilities for cleaning and exporting NEXUS AI reports."""

import re
from datetime import datetime


def clean_markdown(content: str) -> str:
    """Clean unwanted artifacts from generated Markdown."""

    if not isinstance(content, str):
        raise TypeError("Report content must be a string.")

    content = content.strip()

    # Remove unwanted localhost SVG heading-anchor artifacts.
    content = re.sub(
        r"\[svg\]\(https?://localhost(?::\d+)?/#[^)]+\)",
        "",
        content,
        flags=re.IGNORECASE,
    )

    # Normalize excessive blank lines.
    content = re.sub(r"\n{3,}", "\n\n", content)

    return content.strip()


def export_markdown(
    title: str,
    content: str,
    include_timestamp: bool = True,
) -> str:
    """Create a clean Markdown report."""

    if not title or not title.strip():
        raise ValueError("Report title cannot be empty.")

    cleaned_content = clean_markdown(content)

    if not cleaned_content:
        raise ValueError("Report content cannot be empty.")

    sections = [f"# {title.strip()}", ""]

    if include_timestamp:
        timestamp = datetime.now().astimezone().strftime(
            "%Y-%m-%d %H:%M:%S %Z"
        )
        sections.extend([f"**Exported:** {timestamp}", ""])

    sections.extend(["---", "", cleaned_content, ""])

    return "\n".join(sections)