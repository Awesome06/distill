"""Syllabus parser for Markdown and JSON course curricula adhering to ai/pedagogical-synthesis."""

from __future__ import annotations

import json
import re
from pathlib import Path

from distill.models.curriculum import (
    CurriculumBackbone,
    ModuleNode,
    TopicNode,
)


def _slugify(text: str) -> str:
    """Generate a clean slug identifier from text."""
    slug = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", slug)


def parse_syllabus_markdown(content: str) -> CurriculumBackbone:
    """Parse a Markdown-formatted syllabus into a structured CurriculumBackbone."""
    lines = content.splitlines()

    course_code = ""
    course_title = ""
    textbooks: list[str] = []
    modules: list[ModuleNode] = []

    current_module: ModuleNode | None = None
    current_topic: TopicNode | None = None
    in_textbooks_section = False

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Header 1: Course Title
        if stripped.startswith("# ") and not course_title:
            raw_title = stripped[2:].strip()
            if ":" in raw_title:
                parts = raw_title.split(":", 1)
                course_code = parts[0].strip()
                course_title = parts[1].strip()
            else:
                course_title = raw_title
            continue

        # Textbooks section detection
        if stripped.lower().startswith("## textbooks") or stripped.lower().startswith(
            "### textbooks"
        ):
            in_textbooks_section = True
            current_topic = None
            continue

        # Module Header (Header 2)
        if stripped.startswith("## "):
            in_textbooks_section = False
            mod_title = stripped[3:].strip()
            mod_id = f"mod-{len(modules) + 1:02d}-{_slugify(mod_title)}"


            # Detect week number if present (e.g. Module 1: Basics (Week 1))
            week_match = re.search(r"(?i)\(week\s*(\d+)\)", mod_title)
            week_num = int(week_match.group(1)) if week_match else None

            current_module = ModuleNode(
                id=mod_id,
                title=mod_title,
                week_number=week_num,
                topics=[],
            )
            modules.append(current_module)
            current_topic = None
            continue

        # Topic Header (Header 3)
        if stripped.startswith("### "):
            in_textbooks_section = False
            top_title = stripped[4:].strip()
            mod_id = current_module.id if current_module else "mod-01"
            top_id = f"top-{_slugify(top_title)}"

            current_topic = TopicNode(
                id=top_id,
                title=top_title,
                module_id=mod_id,
                prerequisites=[],
                learning_objectives=[],
                readings=[],
            )
            if current_module is None:
                current_module = ModuleNode(
                    id=mod_id,
                    title="General Curriculum",
                    topics=[],
                )
                modules.append(current_module)
            current_module.topics.append(current_topic)
            continue

        # Bullet points: Textbooks, Objectives, Prerequisites, Readings
        if stripped.startswith("- ") or stripped.startswith("* "):
            bullet_text = stripped[2:].strip()

            if in_textbooks_section:
                textbooks.append(bullet_text)
                continue

            if current_topic is not None:
                lower_bullet = bullet_text.lower()
                if lower_bullet.startswith("prerequisites:") or lower_bullet.startswith("prereq:"):
                    raw_prereqs = bullet_text.split(":", 1)[1]
                    for p in raw_prereqs.split(","):
                        cleaned_p = p.strip()
                        if cleaned_p and cleaned_p.lower() != "none":
                            current_topic.prerequisites.append(cleaned_p)
                elif lower_bullet.startswith("objectives:") or lower_bullet.startswith(
                    "objective:"
                ):
                    raw_objs = bullet_text.split(":", 1)[1]
                    for o in raw_objs.split(","):
                        if o.strip():
                            current_topic.learning_objectives.append(o.strip())
                elif lower_bullet.startswith("readings:") or lower_bullet.startswith("reading:"):
                    raw_reads = bullet_text.split(":", 1)[1]
                    for r in raw_reads.split(","):
                        if r.strip():
                            current_topic.readings.append(r.strip())
                elif lower_bullet.startswith("exam weight:"):
                    weight_str = bullet_text.split(":", 1)[1].replace("%", "").strip()
                    try:
                        val = float(weight_str)
                        current_topic.exam_weight = val / 100.0 if val > 1.0 else val
                    except ValueError:
                        pass
                else:
                    # Generic objective / topic description
                    current_topic.learning_objectives.append(bullet_text)

    return CurriculumBackbone(
        course_code=course_code,
        course_title=course_title,
        textbooks=textbooks,
        modules=modules,
    )


def load_curriculum(syllabus_path: Path) -> CurriculumBackbone:
    """Load curriculum from either a Markdown file or JSON document."""
    syllabus_path = Path(syllabus_path)
    content = syllabus_path.read_text(encoding="utf-8")

    if syllabus_path.suffix.lower() == ".json":
        data = json.loads(content)
        return CurriculumBackbone.model_validate(data)

    return parse_syllabus_markdown(content)
