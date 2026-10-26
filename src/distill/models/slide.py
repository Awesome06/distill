"""Slide models and extraction contracts adhering to ai/multimodal-slide-ingestion."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedAsset(BaseModel):
    """Represents an image, diagram, or media file extracted from a slide."""

    asset_id: str = Field(description="Unique asset identifier: {deck}_{slide}_{idx}")
    file_path: str = Field(description="Relative path on disk (e.g. 01_raw_markdown/assets/...)")
    shape_type: str = Field(description="OpenXML shape type or picture format")
    sha256: str = Field(description="SHA-256 content hash of the asset binary")


class SlideShape(BaseModel):
    """Represents a single geometric shape on a slide with bounding box coordinates."""

    shape_id: int
    shape_type: str
    text: str = ""
    top: int
    left: int
    width: int
    height: int


class SlideChunk(BaseModel):
    """Normalized atomic chunk for a single slide adhering to anti-scramble invariants."""

    deck_name: str = Field(description="Source presentation filename (e.g. lecture_01.pptx)")
    slide_number: int = Field(description="1-indexed physical slide position")
    slide_id: str = Field(
        description="Unique compound identifier: {deck_name}#slide-{slide_number}"
    )
    title: str = Field(default="", description="Detected slide title or header")
    text_content: str = Field(default="", description="Spatially sorted body text lines")
    speaker_notes: str = Field(
        default="", description="Raw speaker notes extracted from notes slide"
    )
    tables: list[str] = Field(default_factory=list, description="GitHub-Flavored Markdown tables")
    mermaid_diagrams: list[str] = Field(
        default_factory=list,
        description="Deterministic Mermaid flowcharts from OpenXML connection shapes or SmartArt",
    )
    assets: list[ExtractedAsset] = Field(
        default_factory=list, description="Extracted raster images and figures"
    )
    raw_markdown: str = Field(
        default="", description="Complete rendered slide markdown block with frontmatter"
    )
    sha256: str = Field(default="", description="SHA-256 digest of clean slide content and assets")
