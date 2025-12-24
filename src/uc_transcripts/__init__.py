"""UC Transcripts - Fetch and parse University Challenge transcripts."""

__version__ = "0.1.0"

from uc_transcripts.config import Config, get_config, set_config
from uc_transcripts.models import (
    VideoMetadata,
    Transcript,
    TranscriptSnippet,
    Episode,
    StarterQuestion,
    BonusQuestion,
    BonusPart,
    QuestionAttempt,
)
from uc_transcripts.youtube import get_videos_from_channel
from uc_transcripts.transcripts import fetch_transcript
from uc_transcripts.parser import parse_transcript, estimate_parsing_cost, count_tokens
from uc_transcripts.cache import load_json, save_json, with_cache
from uc_transcripts.utils import zip_directory, unzip_file

__all__ = [
    # Version
    "__version__",
    # Config
    "Config",
    "get_config",
    "set_config",
    # Models
    "VideoMetadata",
    "Transcript",
    "TranscriptSnippet",
    "Episode",
    "StarterQuestion",
    "BonusQuestion",
    "BonusPart",
    "QuestionAttempt",
    # YouTube API
    "get_videos_from_channel",
    # Transcripts
    "fetch_transcript",
    # Parser
    "parse_transcript",
    "estimate_parsing_cost",
    "count_tokens",
    # Cache
    "load_json",
    "save_json",
    "with_cache",
    # Utils
    "zip_directory",
    "unzip_file",
]
