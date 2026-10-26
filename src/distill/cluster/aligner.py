"""Slide-to-syllabus alignment and cross-deck topic classification."""

from __future__ import annotations

import re

from distill.models.curriculum import CurriculumBackbone, TopicNode
from distill.models.slide import SlideChunk


def _tokenize(text: str) -> set[str]:
    """Tokenize text into lowercase alphanumeric keywords."""
    words = re.findall(r"\b[a-zA-Z0-9_-]{3,}\b", text.lower())
    # Exclude common stop words
    stop_words = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "have",
        "not",
        "are",
        "was",
        "will",
        "each",
        "which",
    }
    return {w for w in words if w not in stop_words}


def compute_alignment_score(chunk: SlideChunk, topic: TopicNode) -> float:
    """Compute heuristic alignment score between a slide chunk and a syllabus topic.

    Score components:
    - Exact/partial title match: 5.0x
    - Learning objective keyword overlap: 2.0x
    - Body text to topic keyword overlap: 1.0x
    """
    chunk_title_tokens = _tokenize(chunk.title)
    topic_title_tokens = _tokenize(topic.title)

    score = 0.0

    # 1. Title token intersection
    title_overlap = len(chunk_title_tokens & topic_title_tokens)
    if title_overlap > 0:
        score += title_overlap * 5.0

    # 2. Objective keyword overlap
    obj_tokens: set[str] = set()
    for obj in topic.learning_objectives:
        obj_tokens |= _tokenize(obj)

    chunk_body_tokens = _tokenize(chunk.text_content)
    obj_overlap = len(chunk_body_tokens & obj_tokens)
    score += obj_overlap * 2.0

    # 3. Reading and topic title tokens in chunk body
    score += len(chunk_body_tokens & topic_title_tokens) * 1.5

    return score


def align_slides_to_curriculum(
    chunks: list[SlideChunk],
    backbone: CurriculumBackbone,
    min_score_threshold: float = 2.0,
) -> tuple[dict[str, list[SlideChunk]], list[SlideChunk]]:
    """Classify and map all extracted slide chunks across decks to canonical syllabus topics.

    Args:
        chunks: List of SlideChunk objects extracted from all incoming decks.
        backbone: The authoritative CurriculumBackbone.
        min_score_threshold: Minimum alignment score to map a slide.

    Returns:
        Tuple of:
          - topic_id -> list of mapped SlideChunk objects
          - list of orphaned / unmapped SlideChunk objects
    """
    all_topics: list[TopicNode] = []
    for mod in backbone.modules:
        all_topics.extend(mod.topics)

    mapping: dict[str, list[SlideChunk]] = {t.id: [] for t in all_topics}
    orphaned: list[SlideChunk] = []

    for chunk in chunks:
        best_score = 0.0
        best_topic: TopicNode | None = None

        for topic in all_topics:
            score = compute_alignment_score(chunk, topic)
            if score > best_score:
                best_score = score
                best_topic = topic

        if best_topic and best_score >= min_score_threshold:
            mapping[best_topic.id].append(chunk)
            if chunk.slide_id not in best_topic.mapped_slide_ids:
                best_topic.mapped_slide_ids.append(chunk.slide_id)
        else:
            orphaned.append(chunk)

    return mapping, orphaned
