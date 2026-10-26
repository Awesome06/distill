"""Curriculum coverage audit generator identifying whiteboard lectures and gap topics."""

from __future__ import annotations

from pathlib import Path

from distill.models.curriculum import CoverageReport, CurriculumBackbone
from distill.models.slide import SlideChunk


def generate_coverage_report(
    backbone: CurriculumBackbone,
    mapping: dict[str, list[SlideChunk]],
    orphaned: list[SlideChunk],
) -> CoverageReport:
    """Generate a formal CoverageReport comparing syllabus requirements to covered slides."""
    all_topics = [t for mod in backbone.modules for t in mod.topics]
    total_topics = len(all_topics)

    covered_topics: list[str] = []
    uncovered_topics: list[str] = []

    for topic in all_topics:
        chunks = mapping.get(topic.id, [])
        if chunks:
            covered_topics.append(topic.id)
        else:
            uncovered_topics.append(topic.id)

    covered_count = len(covered_topics)
    uncovered_count = len(uncovered_topics)
    pct = (covered_count / total_topics * 100.0) if total_topics > 0 else 0.0

    return CoverageReport(
        total_syllabus_topics=total_topics,
        covered_topic_count=covered_count,
        uncovered_topic_count=uncovered_count,
        coverage_percentage=round(pct, 1),
        covered_topics=covered_topics,
        uncovered_topics=uncovered_topics,
        orphaned_slides=[c.slide_id for c in orphaned],
    )


def render_coverage_audit_markdown(
    backbone: CurriculumBackbone,
    report: CoverageReport,
    mapping: dict[str, list[SlideChunk]],
    output_path: Path | None = None,
) -> str:
    """Render a comprehensive coverage audit report in GitHub-Flavored Markdown."""
    lines: list[str] = [
        f"# Curriculum Coverage Audit: {backbone.course_code} {backbone.course_title}",
        "",
        "## Executive Summary",
        f"- **Total Syllabus Topics:** {report.total_syllabus_topics}",
        f"- **Covered Topics:** {report.covered_topic_count} ({report.coverage_percentage}%)",
        f"- **Uncovered Topics (Whiteboard Gaps):** {report.uncovered_topic_count}",
        f"- **Unmapped / Orphaned Slides:** {len(report.orphaned_slides)}",
        "",
    ]

    # Whiteboard gaps alert
    if report.uncovered_topics:
        lines.extend(
            [
                "> [!WARNING]",
                "> **Whiteboard Lecture Gaps Detected:** The following syllabus topics have ZERO "
                "matching slides in your lecture decks. These represent topics covered on the "
                "whiteboard, through homework, or via textbook readings. They will be synthesized "
                "using external RAG / textbook grounding.",
                "",
            ]
        )

        for top_id in report.uncovered_topics:
            lines.append(f"- **`{top_id}`**")
        lines.append("")

    # Topic-by-topic breakdown table
    lines.extend(
        [
            "## Syllabus Module Breakdown",
            "| Module | Topic Title | Status | Mapped Slide Count | Slide References |",
            "| :--- | :--- | :--- | :--- | :--- |",
        ]
    )

    for mod in backbone.modules:
        for topic in mod.topics:
            chunks = mapping.get(topic.id, [])
            status = "✅ Covered" if chunks else "⚠️ Whiteboard Gap"
            refs = ", ".join([f"`{c.slide_id}`" for c in chunks[:3]])
            if len(chunks) > 3:
                refs += f" +{len(chunks) - 3} more"
            lines.append(
                f"| {mod.title} | {topic.title} | {status} | {len(chunks)} | {refs or 'None'} |"
            )

    lines.append("")

    full_md = "\n".join(lines)
    if output_path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(full_md, encoding="utf-8")

    return full_md
