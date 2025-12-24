"""Configuration management for UC Transcripts."""

import os
from pathlib import Path
from typing import Optional


class Config:
    """
    Centralized configuration for UC Transcripts.

    Loads API keys from environment variables and manages data directories.
    """

    def __init__(
        self,
        youtube_api_key: Optional[str] = None,
        openai_api_key: Optional[str] = None,
        data_dir: Optional[str] = None,
    ):
        """
        Initialize configuration.

        Args:
            youtube_api_key: YouTube Data API v3 key (defaults to YOUTUBE_API_KEY env var)
            openai_api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            data_dir: Data directory path (defaults to UC_DATA_DIR env var or 'data/')
        """
        self.youtube_api_key = youtube_api_key or os.getenv("YOUTUBE_API_KEY")
        self.openai_api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.data_dir = Path(data_dir or os.getenv("UC_DATA_DIR", "data"))

    @property
    def videos_dir(self) -> Path:
        """Directory for video metadata CSV files."""
        return self.data_dir / "videos"

    @property
    def transcripts_dir(self) -> Path:
        """Directory for raw transcript JSON files."""
        return self.data_dir / "transcripts"

    def questions_dir(self, model: str) -> Path:
        """Directory for parsed question JSON files."""
        return self.data_dir / "questions" / model

    def validate(self) -> None:
        """
        Validate configuration and create necessary directories.

        Raises:
            ValueError: If required API keys are not set
        """
        if not self.youtube_api_key:
            raise ValueError(
                "YOUTUBE_API_KEY not set. "
                "Set it in .env file or pass to Config constructor."
            )
        if not self.openai_api_key:
            raise ValueError(
                "OPENAI_API_KEY not set. "
                "Set it in .env file or pass to Config constructor."
            )

        # Create data directories if they don't exist
        self.videos_dir.mkdir(parents=True, exist_ok=True)
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        # Note: questions_dir is created on-demand per model


# Global config singleton
_config: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global Config instance.

    Returns:
        The global Config instance

    Raises:
        RuntimeError: If config not initialized. Call set_config() first.
    """
    if _config is None:
        raise RuntimeError("Config not initialized. Call set_config() first.")
    return _config


def set_config(config: Config) -> None:
    """
    Set the global Config instance.

    Args:
        config: Config instance to set as global
    """
    global _config
    _config = config
