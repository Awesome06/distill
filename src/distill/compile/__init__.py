"""Marp presentation compilation module adhering to ops/marp-deck-compiler."""

from distill.compile.marp_compiler import (
    GAIAN_MARP_HEADER,
    compile_marp_to_presentation,
    generate_marp_deck_markdown,
    split_slide_budget,
)

__all__ = [
    "GAIAN_MARP_HEADER",
    "split_slide_budget",
    "generate_marp_deck_markdown",
    "compile_marp_to_presentation",
]
