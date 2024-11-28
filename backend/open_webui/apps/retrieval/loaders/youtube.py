from typing import Any, Dict, Generator, List, Optional, Sequence, Union
from urllib.parse import parse_qs, urlparse
from langchain_core.documents import Document


ALLOWED_SCHEMES = {"http", "https"}
ALLOWED_NETLOCS = {
    "youtu.be",
    "m.youtube.com",
    "youtube.com",
    "www.youtube.com",
    "www.youtube-nocookie.com",
    "vid.plus",
}


def _parse_video_id(url: str) -> Optional[str]:
    """Parse a YouTube URL and return the video ID if valid, otherwise None."""
    parsed_url = urlparse(url)

    if parsed_url.scheme not in ALLOWED_SCHEMES:
        return None

    if parsed_url.netloc not in ALLOWED_NETLOCS:
        return None

    path = parsed_url.path

    if path.endswith("/watch"):
        query = parsed_url.query
        parsed_query = parse_qs(query)
        if "v" in parsed_query:
            ids = parsed_query["v"]
            video_id = ids if isinstance(ids, str) else ids[0]
        else:
            return None
    else:
        path = parsed_url.path.lstrip("/")
        video_id = path.split("/")[-1]

    if len(video_id) != 11:  # Video IDs are 11 characters long
        return None

    return video_id


class YoutubeLoader:
    """Load `YouTube` video transcripts."""

    def __init__(
        self,
        video_id: str,
        language: Union[str, Sequence[str]] = "en",
    ):
        """Initialize with YouTube video ID."""
        _video_id = _parse_video_id(video_id)
        self.video_id = _video_id if _video_id is not None else video_id
        self._metadata = {"source": video_id}
        self.language = language
        if isinstance(language, str):
            self.language = [language]
        else:
            self.language = language

    def _get_video_title(self) -> Optional[str]:
        """Get the video title using YouTube API or page scraping."""
        try:
            import requests
            import json

            # First try using YouTube Data API v3 if available
            try:
                from open_webui.config import YOUTUBE_API_KEY
                if YOUTUBE_API_KEY:
                    url = f"https://www.googleapis.com/youtube/v3/videos?id={self.video_id}&key={YOUTUBE_API_KEY}&part=snippet"
                    response = requests.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        if data.get("items"):
                            return data["items"][0]["snippet"]["title"]
            except ImportError:
                pass

            # Fallback to scraping the title from YouTube page
            url = f"https://www.youtube.com/watch?v={self.video_id}"
            response = requests.get(url)
            if response.status_code == 200:
                import re
                title_match = re.search(r'<title>(.+?)</title>', response.text)
                if title_match:
                    title = title_match.group(1)
                    # Remove " - YouTube" from the end if present
                    if title.endswith(" - YouTube"):
                        title = title[:-10]
                    return title
            return None
        except Exception as e:
            print(f"Error getting video title: {e}")
            return None

    def load(self) -> List[Document]:
        """Load YouTube transcripts into `Document` objects."""
        try:
            from youtube_transcript_api import (
                NoTranscriptFound,
                TranscriptsDisabled,
                YouTubeTranscriptApi,
            )
        except ImportError:
            raise ImportError(
                'Could not import "youtube_transcript_api" Python package. '
                "Please install it with `pip install youtube-transcript-api`."
            )

        try:
            print(f"[YoutubeLoader] Processing video URL: {self.video_id}")  # Debug log
            transcript_list = YouTubeTranscriptApi.list_transcripts(self.video_id)
        except Exception as e:
            print(e)
            return []

        try:
            transcript = transcript_list.find_transcript(self.language)
        except NoTranscriptFound:
            transcript = transcript_list.find_transcript(["en"])

        transcript_pieces: List[Dict[str, Any]] = transcript.fetch()

        transcript = " ".join(
            map(
                lambda transcript_piece: transcript_piece["text"].strip(" "),
                transcript_pieces,
            )
        )

        # Get video title and add it to metadata
        title = self._get_video_title()
        if title:
            self._metadata["title"] = title
            
        # Add the original video URL to metadata
        self._metadata["source_url"] = f"https://www.youtube.com/watch?v={self.video_id}"
        print(f"[YoutubeLoader] Document metadata: {self._metadata}")  # Debug log

        return [Document(page_content=transcript, metadata=self._metadata)]
