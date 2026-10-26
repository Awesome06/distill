"""Prompt envelopes and static cache prefix stabilization adhering to ai/token-cost-optimization."""

from __future__ import annotations

from distill.models.curriculum import TopicNode
from distill.models.slide import SlideChunk

# Static system instruction anchored at the start to maximize prompt cache hits
STATIC_PEDAGOGICAL_SYSTEM_PROMPT = """You are an expert author and professor.
Your role is to transform fragmented lecture bullets into an authoritative textbook chapter.

CRITICAL INVARIANTS:
1. First-Principles Intuition: Explain WHY the concept exists before introducing jargon.
2. Complete Theory: Supply full derivations, preconditions, invariants, and formulas.
3. Concrete Worked Examples: Every abstract concept MUST include a state-transition matrix.
4. Edge Cases: Include concrete failure modes, network partitions, and exam traps.
5. Strict Structure: Follow the 4-tier pedagogical contract and conclude with flashcards.
"""



def build_synthesis_prompt_payload(
    topic: TopicNode,
    chunks: list[SlideChunk],
    textbooks: list[str] | None = None,
) -> str:
    """Build dynamic prompt payload quarantined at the tail of the prompt to maximize cache hits."""
    lines: list[str] = [
        f"TARGET TOPIC: {topic.title} (ID: {topic.id})",
        f"MODULE: {topic.module_id}",
        f"PREREQUISITES: {', '.join(topic.prerequisites) or 'None'}",
        f"EXAM WEIGHT: {int(topic.exam_weight * 100)}%",
        f"ASSIGNED TEXTBOOKS: {', '.join(textbooks or []) or 'General Course References'}",
        "",
        "SYLLABUS LEARNING OBJECTIVES:",
    ]

    for obj in topic.learning_objectives:
        lines.append(f"- {obj}")

    lines.extend(
        [
            "",
            "SOURCE SLIDE CHUNKS (FRAGMENTED LECTURE BULLETS):",
        ]
    )

    if not chunks:
        lines.append(
            "(No slide chunks available: This is an uncovered Whiteboard Lecture topic. "
            "Synthesize the complete chapter from core textbook theory and learning objectives.)"
        )
    else:
        for chunk in chunks:
            lines.extend(
                [
                    f"--- SLIDE: {chunk.slide_id} ---",
                    f"Title: {chunk.title}",
                    f"Body Text:\n{chunk.text_content}",
                ]
            )
            if chunk.speaker_notes:
                lines.append(f"Speaker Notes: {chunk.speaker_notes}")
            if chunk.tables:
                lines.append("Tables:\n" + "\n".join(chunk.tables))
            if chunk.mermaid_diagrams:
                lines.append("Mermaid Diagrams:\n" + "\n".join(chunk.mermaid_diagrams))
            if chunk.assets:
                lines.append(f"Extracted Figures: {', '.join([a.file_path for a in chunk.assets])}")
            lines.append("")

    return "\n".join(lines)
