"""Chapter generation coordinator adhering to ai/pedagogical-synthesis."""

from __future__ import annotations

import hashlib
from pathlib import Path

from distill.models.curriculum import CoverageReport, CurriculumBackbone, TopicNode
from distill.models.manifest import BuildManifest, TopicManifest
from distill.models.slide import SlideChunk
from distill.synthesize.master_index import generate_master_index_markdown
from distill.synthesize.template import render_chapter_scaffold


def synthesize_all_chapters(
    backbone: CurriculumBackbone,
    ordered_topics: list[TopicNode],
    mapping: dict[str, list[SlideChunk]],
    coverage: CoverageReport,
    output_dir: Path,
    manifest: BuildManifest | None = None,
) -> dict[str, Path]:
    """Synthesize complete textbook chapters for all topics and write 03_study_guide/."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    generated_files: dict[str, Path] = {}

    for idx, topic in enumerate(ordered_topics, start=1):
        chunks = mapping.get(topic.id, [])
        chapter_md = render_chapter_scaffold(
            topic=topic,
            chunks=chunks,
            chapter_num=idx,
            course_code=backbone.course_code,
        )

        filename = f"{idx:02d}_{topic.id}.md"
        chapter_path = output_dir / filename
        chapter_path.write_text(chapter_md, encoding="utf-8")
        generated_files[topic.id] = chapter_path

        # Update manifest if provided
        if manifest is not None:
            chunk_hashes = "".join(sorted([c.sha256 for c in chunks]))
            chunk_digest = hashlib.sha256(chunk_hashes.encode("utf-8")).hexdigest()
            guide_sha256 = hashlib.sha256(chapter_md.encode("utf-8")).hexdigest()

            manifest.topics[topic.id] = TopicManifest(
                topic_id=topic.id,
                chunk_hashes_digest=chunk_digest,
                study_guide_sha256=guide_sha256,
            )

    # Generate master index README.md
    readme_path = output_dir / "README.md"
    generate_master_index_markdown(
        backbone=backbone,
        ordered_topics=ordered_topics,
        coverage=coverage,
        output_path=readme_path,
    )

    return generated_files
