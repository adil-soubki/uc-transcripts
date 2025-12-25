#!/usr/bin/env python3
"""Parse transcripts into structured questions using OpenAI."""

import argparse
import asyncio
import sys
from pathlib import Path

from dotenv import load_dotenv
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.table import Table

from uc_transcripts import (
    Config,
    set_config,
    load_json,
    save_json,
    parse_transcript_async,
    estimate_parsing_cost,
    VideoMetadata,
    Transcript,
)

# Load environment variables from .env file
load_dotenv()

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="Parse UC transcripts into structured questions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Estimate cost before running
  python bin/parse-questions.py --estimate

  # Parse all transcripts
  python bin/parse-questions.py

  # Use different model
  python bin/parse-questions.py --model gpt-4o

  # Parse specific video
  python bin/parse-questions.py --video-id 4IeES6Q0NNU
""",
    )
    parser.add_argument(
        "--video-id",
        help="Process specific video ID",
    )
    parser.add_argument(
        "--estimate",
        action="store_true",
        help="Estimate cost without parsing",
    )
    parser.add_argument(
        "--model",
        default="gpt-5.1",
        help="OpenAI model to use (default: gpt-5.1)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-parse even if cached",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Data directory (default: data/)",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=5,
        help="Number of concurrent workers (default: 5)",
    )

    args = parser.parse_args()

    # Initialize config
    try:
        config = Config(data_dir=str(args.data_dir))
        config.validate()
        set_config(config)
    except ValueError as e:
        console.print(f"[red]Error: {e}[/red]")
        return 1

    # Show which model directory will be used
    questions_output_dir = config.questions_dir(args.model)
    console.print(f"[dim]Output directory: {questions_output_dir}[/dim]\n")

    # Get list of transcripts to process
    if args.video_id:
        transcript_files = [config.transcripts_dir / f"{args.video_id}.json"]
    else:
        transcript_files = list(config.transcripts_dir.glob("*.json"))

    if not transcript_files:
        console.print("[yellow]No transcript files found[/yellow]")
        return 1

    # Filter out disabled transcripts
    valid_transcripts = []
    for path in transcript_files:
        data = load_json(path)
        if data and not data.get("transcript", {}).get("transcripts_disabled", False):
            valid_transcripts.append((path, data))

    console.print(f"Found {len(valid_transcripts)} valid transcripts\n")

    # Cost estimation
    if args.estimate:
        console.print(f"[bold]Estimating cost for {args.model}...[/bold]\n")
        transcript_data_list = [data for _, data in valid_transcripts]
        cost = estimate_parsing_cost(transcript_data_list, model=args.model)

        table = Table(title="Cost Estimation")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        table.add_row("Model", cost["model"])
        table.add_row("Transcripts", str(cost["num_transcripts"]))
        table.add_row("Input Tokens", f"{cost['total_input_tokens']:,}")
        table.add_row("Output Tokens (est.)", f"{cost['total_output_tokens']:,}")
        table.add_row("Input Cost", f"${cost['estimated_input_cost']:.4f}")
        table.add_row("Output Cost", f"${cost['estimated_output_cost']:.4f}")
        table.add_row("Total Cost", f"${cost['estimated_total_cost']:.4f}")

        console.print(table)
        return 0

    # Parse transcripts with async/concurrent processing
    async def parse_one(semaphore, transcript_path, data, progress_obj, task_id):
        """Parse a single transcript with concurrency control."""
        nonlocal success_count, skip_count, error_count

        video_id = transcript_path.stem
        output_path = config.questions_dir(args.model) / f"{video_id}.json"

        # Skip if cached
        if not args.force and output_path.exists():
            progress_obj.console.print(f"[dim]✓ Cached: {data['title'][:60]}[/dim]")
            skip_count += 1
            progress_obj.advance(task_id)
            return

        # Parse with semaphore to limit concurrency
        async with semaphore:
            try:
                video_metadata = VideoMetadata(**{
                    k: data[k]
                    for k in [
                        "video_id",
                        "title",
                        "published_at",
                        "channel_handle",
                        "channel_id",
                        "uploads_playlist_id",
                    ]
                })
                transcript = Transcript.from_dict(data["transcript"])

                parsed = await parse_transcript_async(
                    video_id=video_id,
                    transcript=transcript,
                    video_metadata=video_metadata,
                    model=args.model,
                )
                save_json(output_path, parsed)
                progress_obj.console.print(f"[green]✓ Parsed: {data['title'][:60]}[/green]")
                success_count += 1
            except Exception as e:
                progress_obj.console.print(f"[red]✗ Error ({video_id}): {e}[/red]")
                error_count += 1

            progress_obj.advance(task_id)

    async def run_parsing():
        """Run all parsing tasks concurrently."""
        semaphore = asyncio.Semaphore(args.workers)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            console=console,
        ) as progress:
            task = progress.add_task(
                f"[cyan]Parsing transcripts ({args.workers} workers)...",
                total=len(valid_transcripts)
            )

            # Create all tasks
            tasks = [
                parse_one(semaphore, transcript_path, data, progress, task)
                for transcript_path, data in valid_transcripts
            ]

            # Run all tasks concurrently
            await asyncio.gather(*tasks)

    success_count = 0
    skip_count = 0
    error_count = 0

    # Run the async parsing
    asyncio.run(run_parsing())

    # Summary
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  [green]Success: {success_count}[/green]")
    console.print(f"  [dim]Skipped (cached): {skip_count}[/dim]")
    console.print(f"  [red]Errors: {error_count}[/red]")

    if success_count > 0:
        console.print(f"\n[bold green]✓ Parsing complete![/bold green]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
