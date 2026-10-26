"""Unified command-line interface for Distill Study Compiler."""

from __future__ import annotations

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from distill.pipeline import DistillPipeline

console = Console()


@click.group()
def cli() -> None:
    """Distill: Map-Reduce & Knowledge-Graph Synthesis Pipeline for PowerPoint Decks."""


@cli.command("run")
@click.option("--force", is_flag=True, help="Force rebuild, ignoring build cache.")
def run_command(force: bool) -> None:
    """Run the complete end-to-end distillation pipeline."""
    console.print(
        Panel.fit(
            "[bold cyan]Distill Study Compiler[/bold cyan]\n"
            "Executing Ingestion -> Clustering -> Synthesis -> Compilation",
            border_style="cyan",
        )
    )
    pipeline = DistillPipeline()
    pipeline.run_all(force=force)
    console.print("[bold green]SUCCESS:[/bold green] All stages completed successfully!")


@cli.command("ingest")
@click.option("--force", is_flag=True, help="Force re-extraction of all decks.")
def ingest_command(force: bool) -> None:
    """Stage 1: Extract slide chunks, tables, OpenXML diagrams, and assets."""
    pipeline = DistillPipeline()
    chunks = pipeline.run_ingestion(force=force)
    pipeline.manifest.save_atomic(pipeline.manifest_path)
    console.print(
        f"[bold green]Ingestion complete:[/bold green] {len(chunks)} slide chunks extracted."
    )


@cli.command("audit")
def audit_command() -> None:
    """Stage 2: Audit curriculum coverage and identify whiteboard gaps."""
    pipeline = DistillPipeline()
    chunks = pipeline.run_ingestion()
    backbone, ordered_topics, mapping, coverage = pipeline.run_clustering(chunks)

    table = Table(title=f"Coverage Audit: {backbone.course_code} {backbone.course_title}")
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


@cli.command("synthesize")
def synthesize_command() -> None:
    """Stage 3 & 4: Synthesize 4-tier textbook study chapters."""
    pipeline = DistillPipeline()
    chunks = pipeline.run_ingestion()
    backbone, ordered_topics, mapping, coverage = pipeline.run_clustering(chunks)
    files = pipeline.run_synthesis(backbone, ordered_topics, mapping, coverage)
    pipeline.manifest.save_atomic(pipeline.manifest_path)
    count = len(files)
    console.print(
        f"[bold green]Synthesis complete:[/bold green] {count} chapters in 03_study_guide/."
    )


@cli.command("compile")
def compile_command() -> None:
    """Stage 5: Compile Marp presentation decks."""
    pipeline = DistillPipeline()
    chunks = pipeline.run_ingestion()
    backbone, ordered_topics, mapping, coverage = pipeline.run_clustering(chunks)
    decks = pipeline.run_compilation(ordered_topics, mapping)
    deck_count = len(decks)
    console.print(
        f"[bold green]Compilation complete:[/bold green] {deck_count} decks in 04_unified_decks/."
    )


if __name__ == "__main__":
    cli()
