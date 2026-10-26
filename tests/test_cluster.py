"""Unit tests for curriculum parsing, Kahn's DAG sorting, and coverage audits."""

import pytest

from distill.cluster import (
    CyclicDependencyError,
    align_slides_to_curriculum,
    generate_coverage_report,
    parse_syllabus_markdown,
    render_coverage_audit_markdown,
    topological_sort_topics,
)
from distill.models.curriculum import TopicNode
from distill.models.slide import SlideChunk


def test_kahn_topological_sort_success():
    # Dependency order: Time (no prereq) -> Consensus -> Transactions
    topic_a = TopicNode(id="time", title="Logical Clocks", module_id="m1", prerequisites=[])

    topic_b = TopicNode(
        id="consensus", title="Raft Consensus", module_id="m1", prerequisites=["time"]
    )
    topic_c = TopicNode(
        id="transactions", title="Distributed 2PC", module_id="m1", prerequisites=["consensus"]
    )

    # Scrambled input
    topics = [topic_c, topic_a, topic_b]
    sorted_order = topological_sort_topics(topics)

    assert [t.id for t in sorted_order] == ["time", "consensus", "transactions"]


def test_kahn_topological_sort_cycle_detection():
    # Circular dependency: A needs B, B needs A
    topic_a = TopicNode(id="a", title="Topic A", module_id="m1", prerequisites=["b"])
    topic_b = TopicNode(id="b", title="Topic B", module_id="m1", prerequisites=["a"])

    with pytest.raises(CyclicDependencyError, match="Circular prerequisite dependency"):
        topological_sort_topics([topic_a, topic_b])


def test_syllabus_markdown_parser():
    sample_md = """
# CS6450: Advanced Distributed Systems

## Textbooks
- Distributed Systems: Principles and Paradigms (Tanenbaum)
- Designing Data-Intensive Applications (Kleppmann)

## Module 1: Time and Consistency (Week 1)
### Logical Time and Clocks
- Prerequisites: none
- Objectives: Derive Lamport clocks, Vector clock partial orders
- Readings: Tanenbaum Chapter 6.1
- Exam Weight: 15%

### Distributed State Machine Replication
- Prerequisites: top-logical-time-and-clocks
- Objectives: Implement Raft leader election, Log matching property
- Readings: Ongaro PhD Thesis
    """
    backbone = parse_syllabus_markdown(sample_md)
    assert backbone.course_code == "CS6450"
    assert backbone.course_title == "Advanced Distributed Systems"
    assert len(backbone.textbooks) == 2
    assert len(backbone.modules) == 1

    mod = backbone.modules[0]
    assert mod.week_number == 1
    assert len(mod.topics) == 2

    top1 = mod.topics[0]
    assert top1.title == "Logical Time and Clocks"
    assert top1.exam_weight == 0.15
    assert len(top1.learning_objectives) >= 1

    top2 = mod.topics[1]
    assert "top-logical-time-and-clocks" in top2.prerequisites


def test_alignment_and_coverage_audit(tmp_path):
    sample_md = """
# CS6450: Systems
## Module 1: Core
### Topic 1: Concurrency
- Objectives: Locks and condition variables

### Topic 2: Memory Consistency
- Objectives: Sequential consistency

### Topic 3: Whiteboard Architecture
- Objectives: Secret unreleased algorithm
    """
    backbone = parse_syllabus_markdown(sample_md)

    # Create slide chunks for Topic 1 and Topic 2, but none for Topic 3
    chunk1 = SlideChunk(
        deck_name="l01.pptx",
        slide_number=1,
        slide_id="l01.pptx#slide-1",
        title="Concurrency and Locks",
        text_content="Mutual exclusion and race conditions with mutexes.",
    )
    chunk2 = SlideChunk(
        deck_name="l02.pptx",
        slide_number=5,
        slide_id="l02.pptx#slide-5",
        title="Memory Consistency Models",
        text_content="Sequential consistency vs relaxed memory architectures.",
    )

    mapping, orphaned = align_slides_to_curriculum([chunk1, chunk2], backbone)
    report = generate_coverage_report(backbone, mapping, orphaned)

    assert report.total_syllabus_topics == 3
    assert report.covered_topic_count == 2
    assert report.uncovered_topic_count == 1
    assert "top-topic-3-whiteboard-architecture" in report.uncovered_topics
    assert report.coverage_percentage == 66.7

    audit_file = tmp_path / "coverage_audit.md"
    rendered = render_coverage_audit_markdown(backbone, report, mapping, audit_file)
    assert "Whiteboard Lecture Gaps Detected" in rendered
    assert audit_file.exists()
