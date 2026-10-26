"""Three-tier SHA-256 build manifest models adhering to ops/incremental-pipeline-runner."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, Field


class SlideManifest(BaseModel):
    """Tier 2: Slide-level hash tracking."""

    slide_id: str
    sha256: str
    asset_hashes: dict[str, str] = Field(
        default_factory=dict, description="asset_id -> sha256 of binary"
    )


class DeckManifest(BaseModel):
    """Tier 1: Deck-level hash tracking."""

    deck_name: str
    sha256: str
    slide_count: int
    last_modified: float
    slides: dict[str, SlideManifest] = Field(
        default_factory=dict, description="slide_id -> SlideManifest"
    )


class TopicManifest(BaseModel):
    """Tier 3: Topic/Chapter-level hash tracking."""

    topic_id: str
    chunk_hashes_digest: str = Field(description="Combined SHA-256 hash of all mapped slide chunks")
    study_guide_sha256: str = Field(default="", description="SHA-256 of generated chapter markdown")
    unified_deck_sha256: str = Field(
        default="", description="SHA-256 of generated Marp slide markdown"
    )
    last_synthesized: float = 0.0
    last_compiled: float = 0.0


class BuildManifest(BaseModel):
    """The master three-tier build manifest stored in .cache/build_manifest.json."""

    version: str = "1.0.0"
    decks: dict[str, DeckManifest] = Field(
        default_factory=dict, description="deck_name -> DeckManifest"
    )
    topics: dict[str, TopicManifest] = Field(
        default_factory=dict, description="topic_id -> TopicManifest"
    )

    @classmethod
    def load_or_init(cls, cache_path: Path) -> BuildManifest:
        """Load an existing manifest or return an empty initial one."""
        if cache_path.exists():
            try:
                data = json.loads(cache_path.read_text(encoding="utf-8"))
                return cls.model_validate(data)
            except Exception:
                pass
        return cls()

    def save_atomic(self, cache_path: Path) -> None:
        """Atomic write using temporary file to prevent corruption on interruption."""
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = cache_path.with_suffix(".tmp")
        payload = self.model_dump_json(indent=2)
        tmp_path.write_text(payload, encoding="utf-8")
        tmp_path.replace(cache_path)
