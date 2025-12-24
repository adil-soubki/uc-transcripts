#!/usr/bin/env python3
"""Fetch transcripts for YouTube videos."""

import argparse
import sys
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from youtube_transcript_api import TranscriptsDisabled

from uc_transcripts import (
    Config,
    set_config,
    get_videos_from_channel,
    fetch_transcript,
    save_json,
)


console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="Fetch transcripts for University Challenge videos",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch all transcripts (resumes from cache)
  python bin/fetch-transcripts.py --channel @CosmicPumpkin

  # Force re-fetch all transcripts
  python bin/fetch-transcripts.py --channel @CosmicPumpkin --force
""",
    )
    parser.add_argument(
        "--channel",
        required=True,
        help="YouTube channel handle (e.g., @CosmicPumpkin)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-fetch even if cached",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data"),
        help="Data directory (default: data/)",
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

    # Get videos
    console.print(f"[bold]Fetching video list from {args.channel}...[/bold]")
    try:
        videos = get_videos_from_channel(args.channel)
    except Exception as e:
        console.print(f"[red]Error fetching videos: {e}[/red]")
        return 1

    console.print(f"Found {len(videos)} videos\n")

    # Fetch transcripts with progress bar
    success_count = 0
    skip_count = 0
    error_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    ) as progress:
        task = progress.add_task("[cyan]Fetching transcripts...", total=len(videos))

        for video in videos:
            cache_path = config.transcripts_dir / f"{video.video_id}.json"

            # Skip if cached and not forcing
            if not args.force and cache_path.exists():
                progress.console.print(f"[dim]✓ Cached: {video.title[:60]}[/dim]")
                skip_count += 1
                progress.advance(task)
                continue

            # Fetch transcript
            try:
                transcript = fetch_transcript(video.video_id)
                combined_data = {
                    **video.to_dict(),
                    "transcript": transcript.to_dict(),
                }
                save_json(cache_path, combined_data)
                progress.console.print(f"[green]✓ Fetched: {video.title[:60]}[/green]")
                success_count += 1
            except TranscriptsDisabled:
                # Save metadata indicating transcripts are disabled
                combined_data = {
                    **video.to_dict(),
                    "transcript": {"transcripts_disabled": True},
                }
                save_json(cache_path, combined_data)
                progress.console.print(f"[yellow]⚠ No transcript: {video.title[:60]}[/yellow]")
                error_count += 1
            except Exception as e:
                progress.console.print(
                    f"[red]✗ Error ({video.video_id}): {video.title[:60]}: {e}[/red]"
                )
                error_count += 1

            progress.advance(task)

    # Summary
    console.print(f"\n[bold]Summary:[/bold]")
    console.print(f"  [green]Success: {success_count}[/green]")
    console.print(f"  [dim]Skipped (cached): {skip_count}[/dim]")
    console.print(f"  [yellow]Errors: {error_count}[/yellow]")

    return 0


if __name__ == "__main__":
    sys.exit(main())
