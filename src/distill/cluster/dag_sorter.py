"""Kahn's Algorithm for topological sorting of curriculum prerequisite DAGs."""

from __future__ import annotations

from collections import deque

from distill.models.curriculum import TopicNode


class CyclicDependencyError(ValueError):
    """Raised when a circular prerequisite dependency is detected in the curriculum DAG."""


def topological_sort_topics(topics: list[TopicNode]) -> list[TopicNode]:
    """Sort curriculum topics in valid pedagogical order using Kahn's Algorithm.

    Ensures that any prerequisite topic precedes all dependent topics in the final sequence.
    Detects cycles and raises CyclicDependencyError if circular dependencies exist.

    Args:
        topics: List of TopicNode objects declaring prerequisites.

    Returns:
        Topologically ordered list of TopicNode objects.
    """
    topic_map = {t.id: t for t in topics}
    in_degree: dict[str, int] = {t.id: 0 for t in topics}
    adjacency: dict[str, list[str]] = {t.id: [] for t in topics}

    # Build adjacency list: prerequisite -> dependents
    for topic in topics:
        for prereq_id in topic.prerequisites:
            if prereq_id in topic_map:
                adjacency[prereq_id].append(topic.id)
                in_degree[topic.id] += 1

    # Queue of nodes with zero in-degree (no remaining unfulfilled prerequisites)
    queue: deque[str] = deque([t_id for t_id, deg in in_degree.items() if deg == 0])
    sorted_topics: list[TopicNode] = []

    while queue:
        current_id = queue.popleft()
        sorted_topics.append(topic_map[current_id])

        for neighbor_id in adjacency[current_id]:
            in_degree[neighbor_id] -= 1
            if in_degree[neighbor_id] == 0:
                queue.append(neighbor_id)

    # Check for cycles
    if len(sorted_topics) != len(topics):
        remaining = [t_id for t_id, deg in in_degree.items() if deg > 0]
        raise CyclicDependencyError(
            f"Circular prerequisite dependency detected among topics: {', '.join(remaining)}"
        )

    return sorted_topics
