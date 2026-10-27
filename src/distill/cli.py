"""Unified command-line interface for Distill Study Compiler."""

from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from distill.pipeline import DistillPipeline

console = Console()


def _run_audit(pipeline: DistillPipeline) -> None:
    chunks = pipeline.run_ingestion()
    backbone, _ordered_topics, _mapping, coverage = pipeline.run_clustering(chunks)

    title_suffix = f" [{pipeline.subject}]" if pipeline.subject else ""
    table_title = f"Coverage Audit: {backbone.course_code} {backbone.course_title}{title_suffix}"
    table = Table(title=table_title)
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="bold green")

    table.add_row("Total Syllabus Topics", str(coverage.total_syllabus_topics))
    table.add_row(
        "Covered Topics",
        f"{coverage.covered_topic_count} ({coverage.coverage_percentage}%)",
    )
    table.add_row("Whiteboard Gap Topics", str(coverage.uncovered_topic_count))
    table.add_row("Extracted Slide Chunks", str(len(chunks)))

    console.print(table)
    if coverage.uncovered_topics:
        gap_count = len(coverage.uncovered_topics)
        console.print(
            f"[bold yellow]Whiteboard Gaps ({gap_count}):[/bold yellow] "
            + ", ".join(coverage.uncovered_topics)
        )


def _run_synthesize(pipeline: DistillPipeline) -> None:
    chunks = pipeline.run_ingestion()
    backbone, ordered_topics, mapping, coverage = pipeline.run_clustering(chunks)
    files = pipeline.run_synthesis(backbone, ordered_topics, mapping, coverage)
    pipeline.manifest.save_atomic(pipeline.manifest_path)
    count = len(files)
    tag = f" [{pipeline.subject}]" if pipeline.subject else ""
    loc = f"03_study_guide/{pipeline.subject}/" if pipeline.subject else "03_study_guide/"
    console.print(f"[bold green]Synthesis complete{tag}:[/bold green] {count} chapters in {loc}.")


def _run_compile(pipeline: DistillPipeline) -> None:
    chunks = pipeline.run_ingestion()
    backbone, ordered_topics, mapping, _coverage = pipeline.run_clustering(chunks)
    decks = pipeline.run_compilation(ordered_topics, mapping)
    deck_count = len(decks)
    tag = f" [{pipeline.subject}]" if pipeline.subject else ""
    loc = f"04_unified_decks/{pipeline.subject}/" if pipeline.subject else "04_unified_decks/"
    msg = f"[bold green]Compilation complete{tag}:[/bold green] {deck_count} decks in {loc}."
    console.print(msg)


@click.group()
def cli() -> None:
    """Distill: Map-Reduce & Knowledge-Graph Synthesis Pipeline for PowerPoint Decks."""


@cli.command("run")
@click.option("--subject", "-s", default=None, help="Target specific subject across stage folders.")
@click.option("--force", is_flag=True, help="Force rebuild, ignoring build cache.")
def run_command(subject: str | None, force: bool) -> None:
    """Run the complete end-to-end distillation pipeline."""
    subjects = [subject] if subject else DistillPipeline.list_subjects()

    if not subjects:
        # Check flat/root mode
        pipeline = DistillPipeline()
        if list(pipeline.inbox_dir.glob("*.pptx")):
            console.print(
                Panel.fit(
                    "[bold cyan]Distill Study Compiler[/bold cyan]\n"
                    "Ingestion -> Clustering -> Synthesis -> Compilation (Root/Flat mode)",
                    border_style="cyan",
                )
            )
            pipeline.run_all(force=force)
            console.print("[bold green]SUCCESS:[/bold green] All stages completed successfully!")
            return

        console.print(
            "[bold yellow]No subjects or presentations found.[/bold yellow]\n"
            "Create a subject folder using: [bold cyan]distill new-subject <name>[/bold cyan]\n"
            "Or drop .pptx decks into: [bold cyan]00_inbox_ppts/<subject>/[/bold cyan]"
        )
        return

    for subj in subjects:
        header = (
            f"[bold cyan]Distill Study Compiler[/bold cyan] "
            f"(Subject: [bold yellow]{subj}[/bold yellow])\n"
            "Executing Ingestion -> Clustering -> Synthesis -> Compilation"
        )
        console.print(Panel.fit(header, border_style="cyan"))
        pipeline = DistillPipeline(subject=subj)
        pipeline.run_all(force=force)
        console.print(f"[bold green]SUCCESS [{subj}]:[/bold green] Completed successfully!\n")


@cli.command("ingest")
@click.option("--subject", "-s", default=None, help="Target specific subject across stage folders.")
@click.option("--force", is_flag=True, help="Force re-extraction of all decks.")
def ingest_command(subject: str | None, force: bool) -> None:
    """Stage 1: Extract slide chunks, tables, OpenXML diagrams, and assets."""
    subjects = [subject] if subject else DistillPipeline.list_subjects()
    if not subjects:
        pipeline = DistillPipeline()
        chunks = pipeline.run_ingestion(force=force)
        pipeline.manifest.save_atomic(pipeline.manifest_path)
        console.print(
            f"[bold green]Ingestion complete:[/bold green] {len(chunks)} slide chunks extracted."
        )
        return

    for subj in subjects:
        pipeline = DistillPipeline(subject=subj)
        chunks = pipeline.run_ingestion(force=force)
        pipeline.manifest.save_atomic(pipeline.manifest_path)
        inbox_rel = f"00_inbox_ppts/{subj}/"
        console.print(
            f"[bold green]Ingestion complete [{subj}]:[/bold green] "
            f"{len(chunks)} slide chunks extracted from {inbox_rel}."
        )


@cli.command("audit")
@click.option("--subject", "-s", default=None, help="Target specific subject across stage folders.")
def audit_command(subject: str | None) -> None:
    """Stage 2: Audit curriculum coverage and identify whiteboard gaps."""
    subjects = [subject] if subject else DistillPipeline.list_subjects()
    if not subjects:
        _run_audit(DistillPipeline())
        return

    for subj in subjects:
        _run_audit(DistillPipeline(subject=subj))


@cli.command("synthesize")
@click.option("--subject", "-s", default=None, help="Target specific subject across stage folders.")
def synthesize_command(subject: str | None) -> None:
    """Stage 3 & 4: Synthesize 4-tier textbook study chapters."""
    subjects = [subject] if subject else DistillPipeline.list_subjects()
    if not subjects:
        _run_synthesize(DistillPipeline())
        return

    for subj in subjects:
        _run_synthesize(DistillPipeline(subject=subj))


@cli.command("compile")
@click.option("--subject", "-s", default=None, help="Target specific subject across stage folders.")
def compile_command(subject: str | None) -> None:
    """Stage 5: Compile Marp presentation decks."""
    subjects = [subject] if subject else DistillPipeline.list_subjects()
    if not subjects:
        _run_compile(DistillPipeline())
        return

    for subj in subjects:
        _run_compile(DistillPipeline(subject=subj))


@cli.command("new-subject")
@click.argument("name")
def new_subject_command(name: str) -> None:
    """Scaffold stage directories for a new subject (00_inbox_ppts/<name>, etc.)."""
    created = DistillPipeline.init_subject_structure(name)
    console.print(f"[bold green]Initialized subject '{name}' across stage folders:[/bold green]")
    for stage, path in created.items():
        console.print(f"  - [cyan]{stage}:[/cyan] {path}")


@cli.command("subjects")
def subjects_command() -> None:
    """List all configured subjects across stage folders."""
    subjects = DistillPipeline.list_subjects()
    if not subjects:
        console.print("[yellow]No subjects discovered in stage folders.[/yellow]")
        return
    table = Table(title="Configured Subjects")
    table.add_column("Subject Name", style="cyan")
    table.add_column("Inbox Directory", style="green")
    table.add_column("Study Guide Directory", style="magenta")
    for s in subjects:
        table.add_row(
            s,
            f"00_inbox_ppts/{s}/",
            f"03_study_guide/{s}/",
        )
    console.print(table)


if __name__ == "__main__":
    cli()
