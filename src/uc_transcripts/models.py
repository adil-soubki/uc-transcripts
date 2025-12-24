"""Data models for University Challenge transcripts and questions."""

from dataclasses import dataclass, asdict, field
from typing import Optional, Literal


@dataclass
class VideoMetadata:
    """Metadata for a YouTube video."""

    video_id: str
    title: str
    published_at: str
    channel_handle: str
    channel_id: str
    uploads_playlist_id: str

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


@dataclass
class TranscriptSnippet:
    """A single snippet/segment of a video transcript."""

    text: str
    start: float
    duration: float


@dataclass
class Transcript:
    """YouTube video transcript with metadata."""

    video_id: str
    is_generated: bool
    language: str
    language_code: str
    snippets: list[TranscriptSnippet]
    transcripts_disabled: bool = False

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "video_id": self.video_id,
            "is_generated": self.is_generated,
            "language": self.language,
            "language_code": self.language_code,
            "snippets": [asdict(s) for s in self.snippets],
            "transcripts_disabled": self.transcripts_disabled,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Transcript":
        """Create Transcript from dictionary."""
        snippets = [TranscriptSnippet(**s) for s in data.get("snippets", [])]
        return cls(
            video_id=data["video_id"],
            is_generated=data["is_generated"],
            language=data["language"],
            language_code=data["language_code"],
            snippets=snippets,
            transcripts_disabled=data.get("transcripts_disabled", False),
        )


@dataclass
class QuestionCategory:
    """Category information for a question."""

    primary: Optional[str] = None
    secondary: Optional[list[str]] = None


@dataclass
class QuestionAttempt:
    """An attempt to answer a starter question."""

    team: Optional[str] = None
    attempted_answer: Optional[str] = None
    outcome: Optional[Literal["correct", "incorrect", "pass"]] = None


@dataclass
class StarterQuestion:
    """A starter question in University Challenge."""

    question_number: int
    type: Literal["starter"] = "starter"
    question_mode: Literal["text", "picture", "music"] = "text"
    question_text: Optional[str] = None
    full_question_read: bool = False
    attempts: list[QuestionAttempt] = field(default_factory=list)
    correct_answer: Optional[str] = None
    bonuses_awarded: bool = False
    category: Optional[dict] = None


@dataclass
class BonusPart:
    """A single part of a bonus question (a, b, or c)."""

    part: Literal["a", "b", "c"]
    text: Optional[str] = None
    attempted_answer: Optional[str] = None
    correct_answer: Optional[str] = None
    outcome: Optional[Literal["correct", "incorrect", "not_attempted"]] = None


@dataclass
class BonusQuestion:
    """A bonus question in University Challenge."""

    question_number: int
    type: Literal["bonus"] = "bonus"
    question_mode: Literal["text", "picture", "music"] = "text"
    intro_text: Optional[str] = None
    parts: list[BonusPart] = field(default_factory=list)
    category: Optional[dict] = None


@dataclass
class Episode:
    """University Challenge episode metadata."""

    series: Optional[int] = None
    episode: Optional[int] = None
    date: Optional[str] = None
    teams: Optional[list[str]] = None
