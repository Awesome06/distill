"""Marp presentation compilation, slide density budgeting, and auto-pagination."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from distill.models.curriculum import TopicNode
from distill.models.slide import SlideChunk

GAIAN_MARP_HEADER = """---
marp: true
theme: gaia
_class: lead
paginate: true
backgroundColor: #fbfbfb
color: #1a1a1a
style: |
  .columns { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
  section { font-family: 'Inter', -apple-system, sans-serif; font-size: 26px; }
  h1 { font-size: 42px; color: #0f172a; }
  h2 { font-size: 34px; color: #1e293b; }
  footer { font-size: 14px; opacity: 0.6; }
---
"""


def split_slide_budget(
    title: str,
    bullets: list[str],
    max_bullets_per_slide: int = 4,
    max_chars_per_bullet: int = 65,
    notes: str = "",
) -> list[str]:
    """Split bullet points across multiple Marp slides if content exceeds viewport budget.

    Adheres to the strict slide density ceiling in ops/marp-deck-compiler:
    - 1 title
    - Maximum 4 bullets per slide
    - Maximum character length per bullet to prevent vertical overflow
    - Preserves presenter notes via `<!-- _notes: ... -->`

    Args:
        title: Main slide header.
        bullets: List of bullet point strings.
        max_bullets_per_slide: Max bullets per slide divider (default: 4).
        max_chars_per_bullet: Max length before clipping/wrapping.
        notes: Contextual speaker notes for Marp Presenter Mode.

    Returns:
        List of formatted slide markdown sections (separated by `---`).
    """
    if not bullets:
        slide = [f"## {title}"]
        if notes:
            slide.append(f"<!-- _notes: {notes} -->")
        return ["\n\n".join(slide)]

    slides: list[str] = []
    chunked_bullets = [
        bullets[i : i + max_bullets_per_slide]
        for i in range(0, len(bullets), max_bullets_per_slide)
    ]

    total_parts = len(chunked_bullets)
    for part_idx, group in enumerate(chunked_bullets, start=1):
        if total_parts == 1:
            slide_title = f"## {title}"
        else:
            slide_title = f"## {title} ({part_idx}/{total_parts})"
        slide_lines = [slide_title, ""]

        for b in group:
            clean_b = b.strip()
            if len(clean_b) > max_chars_per_bullet:
                clean_b = clean_b[: max_chars_per_bullet - 3] + "..."
            slide_lines.append(f"- {clean_b}")

        # Inject presenter notes into the first slide part
        if part_idx == 1 and notes:
            slide_lines.extend(["", f"<!-- _notes: {notes} -->"])

        slides.append("\n".join(slide_lines))

    return slides


def generate_marp_deck_markdown(
    topic: TopicNode,
    chunks: list[SlideChunk],
    chapter_num: int = 1,
) -> str:
    """Generate clean, auto-paginated Marp presentation markdown for a topic."""
    deck_slides: list[str] = [GAIAN_MARP_HEADER]

    # Title Slide
    title_slide = [
        f"# Chapter {chapter_num}\n## {topic.title}",
        f"**Module:** {topic.module_id} | **Exam Weight:** {int(topic.exam_weight * 100)}%",
    ]
    if topic.learning_objectives:
        objs_str = "; ".join(topic.learning_objectives)
        title_slide.append(f"<!-- _notes: Core objectives: {objs_str} -->")
    deck_slides.append("\n\n".join(title_slide))

    # Core Concepts & Slide Chunks
    for chunk in chunks:
        bullets = [line.strip("- *") for line in chunk.text_content.splitlines() if line.strip()]
        if not bullets and not chunk.tables and not chunk.mermaid_diagrams and not chunk.assets:
            continue

        chunk_title = chunk.title or topic.title

        # Bullets
        if bullets:
            paginated = split_slide_budget(
                title=chunk_title,
                bullets=bullets,
                notes=chunk.speaker_notes,
            )
            deck_slides.extend(paginated)

        # Standalone Table Slide
        for tbl in chunk.tables:
            table_slide = [
                f"## {chunk_title}: Comparison Matrix",
                "",
                tbl,
            ]
            deck_slides.append("\n".join(table_slide))

        # Standalone Diagram / Asset Slide
        for asset in chunk.assets:
            asset_slide = [
                f"## {chunk_title}: Architecture",
                "",
                f"![bg contain 80%]({asset.file_path})",
                f"<!-- _notes: Extracted figure from {chunk.slide_id} -->",
            ]
            deck_slides.append("\n".join(asset_slide))

    # Review & Exam Traps Slide
    summary_slide = [
        f"## {topic.title}: Key Exam Takeaways",
        "- Verify safety and liveness invariants before deployment",
        "- Pay attention to network partition edge cases",
        "- Confirm state durability requirements in WAL",
        "",
        "<!-- _notes: Review complete. Next step: active recall self-test. -->",
    ]
    deck_slides.append("\n".join(summary_slide))

    return "\n\n---\n\n".join(deck_slides)


def compile_marp_to_presentation(
    marp_markdown_path: Path,
    output_path: Path,
    output_format: str = "pptx",
) -> bool:
    """Compile a Marp Markdown file into .pptx or .pdf using headless Marp CLI if available.

    Returns:
        True if compilation succeeded; False if Marp CLI is not installed or execution failed.
    """
    marp_bin = shutil.which("marp")
    npx_bin = shutil.which("npx")

    cmd: list[str] = []
    if marp_bin:
        cmd = [marp_bin, str(marp_markdown_path), f"--{output_format}", "-o", str(output_path)]
    elif npx_bin:
        cmd = [
            npx_bin,
            "@marp-team/marp-cli",
            str(marp_markdown_path),
            f"--{output_format}",
            "-o",
            str(output_path),
        ]
    else:
        # Marp CLI is not locally installed; the .marp.md is preserved for the user
        return False

    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=60, check=False)
        return res.returncode == 0
    except Exception:
        return False
