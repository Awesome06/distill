"""Deterministic OpenXML AST connector and diagram parsing to Mermaid."""

from __future__ import annotations

import re
from typing import Any

# OpenXML namespaces
NS = {
    "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
}


def _safe_xpath(element: Any, query: str) -> list[Any]:
    """Execute xpath query supporting both python-pptx oxml elements and native lxml."""
    if not hasattr(element, "xpath"):
        return []
    try:
        return list(element.xpath(query, namespaces=NS))
    except TypeError:
        return list(element.xpath(query))


def sanitize_mermaid_label(text: str) -> str:
    """Sanitize shape text for inclusion in Mermaid node labels."""
    cleaned = re.sub(r"\s+", " ", text).strip()
    cleaned = cleaned.replace('"', "'").replace("[", "(").replace("]", ")")
    if len(cleaned) > 40:
        cleaned = cleaned[:37] + "..."
    return cleaned or "Step"


def extract_shape_text_map(slide_element: Any) -> dict[int, str]:
    """Map shape ID to extracted text from a slide XML element."""
    shape_texts: dict[int, str] = {}

    for sp in _safe_xpath(slide_element, ".//p:sp"):
        cNvPr = _safe_xpath(sp, ".//p:nvSpPr/p:cNvPr")
        if not cNvPr:
            continue
        try:
            shape_id = int(cNvPr[0].get("id", "0"))
        except ValueError:
            continue

        text_runs = _safe_xpath(sp, ".//p:txBody//a:t")
        text = " ".join([t.text for t in text_runs if t.text]).strip()
        if text:
            shape_texts[shape_id] = text

    return shape_texts


def parse_connector_ast_to_mermaid(slide_element: Any) -> str | None:
    """Inspect OpenXML <p:cxnSp> elements and deterministically generate a Mermaid diagram.

    Args:
        slide_element: lxml element of the slide (slide._element).

    Returns:
        Mermaid diagram string (e.g. ```mermaid\ngraph TD\n...```) or None if no connectors found.
    """
    connectors = _safe_xpath(slide_element, ".//p:cxnSp")
    if not connectors:
        return None

    shape_texts = extract_shape_text_map(slide_element)
    edges: list[tuple[int, int]] = []

    for cxn in connectors:
        st_cxn = _safe_xpath(cxn, ".//a:stCxn")
        end_cxn = _safe_xpath(cxn, ".//a:endCxn")
        if not st_cxn or not end_cxn:
            continue

        try:
            src_id = int(st_cxn[0].get("id", "0"))
            dst_id = int(end_cxn[0].get("id", "0"))
            if src_id and dst_id and src_id != dst_id:
                edges.append((src_id, dst_id))
        except ValueError:
            continue

    if not edges:
        return None

    # Construct Mermaid diagram
    lines = ["```mermaid", "graph TD"]
    seen_nodes: set[int] = set()

    for src_id, dst_id in edges:
        src_label = sanitize_mermaid_label(shape_texts.get(src_id, f"Node_{src_id}"))
        dst_label = sanitize_mermaid_label(shape_texts.get(dst_id, f"Node_{dst_id}"))

        src_node = f"N{src_id}"
        dst_node = f"N{dst_id}"

        if src_id not in seen_nodes:
            lines.append(f'    {src_node}["{src_label}"]')
            seen_nodes.add(src_id)

        if dst_id not in seen_nodes:
            lines.append(f'    {dst_node}["{dst_label}"]')
            seen_nodes.add(dst_id)

        lines.append(f"    {src_node} --> {dst_node}")

    lines.append("```")
    return "\n".join(lines)
