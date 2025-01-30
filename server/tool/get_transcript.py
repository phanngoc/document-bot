from langchain_core.tools import tool
from youtube_transcript_api import YouTubeTranscriptApi
from typing import List, Optional

@tool
def get_transcript(video_id: str, languages: Optional[List[str]] = None):
    """Get the transcript of a YouTube video."""
    transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['vi'])
    return transcript 