"""Curriculum and syllabus data models adhering to ai/pedagogical-synthesis."""

from __future__ import annotations

from pydantic import BaseModel, Field


class LearningObjective(BaseModel):
    """Specific measurable learning objective from the syllabus."""

    id: str = Field(description="Unique objective ID (e.g. LO-01-A)")
    description: str = Field(description="Action-oriented statement of student capability")


class TopicNode(BaseModel):
    """Atomic curriculum node to be synthesized into a standalone study chapter."""

    id: str = Field(description="Canonical slug identifier (e.g. topic-02-raft-consensus)")
    title: str = Field(description="Human readable chapter title")
    module_id: str = Field(description="Parent module identifier")
    prerequisites: list[str] = Field(
        default_factory=list,
        description="IDs of prerequisite topics that MUST precede this topic in Kahn's DAG",
    )
    learning_objectives: list[str] = Field(
        default_factory=list, description="IDs or text of assigned learning objectives"
    )
    readings: list[str] = Field(
        default_factory=list, description="Prescribed textbook chapters or paper citations"
    )
    exam_weight: float = Field(
        default=0.0, description="Approximate course/exam weighting percentage (0.0 - 1.0)"
    )
    mapped_slide_ids: list[str] = Field(
        default_factory=list, description="Compound slide IDs mapped to this topic"
    )


class ModuleNode(BaseModel):
    """High-level syllabus module or week grouping."""

    id: str = Field(description="Module slug (e.g. module-01-distributed-foundations)")
    title: str = Field(description="Module title")
    week_number: int | None = Field(default=None, description="Course schedule week number")
    topics: list[TopicNode] = Field(default_factory=list, description="Ordered topic nodes")


class CurriculumBackbone(BaseModel):
    """The authoritative top-down curriculum representation parsed from 00_syllabus/."""

    course_code: str = Field(default="", description="Course code (e.g. CS6450)")
    course_title: str = Field(default="", description="Course name")
    term: str = Field(default="", description="Term / Semester")
    textbooks: list[str] = Field(default_factory=list, description="Prescribed core textbooks")
    modules: list[ModuleNode] = Field(default_factory=list, description="Course modules")


class CoverageReport(BaseModel):
    """Audit report comparing syllabus requirements against covered slide content."""

    total_syllabus_topics: int
    covered_topic_count: int
    uncovered_topic_count: int
    coverage_percentage: float
    covered_topics: list[str] = Field(default_factory=list)
    uncovered_topics: list[str] = Field(
        default_factory=list,
        description="Topics declared in syllabus with 0 slide chunks (whiteboard lectures)",
    )
    orphaned_slides: list[str] = Field(
        default_factory=list,
        description="Slide IDs that could not be mapped to any syllabus topic",
    )
