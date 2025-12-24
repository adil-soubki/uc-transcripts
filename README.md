# UC Transcripts

Fetch and parse University Challenge transcripts from YouTube into structured quiz question data.

## Overview

This project provides a clean pipeline to:
1. **Fetch video metadata** from YouTube channels using the YouTube Data API
2. **Download transcripts** for those videos using the YouTube Transcript API
3. **Parse transcripts** into structured question data using OpenAI's GPT models

The parsed data follows the QBReader taxonomy and includes detailed metadata about University Challenge episodes, starter questions, bonus questions, and their answers.

## Features

- **Clean CLI interface** with beautiful rich output (progress bars, tables)
- **Automatic caching** to avoid redundant API calls
- **Model-specific caching** - Each model gets its own output directory
- **Cost estimation** before running expensive OpenAI parsing
- **Configurable** with environment variables
- **Well-structured** codebase following DRY, YAGNI, and SOLID principles
- **Type-safe** with comprehensive type hints and dataclasses

## Project Structure

```
uc-transcripts/
├── src/uc_transcripts/      # Python package
│   ├── config.py             # Configuration management
│   ├── models.py             # Data models
│   ├── youtube.py            # YouTube API service
│   ├── transcripts.py        # Transcript fetching
│   ├── parser.py             # OpenAI parsing
│   ├── prompts.py            # LLM prompts
│   ├── cache.py              # Caching utilities
│   └── utils.py              # Shared utilities
├── bin/                      # CLI scripts
│   ├── fetch-videos.py
│   ├── fetch-transcripts.py
│   └── parse-questions.py
├── data/                     # Data directory (gitignored)
│   ├── videos/               # Video metadata CSVs
│   ├── transcripts/          # Raw transcript JSONs
│   └── questions/            # Parsed questions (organized by model)
│       ├── gpt-5.1/          # Questions parsed with gpt-5.1
│       ├── gpt-4o/           # Questions parsed with gpt-4o
│       └── gpt-4o-mini/      # Questions parsed with gpt-4o-mini
└── pyproject.toml            # Project configuration
```

## Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://docs.astral.sh/uv/) package manager
- YouTube Data API v3 key ([get one here](https://console.cloud.google.com/apis/credentials))
- OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### Installation

1. Clone the repository:
   ```bash
   cd /path/to/uc-transcripts
   ```

2. Install dependencies with uv:
   ```bash
   uv sync
   ```

3. Set up API keys:
   ```bash
   # Copy the example file
   cp .env.example .env

   # Edit .env and add your API keys
   # YOUTUBE_API_KEY=your-youtube-key-here
   # OPENAI_API_KEY=your-openai-key-here
   ```

## Usage

The scripts automatically load environment variables from `.env` using python-dotenv. You can run them in two ways:

**Option 1: Activate venv and run directly (simpler)**
```bash
source .venv/bin/activate
python bin/fetch-videos.py --channel @CosmicPumpkin
```

**Option 2: Use uv run (no activation needed)**
```bash
# Automatically uses .env
uv run python bin/fetch-videos.py --channel @CosmicPumpkin

# Or explicitly specify env file (useful for multiple env files)
uv run --env-file .env python bin/fetch-videos.py --channel @CosmicPumpkin
```

### 1. Fetch Video Metadata

```bash
# Fetch all videos from a channel
python bin/fetch-videos.py --channel @CosmicPumpkin
```

**Output:**
- CSV file: `data/videos/CosmicPumpkin_videos.csv`
- Rich table showing video details

### 2. Fetch Transcripts

```bash
# Download transcripts for all videos (uses cache)
python bin/fetch-transcripts.py --channel @CosmicPumpkin

# Force re-fetch all transcripts
python bin/fetch-transcripts.py --channel @CosmicPumpkin --force
```

**Output:**
- JSON files: `data/transcripts/{video_id}.json`
- Progress bar with status for each video
- Summary of successes/skips/errors

### 3. Parse Questions with OpenAI

```bash
# Estimate cost first (recommended!)
python bin/parse-questions.py --estimate

# Parse all transcripts with default model (gpt-5.1)
python bin/parse-questions.py

# Use a different model
python bin/parse-questions.py --model gpt-4o

# Parse a specific video
python bin/parse-questions.py --video-id 4IeES6Q0NNU
```

**Output:**
- JSON files: `data/questions/{model}/{video_id}.json`
- Each model gets its own subdirectory (prevents mixing)
- Progress bar during parsing
- Summary of successes/skips/errors

**Note:** Different models create separate caches:
- `gpt-5.1` → `data/questions/gpt-5.1/`
- `gpt-4o` → `data/questions/gpt-4o/`
- This allows you to compare outputs from different models

## Data Format

### Transcript JSON (`data/transcripts/{video_id}.json`)

```json
{
  "video_id": "4IeES6Q0NNU",
  "title": "University Challenge S55E23 - Lincoln v UCL",
  "published_at": "2025-12-15T21:23:39Z",
  "channel_handle": "CosmicPumpkin",
  "channel_id": "UCkhkV9d_BWQx3Y-C_4aG0lg",
  "uploads_playlist_id": "UUkhkV9d_BWQx3Y-C_4aG0lg",
  "transcript": {
    "video_id": "4IeES6Q0NNU",
    "is_generated": true,
    "language": "English (auto-generated)",
    "language_code": "en",
    "snippets": [
      {"text": "Good evening.", "start": 0.0, "duration": 1.5},
      ...
    ]
  }
}
```

### Parsed Questions JSON (`data/questions/{model}/{video_id}.json`)

```json
{
  "episode": {
    "series": 55,
    "episode": 23,
    "date": "2025-12-15",
    "teams": ["Lincoln", "UCL"]
  },
  "questions": [
    {
      "question_number": 1,
      "type": "starter",
      "question_mode": "text",
      "question_text": "Which element has atomic number 79?",
      "full_question_read": true,
      "attempts": [
        {
          "team": "Lincoln",
          "attempted_answer": "Gold",
          "outcome": "correct"
        }
      ],
      "correct_answer": "Gold",
      "bonuses_awarded": true,
      "category": {
        "primary": "Science",
        "secondary": ["Chemistry"]
      }
    },
    {
      "question_number": 1,
      "type": "bonus",
      "question_mode": "text",
      "intro_text": "Bonuses on chemistry",
      "parts": [
        {
          "part": "a",
          "text": "What is the symbol for gold?",
          "attempted_answer": "Au",
          "correct_answer": "Au",
          "outcome": "correct"
        },
        ...
      ],
      "category": {
        "primary": "Science",
        "secondary": ["Chemistry"]
      }
    }
  ]
}
```

## Model-Specific Output Directories

Each model automatically gets its own output directory to prevent mixing results:

```bash
# Parse with gpt-5.1
python bin/parse-questions.py --model gpt-5.1
# Output: data/questions/gpt-5.1/{video_id}.json

# Parse with gpt-4o
python bin/parse-questions.py --model gpt-4o
# Output: data/questions/gpt-4o/{video_id}.json

# Parse with gpt-4o-mini
python bin/parse-questions.py --model gpt-4o-mini
# Output: data/questions/gpt-4o-mini/{video_id}.json
```

**Benefits:**
- ✅ No risk of mixing outputs from different models
- ✅ Easy to compare results side-by-side
- ✅ Each model has independent cache
- ✅ Can re-parse with different model without `--force`

## Configuration

### Environment Variables

Set these in your `.env` file:

- `YOUTUBE_API_KEY` - YouTube Data API v3 key (required)
- `OPENAI_API_KEY` - OpenAI API key (required)
- `UC_DATA_DIR` - Custom data directory (optional, default: `data/`)

### Cost Estimation

Before parsing transcripts with OpenAI, always estimate the cost:

```bash
uv run --env-file .env python bin/parse-questions.py --estimate
```

Example output:
```
╭─────────────────── Cost Estimation ────────────────────╮
│ Metric             │ Value                             │
├────────────────────┼───────────────────────────────────┤
│ Model              │ gpt-5.1                           │
│ Transcripts        │ 242                               │
│ Input Tokens       │ 1,385,665                         │
│ Output Tokens      │ 363,000                           │
│ Input Cost         │ $1.7321                           │
│ Output Cost        │ $3.6300                           │
│ Total Cost         │ $5.3621                           │
╰────────────────────┴───────────────────────────────────╯
```

## Library Usage

You can also use this as a Python library:

```python
from uc_transcripts import (
    Config,
    set_config,
    get_videos_from_channel,
    fetch_transcript,
    parse_transcript,
)

# Initialize config
config = Config()
config.validate()
set_config(config)

# Fetch videos
videos = get_videos_from_channel("@CosmicPumpkin")

# Fetch a transcript
transcript = fetch_transcript(videos[0].video_id)

# Parse with OpenAI
parsed = parse_transcript(
    video_id=videos[0].video_id,
    transcript=transcript,
    video_metadata=videos[0],
    model="gpt-5.1",
)
```

## Development

### Install dev dependencies

```bash
uv sync --group dev
```

### Run linter

```bash
uv run ruff check src/ bin/
```

### Format code

```bash
uv run ruff format src/ bin/
```

## Design Principles

This project follows:

- **DRY (Don't Repeat Yourself)**: Shared utilities, centralized config
- **YAGNI (You Aren't Gonna Need It)**: Simple, focused features
- **SOLID**: Single responsibility, dependency inversion, etc.

## Architecture

- **Config Layer** (`config.py`): Centralized configuration with validation
- **Data Layer** (`models.py`): Type-safe dataclasses for all domain objects
- **Service Layer** (`youtube.py`, `transcripts.py`, `parser.py`): Business logic
- **Utilities** (`cache.py`, `utils.py`): Cross-cutting concerns
- **CLI Layer** (`bin/*.py`): User-facing command-line interface

## License

This project is for educational and research purposes.

## Acknowledgments

- YouTube Data API for video metadata
- YouTube Transcript API for captions
- OpenAI GPT models for parsing
- QBReader for the category taxonomy
- CosmicPumpkin YouTube channel for University Challenge episodes
