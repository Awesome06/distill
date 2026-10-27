---
title: Per-Subject Staging Architecture
summary: Decision to organize slide ingestion, curriculum DAGs, study guides, and decks into subject subdirectories within root staging folders.
type: adr
status: active
tags: [adr, multi-subject, staging, pipeline]
aliases: [adr-002, per-subject-staging]
---

# ADR 002: Per-Subject Staging Architecture

## Context
Originally, Distill processed slide decks and course syllabi in flat root directories (`00_inbox_ppts/`, `00_syllabus/`, `01_raw_markdown/`, etc.). When managing multiple courses, lectures from different subjects were intermingled, leading to conflicting curriculum backbones, mixed-topic DAG alignments, and shared cache collisions.

## Decision
1. Organize course inputs, intermediate representations, and synthesized outputs per subject directly inside the existing root stage folders:
   - `00_syllabus/<subject>/`
   - `00_inbox_ppts/<subject>/`
   - `01_raw_markdown/<subject>/assets/`
   - `02_curriculum_backbone/<subject>/`
   - `03_study_guide/<subject>/`
   - `04_unified_decks/<subject>/`
   - `.cache/<subject>/build_manifest.json`
2. Maintain backward-compatible fallback for flat root layouts when no subject subdirectories exist.
3. Provide automated CLI subject scaffolding (`distill new-subject <name>`), discovery (`distill subjects`), and target options (`--subject <name>`) across all stage runners.

## Consequences
- Every course maintains an isolated syllabus, DAG, 4-tier textbook, Marp decks, and three-tier SHA-256 build manifest.
- Slide assets carve relative paths dynamically scoped to the subject folder (`01_raw_markdown/<subject>/assets/`).
- Running `distill run` without `--subject` discovers and executes across all configured subjects sequentially.

## References
- System Architecture: [[wiki/architecture]] (relates_to)
- Initial Architectural Baseline: [[wiki/adr/001-initial-architecture]] (extends)
