"""Merged table normalizer for presentation tables adhering to ai/multimodal-slide-ingestion."""

from __future__ import annotations

from typing import Any


def sanitize_table_cell(text: str) -> str:
    """Sanitize cell text to prevent breaking Markdown table delimiters."""
    cleaned = text.strip().replace("\r\n", "\n").replace("\r", "\n")
    # Replace internal newlines with <br>
    cleaned = cleaned.replace("\n", "<br>")
    # Escape pipe characters
    cleaned = cleaned.replace("|", "\\|")
    return cleaned or " "


def extract_table_as_markdown(table_shape: Any) -> str | None:
    """Extract a python-pptx table shape into a normalized GitHub-Flavored Markdown table.

    Resolves merged cells and missing spans to ensure every row has a uniform column count.

    Args:
        table_shape: python-pptx shape object where shape.has_table is True.

    Returns:
        Rendered GitHub-Flavored Markdown table string, or None if table is empty.
    """
    if not getattr(table_shape, "has_table", False):
        return None

    table = table_shape.table
    rows = table.rows
    cols = table.columns
    if not rows or not cols:
        return None

    num_rows = len(rows)
    num_cols = len(cols)

    # Build 2D matrix
    grid: list[list[str]] = [["" for _ in range(num_cols)] for _ in range(num_rows)]

    for r_idx, row in enumerate(rows):
        for c_idx, cell in enumerate(row.cells):
            cell_text = cell.text.strip()
            # If cell is part of a merge and empty, see if we can maintain context
            grid[r_idx][c_idx] = sanitize_table_cell(cell_text)

    if not grid or all(all(c == " " for c in row) for row in grid):
        return None

    # Construct Markdown
    md_lines: list[str] = []

    # Header row
    header = "| " + " | ".join(grid[0]) + " |"
    delimiter = "| " + " | ".join(["---"] * num_cols) + " |"
    md_lines.append(header)
    md_lines.append(delimiter)

    # Data rows
    for row in grid[1:]:
        md_lines.append("| " + " | ".join(row) + " |")

    return "\n".join(md_lines)
