"""Deterministic regex noise scrubbing adhering to ai/multimodal-slide-ingestion."""

from __future__ import annotations

import re

# Common slide footers, page numbering, and copyright notices
BOILERPLATE_PATTERNS = [
    re.compile(r"^\s*(?:slide|page)\s*\d+\s*(?:of|/)\s*\d+\s*$", re.IGNORECASE),
    re.compile(r"^\s*\d+\s*/\s*\d+\s*$"),
    re.compile(r"^\s*(?:slide|page)\s*\d+\s*$", re.IGNORECASE),
    re.compile(r"(?i)^\s*(?:©|\(c\)|copyright).*$"),
    re.compile(r"(?i)^\s*(?:strictly\s+)?confidential\s*$"),
]

# Filler / transition slide titles that add noise
FILLER_SLIDE_TITLES = {
    "agenda",
    "table of contents",
    "overview",
    "q&a",
    "q & a",
    "questions",
    "questions?",
    "any questions?",
    "thank you",
    "thank you!",
    "thanks!",
    "break",
    "coffee break",
    "announcements",
    "wrap up",
    "summary of last lecture",
}


def is_filler_slide(title: str, text_content: str) -> bool:
    """Check if slide is purely a transition, agenda, or closing Q&A slide."""
    norm_title = title.strip().lower()
    if norm_title in FILLER_SLIDE_TITLES and len(text_content.strip().split()) <= 10:
        return True

    # If title is empty and text is just "Questions?" or "Thank You"
    norm_body = text_content.strip().lower()
    return norm_body in FILLER_SLIDE_TITLES


def clean_text_line(line: str) -> str:
    """Strip recurring boilerplate tokens from a text line."""
    cleaned = line.strip()
    for pattern in BOILERPLATE_PATTERNS:
        cleaned = pattern.sub("", cleaned).strip()
    return cleaned


def scrub_slide_text(raw_lines: list[str]) -> list[str]:
    """Clean and filter a list of text lines extracted from a slide."""
    cleaned_lines: list[str] = []
    for line in raw_lines:
        cleaned = clean_text_line(line)
        if cleaned and cleaned not in cleaned_lines:  # Deduplicate identical adjacent lines
            cleaned_lines.append(cleaned)
    return cleaned_lines
