#!/usr/bin/env python3
"""Fetch video metadata from YouTube channel."""

import argparse
import sys
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from rich.console import Console
from rich.table import Table

from uc_transcripts import Config, set_config, get_videos_from_channel

# Load environment variables from .env file
load_dotenv()

console = Console()


def main():
    parser = argparse.ArgumentParser(
        description="Fetch University Challenge video metadata from YouTube",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Fetch videos from a channel
  python bin/fetch-videos.py --channel @CosmicPumpkin

  # Custom data directory
  python bin/fetch-videos.py --channel @CosmicPumpkin --data-dir ./my-data
""",
    )
    parser.add_argument(
        "--channel",
        required=True,
        help="YouTube channel handle (e.g., @CosmicPumpkin)",
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

    # Fetch videos
    console.print(f"[bold]Fetching videos from {args.channel}...[/bold]")

    try:
        videos = get_videos_from_channel(args.channel)
    except Exception as e:
        console.print(f"[red]Error fetching videos: {e}[/red]")
        return 1

    # Save to CSV
    channel_name = args.channel.replace("@", "")
    csv_path = config.videos_dir / f"{channel_name}_videos.csv"

    df = pd.DataFrame([v.to_dict() for v in videos])
    df.to_csv(csv_path, index=False)

    console.print(f"\n[green]✓ Saved {len(videos)} videos to {csv_path}[/green]")

    # Display summary table
    table = Table(title=f"Videos from {args.channel}")
    table.add_column("Video ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Published", style="dim")

    for video in videos[:10]:  # Show first 10
        table.add_row(video.video_id, video.title[:60], video.published_at[:10])

    if len(videos) > 10:
        table.add_row("...", f"... and {len(videos) - 10} more videos", "...")

    console.print(table)

    return 0


if __name__ == "__main__":
    sys.exit(main())
