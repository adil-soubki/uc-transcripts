"""YouTube Data API service for fetching video metadata."""

from googleapiclient.discovery import build

from uc_transcripts.config import get_config
from uc_transcripts.models import VideoMetadata


def build_youtube_client():
    """
    Build YouTube API client with configured API key.

    Returns:
        YouTube API client instance
    """
    config = get_config()
    return build("youtube", "v3", developerKey=config.youtube_api_key)


def get_channel_id_from_handle(handle: str) -> str:
    """
    Resolve channel handle (e.g., @CosmicPumpkin) to channel ID.

    Args:
        handle: YouTube channel handle

    Returns:
        Channel ID string
    """
    youtube = build_youtube_client()
    request = youtube.search().list(
        part="snippet",
        q=handle,
        type="channel",
        maxResults=1
    )
    response = request.execute()
    return response["items"][0]["snippet"]["channelId"]


def get_uploads_playlist_id(channel_id: str) -> str:
    """
    Get the uploads playlist ID for a channel.

    Args:
        channel_id: YouTube channel ID

    Returns:
        Uploads playlist ID
    """
    youtube = build_youtube_client()
    request = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    )
    response = request.execute()

    uploads_playlist_id = (
        response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    )
    return uploads_playlist_id


def get_videos_from_playlist(
    playlist_id: str,
    channel_handle: str,
    channel_id: str
) -> list[VideoMetadata]:
    """
    Fetch all videos from a playlist with pagination.

    Args:
        playlist_id: YouTube playlist ID
        channel_handle: Channel handle for metadata
        channel_id: Channel ID for metadata

    Returns:
        List of VideoMetadata objects
    """
    youtube = build_youtube_client()
    videos = []
    next_page_token = None

    while True:
        request = youtube.playlistItems().list(
            part="snippet",
            playlistId=playlist_id,
            maxResults=50,
            pageToken=next_page_token
        )
        response = request.execute()

        for item in response["items"]:
            video_id = item["snippet"]["resourceId"]["videoId"]
            title = item["snippet"]["title"]
            published_at = item["snippet"]["publishedAt"]

            videos.append(VideoMetadata(
                video_id=video_id,
                title=title,
                published_at=published_at,
                channel_handle=channel_handle,
                channel_id=channel_id,
                uploads_playlist_id=playlist_id,
            ))

        next_page_token = response.get("nextPageToken")
        if not next_page_token:
            break

    return videos


def get_videos_from_channel(channel_handle: str) -> list[VideoMetadata]:
    """
    High-level function to fetch all videos from a channel.

    Args:
        channel_handle: YouTube channel handle (e.g., @CosmicPumpkin)

    Returns:
        List of VideoMetadata objects
    """
    channel_id = get_channel_id_from_handle(channel_handle)
    uploads_playlist_id = get_uploads_playlist_id(channel_id)
    videos = get_videos_from_playlist(
        uploads_playlist_id,
        channel_handle,
        channel_id
    )
    return videos
