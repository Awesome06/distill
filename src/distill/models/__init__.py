"""Data contracts and schemas for distill."""

from distill.models.curriculum import (
    CoverageReport,
    CurriculumBackbone,
    LearningObjective,
    ModuleNode,
    TopicNode,
)
from distill.models.manifest import (
    BuildManifest,
    DeckManifest,
    SlideManifest,
    TopicManifest,
)
from distill.models.slide import ExtractedAsset, SlideChunk, SlideShape

__all__ = [
    "BuildManifest",
    "DeckManifest",
    "SlideManifest",
    "TopicManifest",
    "ExtractedAsset",
    "SlideChunk",
    "SlideShape",
    "CurriculumBackbone",
    "LearningObjective",
    "ModuleNode",
    "TopicNode",
    "CoverageReport",
]
