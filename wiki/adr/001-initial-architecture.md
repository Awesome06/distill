---
title: Initial Architectural Baseline
summary: Foundational decision establishing modular boundaries, agent skills integration, and repository wiki memory.
type: adr
status: active
tags: [adr, baseline, setup]
aliases: [adr-001, baseline-architecture]
---

# ADR 001: Initial Architectural Baseline

## Context
Establishes the foundational project layout, agentic skill integration, and repository wiki knowledge graph.

## Decision
1. Organize project components around modular boundaries.
2. Link the repository to the centralized agent skills vault for hardened engineering directives.
3. Maintain atomic architectural decision records (ADRs) and domain specifications in `wiki/`.

## Consequences
- Every new architectural pivot MUST be captured in a sequential ADR in `wiki/adr/`.
- Cross-references use bidirectional wikilink syntax (e.g. [[wiki/architecture]]) with optional edge typing.

## References
- Root Knowledge Graph: [[wiki/index]] (relates_to)
- System Architecture: [[wiki/architecture]] (relates_to)
