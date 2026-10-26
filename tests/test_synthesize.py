"""Unit tests for pedagogical chapter synthesis and master index generation."""

from pathlib import Path

from distill.models.curriculum import CoverageReport, CurriculumBackbone, ModuleNode, TopicNode
from distill.models.manifest import BuildManifest
from distill.models.slide import ExtractedAsset, SlideChunk
from distill.synthesize import (
    STATIC_PEDAGOGICAL_SYSTEM_PROMPT,
    build_synthesis_prompt_payload,
    render_chapter_scaffold,
    synthesize_all_chapters,
)


def test_render_chapter_scaffold():
    topic = TopicNode(
        id="raft",
        title="Raft Consensus",
        module_id="mod-01",
        prerequisites=["time"],
        learning_objectives=["Derive leader election safety", "Understand log compaction"],
        exam_weight=0.25,
    )
    chunk = SlideChunk(
        deck_name="l01.pptx",
        slide_number=1,
        slide_id="l01.pptx#slide-1",
        title="Raft State Machine",
        text_content="Leader election invariants",
        assets=[
            ExtractedAsset(
                asset_id="l01_s01_img01",
                file_path="01_raw_markdown/assets/l01_s01_img01.png",
                shape_type="image/png",
                sha256="abc12345",
            )
        ],
    )

    scaffold = render_chapter_scaffold(topic, [chunk], chapter_num=1, course_code="CS6450")

    # Frontmatter and checklist
    assert "id: raft" in scaffold
    assert "exam_weight: 25%" in scaffold
    assert "Syllabus Mastery Checklist" in scaffold
    assert "Derive leader election safety" in scaffold

    # 4 Tiers
    assert "## 1. First-Principles Intuition" in scaffold
    assert "## 2. Formal Theory & Mathematical Formulation" in scaffold
    assert "## 3. Concrete Worked Examples & State-Trace Walkthrough" in scaffold
    assert "## 4. Edge Cases & Exam Traps" in scaffold

    # State transition matrix
    assert "| Step | Event / Stimulus | Node State |" in scaffold

    # Embedded asset
    assert "![l01_s01_img01](01_raw_markdown/assets/l01_s01_img01.png)" in scaffold

    # Active Recall deck
    assert "## 5. Active Recall Flashcard Deck" in scaffold


def test_prompt_payload_builder():
    topic = TopicNode(
        id="t1",
        title="Vector Clocks",
        module_id="m1",
        learning_objectives=["Vector comparison rules"],
    )
    payload = build_synthesis_prompt_payload(topic, chunks=[])
    assert "TARGET TOPIC: Vector Clocks" in payload
    assert "Vector comparison rules" in payload
    assert "Whiteboard Lecture" in payload
    assert len(STATIC_PEDAGOGICAL_SYSTEM_PROMPT) > 50


def test_synthesize_all_chapters(tmp_path: Path):
    backbone = CurriculumBackbone(
        course_code="CS6450",
        course_title="Distributed Systems",
        modules=[
            ModuleNode(
                id="m1",
                title="Consensus",
                topics=[
                    TopicNode(
                        id="raft",
                        title="Raft",
                        module_id="m1",
                        learning_objectives=["Leader Election"],
                    )
                ],
            )
        ],
    )
    ordered_topics = backbone.modules[0].topics
    chunk = SlideChunk(
        deck_name="d.pptx",
        slide_number=1,
        slide_id="d.pptx#slide-1",
        title="Raft",
        text_content="Leader election details",
    )
    mapping = {"raft": [chunk]}
    coverage = CoverageReport(
        total_syllabus_topics=1,
        covered_topic_count=1,
        uncovered_topic_count=0,
        coverage_percentage=100.0,
    )
    manifest = BuildManifest()

    out_dir = tmp_path / "study_guide"
    files = synthesize_all_chapters(
        backbone=backbone,
        ordered_topics=ordered_topics,
        mapping=mapping,
        coverage=coverage,
        output_dir=out_dir,
        manifest=manifest,
    )

    assert "raft" in files
    assert files["raft"].exists()
    assert (out_dir / "README.md").exists()
    assert "raft" in manifest.topics
