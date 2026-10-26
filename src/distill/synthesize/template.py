"""Pedagogical chapter template adhering to ai/pedagogical-synthesis and repo-wiki."""

from __future__ import annotations

from distill.models.curriculum import TopicNode
from distill.models.slide import SlideChunk


def render_chapter_scaffold(
    topic: TopicNode,
    chunks: list[SlideChunk],
    chapter_num: int = 1,
    course_code: str = "",
) -> str:
    """Generate the authoritative 4-tier pedagogical chapter scaffold for a topic.

    Structure:
    - YAML Frontmatter (topic metadata, prerequisites, exam weighting)
    - Interactive Syllabus Mastery Checklist
    - Canonical Terminology & Synonym Mapping
    - Tier 1: First-Principles Intuition (Problem it solves, physical analogy)
    - Tier 2: Formal Theory & Derivation (Invariants, formal guarantees)
    - Tier 3: Concrete Worked Examples with State-Trace Matrices & Embedded Assets
    - Tier 4: Edge Cases & Exam Traps (Boundary conditions, failure modes)
    - Active Recall Flashcard Deck (High-yield Q&A pairs)
    """
    slide_refs = ", ".join([f"`{c.slide_id}`" for c in chunks]) or "None (Whiteboard RAG)"
    prereq_refs = ", ".join([f"[[{p}]]" for p in topic.prerequisites]) or "None"

    # Frontmatter
    lines: list[str] = [
        "---",
        f"id: {topic.id}",
        f"title: {topic.title}",
        f"module: {topic.module_id}",
        f"chapter_number: {chapter_num}",
        f"course: {course_code}",
        f"exam_weight: {int(topic.exam_weight * 100)}%",
        f"prerequisites: [{', '.join(topic.prerequisites)}]",
        f"source_slides: [{', '.join([c.slide_id for c in chunks])}]",
        "---",
        "",
        f"# Chapter {chapter_num}: {topic.title}",
        "",
        f"**Prerequisites:** {prereq_refs} | **Exam Weight:** {int(topic.exam_weight * 100)}%",
        f"**Source Slide Chunks:** {slide_refs}",
        "",
        "## Syllabus Mastery Checklist",
    ]

    # Checklist
    if topic.learning_objectives:
        for idx, obj in enumerate(topic.learning_objectives, start=1):
            lines.append(f"- [ ] **Objective {idx}:** {obj} (See Section {chapter_num}.{idx})")
    else:
        lines.append("- [ ] **Objective 1:** Master core theoretical invariants and edge cases.")
    lines.append("")

    # Terminology Table
    lines.extend(
        [
            "## Canonical Terminology & Synonym Alignment",
            "| Standard Term | Alternative / Slide Term | Scope & Context |",
            "| :--- | :--- | :--- |",
            f"| {topic.title} | {topic.title} | Core concept as defined in course syllabus |",
            "",
        ]
    )

    # Tier 1
    lines.extend(
        [
            "---",
            "",
            "## 1. First-Principles Intuition",
            f"> **Why does {topic.title} exist?**",
            "",
            (
                f"Before diving into formal protocols, understand the core problem {topic.title} "
                "solves. In distributed systems, networks are asynchronous, "
                "messages are delayed, and independent failures are inevitable."
            ),
            "",
        ]
    )

    # Tier 2
    lines.extend(
        [
            "---",
            "",
            "## 2. Formal Theory & Mathematical Formulation",
            "### 2.1 Core Invariants & Safety Guarantees",
            "A system implementing this protocol must guarantee the following invariants under all "
            "non-Byzantine conditions:",
            "",
            "- **Safety Invariant:** Nothing bad happens (e.g. no conflicting leader elected).",
            "- **Liveness Invariant:** Something good eventually happens (e.g. state advances).",
            "",
        ]
    )


    # Incorporate slide tables or equations if present
    for chunk in chunks:
        for tbl in chunk.tables:
            lines.extend([f"### Slide Table ({chunk.slide_id})", tbl, ""])
        for diag in chunk.mermaid_diagrams:
            lines.extend([f"### Architecture Flowchart ({chunk.slide_id})", diag, ""])

    # Tier 3: Worked Examples & State Trace
    lines.extend(
        [
            "---",
            "",
            "## 3. Concrete Worked Examples & State-Trace Walkthrough",
            "### 3.1 Step-by-Step State Transition Matrix",
            "The following trace illustrates the step-by-step state changes during execution:",
            "",
            "| Step | Event / Stimulus | Node State | Buffer / Network | Invariant Check |",
            "| :--- | :--- | :--- | :--- | :--- |",
            "| 1 | Initial State | INIT / IDLE | Empty | Valid |",
            "| 2 | Stimulus Triggered | PROCESSING | [Msg: Prepare] | Safety Preserved |",
            "| 3 | State Committed | COMMITTED | [Msg: Ack] | Quorum Satisfied |",
            "",
        ]
    )

    # Embed visual slide assets
    all_assets = [a for c in chunks for a in c.assets]
    if all_assets:
        lines.append("### 3.2 Visual Slide Assets & Architectural Diagrams")
        for asset in all_assets:
            lines.extend(
                [
                    f"![{asset.asset_id}]({asset.file_path})",
                    f"*Figure: Architectural diagram extracted from `{asset.asset_id}`.*",
                    "",
                ]
            )

    # Tier 4: Edge Cases & Traps
    lines.extend(
        [
            "---",
            "",
            "## 4. Edge Cases & Exam Traps",
            (
                f"- **Trap 1 (Network Partition):** How does {topic.title} behave when a "
                "minority partition is isolated?"
            ),
            (
                "- **Trap 2 (Concurrent Conflicts):** What happens if competing operations arrive "
                "with identical terms?"
            ),
            (
                "- **Trap 3 (Crash Recovery):** Which state must be written to stable storage "
                "before acknowledging messages?"
            ),
            "",
        ]
    )

    # Active Recall Flashcards
    lines.extend(
        [
            "---",
            "",
            "## 5. Active Recall Flashcard Deck (Spaced Repetition)",
            "Use these prompt-answer pairs for self-testing in Anki or verbal rehearsal:",
            "",
            f"**Q1:** What is the primary problem solved by {topic.title}?",
            (
                "**A1:** Correctness guarantees under asynchronous delays "
                "and partial node crashes."
            ),
            "",
            "**Q2:** Distinguish between the safety and liveness invariants of this protocol.",
            (
                "**A2:** Safety guarantees no conflicting invalid states occur; "
                "Liveness guarantees progress."
            ),
            "",
            "**Q3:** What is the consequence of failing to persist state before responding?",
            (
                "**A3:** A node may crash, restart, and violate previously granted promises "
                "or quorum agreements."
            ),
            "",
        ]
    )

    return "\n".join(lines)

