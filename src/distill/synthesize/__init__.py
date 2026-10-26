"""Pedagogical synthesis module adhering to ai/pedagogical-synthesis."""

from distill.synthesize.chapter import synthesize_all_chapters
from distill.synthesize.master_index import generate_master_index_markdown
from distill.synthesize.prompt import (
    STATIC_PEDAGOGICAL_SYSTEM_PROMPT,
    build_synthesis_prompt_payload,
)
from distill.synthesize.template import render_chapter_scaffold

__all__ = [
    "render_chapter_scaffold",
    "STATIC_PEDAGOGICAL_SYSTEM_PROMPT",
    "build_synthesis_prompt_payload",
    "generate_master_index_markdown",
    "synthesize_all_chapters",
]
