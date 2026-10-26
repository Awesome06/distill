"""Unit tests for multimodal ingestion, spatial sorting, and table extraction."""

from dataclasses import dataclass
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.util import Inches

from distill.ingest import (
    extract_presentation,
    extract_table_as_markdown,
    is_filler_slide,
    parse_connector_ast_to_mermaid,
    scrub_slide_text,
    sort_shapes_spatially,
)


@dataclass
class DummyShape:
    top: int
    left: int
    name: str


def test_spatial_sorting_anti_scramble():
    # In OpenXML, right shape might be created before left shape
    shape_right = DummyShape(top=100_000, left=500_000, name="Column 2 (Right)")
    shape_left = DummyShape(top=100_000, left=100_000, name="Column 1 (Left)")
    shape_bottom = DummyShape(top=600_000, left=100_000, name="Footer")

    # Pass in scrambled order
    scrambled = [shape_right, shape_bottom, shape_left]
    sorted_shapes = sort_shapes_spatially(scrambled, line_threshold=150_000)

    # First row should have left, then right; second row should have bottom
    assert sorted_shapes[0].name == "Column 1 (Left)"
    assert sorted_shapes[1].name == "Column 2 (Right)"
    assert sorted_shapes[2].name == "Footer"


def test_cleaner_noise_and_filler():
    raw_lines = [
        "Distributed Hash Tables",
        "Slide 14 of 45",
        "Consistent hashing guarantees O(log N) hops",
        "(c) 2024 University Tech. All Rights Reserved.",
    ]
    cleaned = scrub_slide_text(raw_lines)
    assert len(cleaned) == 2
    assert "Distributed Hash Tables" in cleaned
    assert "Consistent hashing guarantees O(log N) hops" in cleaned
    assert "Slide 14 of 45" not in cleaned

    assert is_filler_slide("Agenda", "Topic 1\nTopic 2") is True
    assert is_filler_slide("Any Questions?", "") is True
    assert is_filler_slide("Raft Consensus Algorithm", "Extensive protocol details...") is False


def test_table_normalizer(tmp_path: Path):
    prs = Presentation()
    slide_layout = prs.slide_layouts[5]  # Blank
    slide = prs.slides.add_slide(slide_layout)

    # Add table: 2 rows, 2 cols
    table_shape = slide.shapes.add_table(2, 2, Inches(1), Inches(1), Inches(4), Inches(2))
    table = table_shape.table
    table.cell(0, 0).text = "Feature"
    table.cell(0, 1).text = "TCP"
    table.cell(1, 0).text = "Reliability"
    table.cell(1, 1).text = "Guaranteed"

    md = extract_table_as_markdown(table_shape)
    assert md is not None
    assert "| Feature | TCP |" in md
    assert "| --- | --- |" in md
    assert "| Reliability | Guaranteed |" in md


def test_openxml_connector_to_mermaid():
    xml_content = """
    <p:spTree xmlns:p="http://schemas.openxmlformats.org/presentationml/2006/main"
              xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">
        <p:sp>
            <p:nvSpPr><p:cNvPr id="10" name="Box1"/></p:nvSpPr>
            <p:txBody><a:p><a:r><a:t>Client Request</a:t></a:r></a:p></p:txBody>
        </p:sp>
        <p:sp>
            <p:nvSpPr><p:cNvPr id="20" name="Box2"/></p:nvSpPr>
            <p:txBody><a:p><a:r><a:t>Load Balancer</a:t></a:r></a:p></p:txBody>
        </p:sp>
        <p:cxnSp>
            <p:nvCxnSpPr><p:cNvSpPr/></p:nvCxnSpPr>
            <p:spPr>
                <a:stCxn id="10"/>
                <a:endCxn id="20"/>
            </p:spPr>
        </p:cxnSp>
    </p:spTree>
    """
    element = etree.fromstring(xml_content.encode("utf-8"))
    mermaid = parse_connector_ast_to_mermaid(element)
    assert mermaid is not None
    assert "graph TD" in mermaid
    assert 'N10["Client Request"]' in mermaid
    assert 'N20["Load Balancer"]' in mermaid
    assert "N10 --> N20" in mermaid


def test_full_presentation_extraction(tmp_path: Path):
    pptx_path = tmp_path / "test_lecture.pptx"
    assets_dir = tmp_path / "assets"
    out_dir = tmp_path / "raw_md"

    prs = Presentation()
    # Slide 1: Title & Body
    slide_layout = prs.slide_layouts[1]
    slide = prs.slides.add_slide(slide_layout)
    slide.shapes.title.text = "Distributed Systems 101"
    body_tf = slide.shapes.placeholders[1].text_frame
    body_tf.text = "First principle: Independent failures."

    # Notes
    notes_slide = slide.notes_slide
    notes_slide.notes_text_frame.text = "Remind students about network partitions."

    # Slide 2: Filler
    filler_layout = prs.slide_layouts[1]
    filler_slide = prs.slides.add_slide(filler_layout)
    filler_slide.shapes.title.text = "Questions?"

    prs.save(str(pptx_path))

    manifest, chunks = extract_presentation(pptx_path, assets_dir, out_dir)
    assert manifest.deck_name == "test_lecture.pptx"
    # The filler slide should be filtered out
    assert manifest.slide_count == 1
    assert len(chunks) == 1

    chunk = chunks[0]
    assert chunk.title == "Distributed Systems 101"
    assert "First principle: Independent failures." in chunk.text_content
    assert "Remind students about network partitions." in chunk.speaker_notes
    assert (out_dir / "test_lecture.md").exists()
