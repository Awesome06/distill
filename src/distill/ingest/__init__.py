"""Ingestion module for slide presentations adhering to ai/multimodal-slide-ingestion."""

from distill.ingest.assets import carve_shape_asset
from distill.ingest.cleaner import is_filler_slide, scrub_slide_text
from distill.ingest.extractor import extract_presentation, extract_slide_chunk
from distill.ingest.openxml_ast import parse_connector_ast_to_mermaid
from distill.ingest.spatial import sort_shapes_spatially
from distill.ingest.tables import extract_table_as_markdown

__all__ = [
    "extract_presentation",
    "extract_slide_chunk",
    "sort_shapes_spatially",
    "extract_table_as_markdown",
    "parse_connector_ast_to_mermaid",
    "carve_shape_asset",
    "is_filler_slide",
    "scrub_slide_text",
]
