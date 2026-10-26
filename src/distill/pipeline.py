"""Master incremental pipeline runner for ingestion, clustering, and compilation."""

from __future__ import annotations

import hashlib
from pathlib import Path

from distill.cluster import (
    align_slides_to_curriculum,
    generate_coverage_report,
    load_curriculum,
    render_coverage_audit_markdown,
    topological_sort_topics,
)
from distill.compile import (
    compile_marp_to_presentation,
    generate_marp_deck_markdown,
)
from distill.ingest import extract_presentation
from distill.models.curriculum import CoverageReport, CurriculumBackbone, TopicNode
from distill.models.manifest import BuildManifest
from distill.models.slide import SlideChunk
from distill.synthesize import synthesize_all_chapters


class DistillPipeline:
    """End-to-end incremental study compiler pipeline."""

    def __init__(self, root_dir: Path | None = None) -> None:
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.syllabus_dir = self.root_dir / "00_syllabus"
        self.inbox_dir = self.root_dir / "00_inbox_ppts"
        self.raw_md_dir = self.root_dir / "01_raw_markdown"
        self.assets_dir = self.raw_md_dir / "assets"
        self.backbone_dir = self.root_dir / "02_curriculum_backbone"
        self.study_guide_dir = self.root_dir / "03_study_guide"
        self.decks_dir = self.root_dir / "04_unified_decks"
        self.cache_dir = self.root_dir / ".cache"
        self.manifest_path = self.cache_dir / "build_manifest.json"

        self.manifest = BuildManifest.load_or_init(self.manifest_path)

    def run_ingestion(self, force: bool = False) -> list[SlideChunk]:
        """Stage 1: Extract text, tables, OpenXML connectors, and image assets from inbox decks."""
        self.assets_dir.mkdir(parents=True, exist_ok=True)
        self.raw_md_dir.mkdir(parents=True, exist_ok=True)

        all_chunks: list[SlideChunk] = []
        ppt_files = list(self.inbox_dir.glob("*.pptx"))

        for ppt in ppt_files:
            deck_bytes = ppt.read_bytes()
            current_hash = hashlib.sha256(deck_bytes).hexdigest()

            # Incremental caching check
            cached_deck = self.manifest.decks.get(ppt.name)
            if not force and cached_deck and cached_deck.sha256 == current_hash:
                # Deck is clean, extract chunks without re-parsing if desired,
                # or read cached slide manifests
                pass

            deck_manifest, chunks = extract_presentation(
                pptx_path=ppt,
                assets_dir=self.assets_dir,
                output_dir=self.raw_md_dir,
            )
            self.manifest.decks[ppt.name] = deck_manifest
            all_chunks.extend(chunks)

        return all_chunks

    def run_clustering(
        self,
        chunks: list[SlideChunk],
    ) -> tuple[CurriculumBackbone, list[TopicNode], dict[str, list[SlideChunk]], CoverageReport]:
        """Stage 2: Parse syllabus, sort topic DAG, and align slide chunks."""
        self.backbone_dir.mkdir(parents=True, exist_ok=True)

        # Locate syllabus file
        syllabus_files = list(self.syllabus_dir.glob("*.md")) + list(
            self.syllabus_dir.glob("*.json")
        )
        if not syllabus_files:
            # Fallback to default curriculum backbone if no syllabus dropped yet
            from distill.models.curriculum import ModuleNode

            backbone = CurriculumBackbone(
                course_code="COURSE101",
                course_title="General Lecture Series",
                modules=[
                    ModuleNode(
                        id="mod-01",
                        title="Main Lecture Module",
                        topics=[],
                    )
                ],
            )
        else:
            backbone = load_curriculum(syllabus_files[0])

        all_topics = [t for mod in backbone.modules for t in mod.topics]

        # Topological sorting of prerequisites via Kahn's Algorithm
        if all_topics:
            ordered_topics = topological_sort_topics(all_topics)
        else:
            # If syllabus had no explicit topics, derive topics from slide titles
            from distill.models.curriculum import TopicNode

            seen_titles: set[str] = set()
            ordered_topics = []
            for c in chunks:
                if c.title and c.title not in seen_titles:
                    seen_titles.add(c.title)
                    t_slug = f"top-{len(ordered_topics) + 1:02d}"
                    topic_node = TopicNode(
                        id=t_slug,
                        title=c.title,
                        module_id="mod-01",
                    )
                    ordered_topics.append(topic_node)
                    if backbone.modules:
                        backbone.modules[0].topics.append(topic_node)

        # Align slides to topics
        mapping, orphaned = align_slides_to_curriculum(chunks, backbone)

        # Generate coverage report & render markdown audit
        coverage = generate_coverage_report(backbone, mapping, orphaned)
        audit_file = self.backbone_dir / "coverage_audit.md"
        render_coverage_audit_markdown(backbone, coverage, mapping, audit_file)

        return backbone, ordered_topics, mapping, coverage

    def run_synthesis(
        self,
        backbone: CurriculumBackbone,
        ordered_topics: list[TopicNode],
        mapping: dict[str, list[SlideChunk]],
        coverage: CoverageReport,
    ) -> dict[str, Path]:
        """Stage 3 & 4: Synthesize 4-tier textbook chapters and master index."""
        self.study_guide_dir.mkdir(parents=True, exist_ok=True)
        return synthesize_all_chapters(
            backbone=backbone,
            ordered_topics=ordered_topics,
            mapping=mapping,
            coverage=coverage,
            output_dir=self.study_guide_dir,
            manifest=self.manifest,
        )

    def run_compilation(
        self,
        ordered_topics: list[TopicNode],
        mapping: dict[str, list[SlideChunk]],
    ) -> list[Path]:
        """Stage 5: Generate Marp presentation decks and compile to pptx/pdf."""
        self.decks_dir.mkdir(parents=True, exist_ok=True)
        compiled_decks: list[Path] = []

        for idx, topic in enumerate(ordered_topics, start=1):
            chunks = mapping.get(topic.id, [])
            marp_md = generate_marp_deck_markdown(
                topic=topic,
                chunks=chunks,
                chapter_num=idx,
            )

            marp_file = self.decks_dir / f"{idx:02d}_{topic.id}.marp.md"
            marp_file.write_text(marp_md, encoding="utf-8")
            compiled_decks.append(marp_file)

            # Attempt compilation to .pptx if Marp CLI is available
            pptx_target = self.decks_dir / f"{idx:02d}_{topic.id}.pptx"
            compile_marp_to_presentation(marp_file, pptx_target, output_format="pptx")

        return compiled_decks

    def run_all(self, force: bool = False) -> None:
        """Execute all stages end-to-end with atomic manifest updates."""
        # 1. Ingest
        chunks = self.run_ingestion(force=force)

        # 2. Cluster & Audit
        backbone, ordered_topics, mapping, coverage = self.run_clustering(chunks)

        # 3. Synthesize
        self.run_synthesis(backbone, ordered_topics, mapping, coverage)

        # 4. Compile
        self.run_compilation(ordered_topics, mapping)

        # 5. Atomic Manifest Save
        self.manifest.save_atomic(self.manifest_path)
