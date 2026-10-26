"""Curriculum clustering, DAG sorting, and coverage audit module."""

from distill.cluster.aligner import align_slides_to_curriculum, compute_alignment_score
from distill.cluster.audit import generate_coverage_report, render_coverage_audit_markdown
from distill.cluster.dag_sorter import CyclicDependencyError, topological_sort_topics
from distill.cluster.syllabus_parser import load_curriculum, parse_syllabus_markdown

__all__ = [
    "topological_sort_topics",
    "CyclicDependencyError",
    "parse_syllabus_markdown",
    "load_curriculum",
    "compute_alignment_score",
    "align_slides_to_curriculum",
    "generate_coverage_report",
    "render_coverage_audit_markdown",
]
