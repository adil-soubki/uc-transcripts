"""OpenAI parsing service for transcript analysis."""

import json
import openai
import tiktoken

from uc_transcripts.config import get_config
from uc_transcripts.models import Transcript, VideoMetadata
from uc_transcripts.prompts import build_uc_parse_prompt


# Pricing per 1k tokens
PRICING = {
    "gpt-5.1": {"input": 0.00125, "output": 0.01000},
    "gpt-5-mini": {"input": 0.00025, "output": 0.002},
    "gpt-5-nano": {"input": 0.00005, "output": 0.0004},
    "gpt-4o": {"input": 0.0025, "output": 0.01},
    "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
}


def get_openai_client():
    """
    Get configured OpenAI client.

    Returns:
        OpenAI client instance
    """
    config = get_config()
    return openai.OpenAI(api_key=config.openai_api_key)


def parse_transcript(
    video_id: str,
    transcript: Transcript,
    video_metadata: VideoMetadata,
    model: str = "gpt-5.1",
    temperature: float = 0.0,
) -> dict:
    """
    Parse transcript into structured questions using OpenAI.

    Args:
        video_id: YouTube video ID
        transcript: Transcript object
        video_metadata: Video metadata (title, date, etc.)
        model: OpenAI model to use
        temperature: Sampling temperature (0.0 for deterministic)

    Returns:
        Parsed episode data as dict

    Raises:
        RuntimeError: If JSON parsing fails
    """
    client = get_openai_client()
    prompt = build_uc_parse_prompt(transcript, video_metadata)

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a careful data extraction system."},
                {"role": "user", "content": prompt}
            ],
            temperature=temperature,
        )
    except openai.BadRequestError as e:
        # Handle model that doesn't support temperature parameter
        if "temperature" in str(e):
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a careful data extraction system."},
                    {"role": "user", "content": prompt}
                ],
            )
        else:
            raise

    raw_json = response.choices[0].message.content

    try:
        return json.loads(raw_json)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Invalid JSON from model for {video_id}") from e


def count_tokens(text: str, model: str) -> int:
    """
    Count tokens for cost estimation.

    Args:
        text: Text to count tokens for
        model: Model name for encoding

    Returns:
        Number of tokens
    """
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        encoding = tiktoken.get_encoding("cl100k_base")

    return len(encoding.encode(text))


def estimate_parsing_cost(
    transcripts: list[dict],
    model: str = "gpt-5.1",
    avg_output_tokens: int = 9000,
) -> dict:
    """
    Estimate total cost of parsing all transcripts.

    Args:
        transcripts: List of transcript data dicts
        model: OpenAI model to use
        avg_output_tokens: Estimated output tokens per transcript

    Returns:
        Dict with cost estimation details
    """
    total_input_tokens = 0
    total_output_tokens = avg_output_tokens * len(transcripts)

    for transcript_data in transcripts:
        # Build prompt to count tokens
        video_metadata = VideoMetadata(**{
            k: transcript_data[k]
            for k in ["video_id", "title", "published_at", "channel_handle",
                      "channel_id", "uploads_playlist_id"]
        })
        transcript = Transcript.from_dict(transcript_data["transcript"])
        prompt = build_uc_parse_prompt(transcript, video_metadata)
        total_input_tokens += count_tokens(prompt, model)

    try:
        pricing = PRICING[model]
    except KeyError as err:
        err.add_note(
            f"No pricing information entered for {model} in {__file__}. "
            f"See https://platform.openai.com/docs/pricing for details."
        )
        raise
    input_cost = (total_input_tokens / 1000) * pricing["input"]
    output_cost = (total_output_tokens / 1000) * pricing["output"]

    return {
        "model": model,
        "num_transcripts": len(transcripts),
        "total_input_tokens": total_input_tokens,
        "total_output_tokens": total_output_tokens,
        "estimated_input_cost": round(input_cost, 4),
        "estimated_output_cost": round(output_cost, 4),
        "estimated_total_cost": round(input_cost + output_cost, 4),
    }
