"""YouTube Transcript API service for fetching video transcripts."""

from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled

from uc_transcripts.models import Transcript, TranscriptSnippet


def fetch_transcript(video_id: str) -> Transcript:
    """
    Fetch transcript for a single video.

    Args:
        video_id: YouTube video ID

    Returns:
        Transcript object with metadata and snippets

    Raises:
        TranscriptsDisabled: If transcripts are not available for the video
    """
    api = YouTubeTranscriptApi()
    fetched = api.fetch(video_id, languages=("en", "en-GB"))

    snippets = [
        TranscriptSnippet(
            text=snippet["text"],
            start=snippet["start"],
            duration=snippet["duration"]
        )
        for snippet in fetched.to_raw_data()
    ]

    return Transcript(
        video_id=fetched.video_id,
        is_generated=fetched.is_generated,
        language=fetched.language,
        language_code=fetched.language_code,
        snippets=snippets,
        transcripts_disabled=False,
    )
