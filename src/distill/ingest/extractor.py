"""Master presentation ingestion engine for spatial sorting, AST parsing, and assets."""

from __future__ import annotations

import hashlib
from pathlib import Path

from pptx import Presentation

from distill.ingest.assets import carve_shape_asset
from distill.ingest.cleaner import is_filler_slide, scrub_slide_text
from distill.ingest.openxml_ast import parse_connector_ast_to_mermaid
from distill.ingest.spatial import sort_shapes_spatially
from distill.ingest.tables import extract_table_as_markdown
from distill.models.manifest import DeckManifest, SlideManifest
from distill.models.slide import ExtractedAsset, SlideChunk


def extract_slide_chunk(
    slide: Presentation.slides,
    slide_num: int,
    deck_name: str,
    assets_dir: Path,
) -> SlideChunk:
    """Extract an atomic, spatially sorted SlideChunk from a python-pptx slide object."""
    deck_stem = Path(deck_name).stem
    slide_id = f"{deck_name}#slide-{slide_num}"

    # 1. Extract speaker notes
    speaker_notes = ""
    if hasattr(slide, "has_notes_slide") and slide.has_notes_slide:
        try:
            notes_tf = slide.notes_slide.notes_text_frame
            if notes_tf:
                speaker_notes = notes_tf.text.strip()
        except Exception:
            pass

    # 2. Spatially sort shapes to eliminate z-order scrambling
    shapes = sort_shapes_spatially(list(slide.shapes))

    # 3. Identify slide title
    title = ""
    if slide.shapes.title and slide.shapes.title.text:
        title = slide.shapes.title.text.strip()

    raw_text_lines: list[str] = []
    tables: list[str] = []
    assets: list[ExtractedAsset] = []
    asset_idx = 1

    # 4. Iterate over spatially ordered shapes
    for shape in shapes:
        # Avoid duplicating the title in the body
        if shape == slide.shapes.title:
            continue

        # Check for tables
        if getattr(shape, "has_table", False):
            tbl_md = extract_table_as_markdown(shape)
            if tbl_md:
                tables.append(tbl_md)
            continue

        # Check for images / media assets
        asset = carve_shape_asset(shape, deck_stem, slide_num, asset_idx, assets_dir)
        if asset:
            assets.append(asset)
            asset_idx += 1

        # Check for text frames
        if getattr(shape, "has_text_frame", False) and shape.text_frame:
            for p in shape.text_frame.paragraphs:
                p_text = p.text.strip()
                if p_text:
                    raw_text_lines.append(p_text)

    # If title was not explicitly tagged in slide layout, take first prominent text line
    if not title and raw_text_lines:
        title = raw_text_lines.pop(0)

    # 5. Clean and scrub boilerplate
    clean_lines = scrub_slide_text(raw_text_lines)
    text_content = "\n".join(clean_lines)

    # 6. Parse OpenXML connectors into Mermaid flowchart
    mermaid_diagrams: list[str] = []
    mermaid_diag = parse_connector_ast_to_mermaid(slide._element)
    if mermaid_diag:
        mermaid_diagrams.append(mermaid_diag)

    # 7. Format clean Markdown representation
    md_parts: list[str] = [f"<!-- slide: {slide_id} -->"]
    if title:
        md_parts.append(f"### {title}")
    if text_content:
        md_parts.append(text_content)
    if tables:
        md_parts.extend(tables)
    if mermaid_diagrams:
        md_parts.extend(mermaid_diagrams)
    for asset in assets:
        md_parts.append(f"![{asset.asset_id}]({asset.file_path})")

    raw_markdown = "\n\n".join(md_parts)
    chunk_hash = hashlib.sha256(raw_markdown.encode("utf-8")).hexdigest()

    return SlideChunk(
        deck_name=deck_name,
        slide_number=slide_num,
        slide_id=slide_id,
        title=title,
        text_content=text_content,
        speaker_notes=speaker_notes,
        tables=tables,
        mermaid_diagrams=mermaid_diagrams,
        assets=assets,
        raw_markdown=raw_markdown,
        sha256=chunk_hash,
    )


def extract_presentation(
    pptx_path: Path,
    assets_dir: Path,
    output_dir: Path | None = None,
) -> tuple[DeckManifest, list[SlideChunk]]:
    """Extract an entire presentation into normalized slide chunks and update deck manifest."""
    pptx_path = Path(pptx_path)
    deck_name = pptx_path.name
    deck_bytes = pptx_path.read_bytes()
    deck_sha256 = hashlib.sha256(deck_bytes).hexdigest()

    prs = Presentation(str(pptx_path))
    chunks: list[SlideChunk] = []
    slide_manifests: dict[str, SlideManifest] = {}

    for slide_idx, slide in enumerate(prs.slides, start=1):
        chunk = extract_slide_chunk(slide, slide_idx, deck_name, assets_dir)

        # Filter out empty filler slides with no content/diagrams
        if (
            is_filler_slide(chunk.title, chunk.text_content)
            and not chunk.assets
            and not chunk.tables
        ):
            continue

        chunks.append(chunk)
        slide_manifests[chunk.slide_id] = SlideManifest(
            slide_id=chunk.slide_id,
            sha256=chunk.sha256,
            asset_hashes={a.asset_id: a.sha256 for a in chunk.assets},
        )

    # Optional: Persist raw markdown file to 01_raw_markdown/
    if output_dir:
        output_dir.mkdir(parents=True, exist_ok=True)
        md_file = output_dir / f"{pptx_path.stem}.md"
        full_markdown = "\n\n---\n\n".join([c.raw_markdown for c in chunks])
        md_file.write_text(full_markdown, encoding="utf-8")

    deck_manifest = DeckManifest(
        deck_name=deck_name,
        sha256=deck_sha256,
        slide_count=len(chunks),
        last_modified=pptx_path.stat().st_mtime,
        slides=slide_manifests,
    )

    return deck_manifest, chunks
