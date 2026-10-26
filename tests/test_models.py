"""Unit tests for core data models and manifests."""

from pathlib import Path

from distill.models import (
    BuildManifest,
    CurriculumBackbone,
    DeckManifest,
    ExtractedAsset,
    ModuleNode,
    SlideChunk,
    SlideManifest,
    TopicManifest,
    TopicNode,
)


def test_build_manifest_atomic_save(tmp_path: Path):
    cache_file = tmp_path / "cache" / "build_manifest.json"
    manifest = BuildManifest()

    manifest.decks["lecture_01.pptx"] = DeckManifest(
        deck_name="lecture_01.pptx",
        sha256="abc123hash",
        slide_count=1,
        last_modified=1234567.89,
        slides={
            "lecture_01.pptx#slide-1": SlideManifest(
                slide_id="lecture_01.pptx#slide-1",
                sha256="slidehash1",
                asset_hashes={"asset1": "imghash1"},
            )
        },
    )

    manifest.topics["topic-01"] = TopicManifest(
        topic_id="topic-01",
        chunk_hashes_digest="digest123",
        study_guide_sha256="guidehash",
    )

    manifest.save_atomic(cache_file)
    assert cache_file.exists()

    loaded = BuildManifest.load_or_init(cache_file)
    assert "lecture_01.pptx" in loaded.decks
    assert loaded.decks["lecture_01.pptx"].slide_count == 1
    assert "topic-01" in loaded.topics


def test_curriculum_backbone_model():
    backbone = CurriculumBackbone(
        course_code="CS6450",
        course_title="Distributed Systems",
        modules=[
            ModuleNode(
                id="module-01",
                title="Foundations",
                week_number=1,
                topics=[
                    TopicNode(
                        id="topic-01",
                        title="Time and Clocks",
                        module_id="module-01",
                        prerequisites=[],
                        learning_objectives=["Understand Lamport timestamps"],
                    )
                ],
            )
        ],
    )
    assert len(backbone.modules) == 1
    assert backbone.modules[0].topics[0].id == "topic-01"


def test_slide_chunk_model():
    chunk = SlideChunk(
        deck_name="deck1.pptx",
        slide_number=1,
        slide_id="deck1.pptx#slide-1",
        title="Intro",
        text_content="Welcome to CS6450",
        assets=[
            ExtractedAsset(
                asset_id="deck1_slide1_img1",
                file_path="01_raw_markdown/assets/deck1_slide1_img1.png",
                shape_type="picture",
                sha256="hash123",
            )
        ],
    )
    assert chunk.slide_id == "deck1.pptx#slide-1"
    assert len(chunk.assets) == 1
