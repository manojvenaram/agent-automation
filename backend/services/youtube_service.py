"""
Official YouTube Data API v3 Service.
Uses Google OAuth2 authorization.
Credentials and refresh tokens are securely stored in credentials/ (gitignored).
Default privacy status is strictly 'private' for testing safety.
"""

import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from backend.core.config import settings, CREDENTIALS_DIR
from backend.core.logging import logger

YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube.readonly"
]


class YouTubeService:
    def __init__(self):
        self.secrets_file = settings.youtube_client_secrets_file
        self.token_file = settings.youtube_token_file

    def is_authenticated(self) -> bool:
        """Check if valid authenticated YouTube credentials exist and can be refreshed."""
        if not self.token_file.exists():
            return False
        # get_authenticated_service handles token refresh automatically
        try:
            return self.get_authenticated_service() is not None
        except Exception:
            return False

    def get_authenticated_service(self):
        """Retrieve or refresh authenticated YouTube API client."""
        creds = None
        if self.token_file.exists():
            try:
                with open(self.token_file, "rb") as token:
                    creds = pickle.load(token)
            except Exception as e:
                logger.warning(f"Could not load token file: {e}")

        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                with open(self.token_file, "wb") as token:
                    pickle.dump(creds, token)
            except Exception as e:
                logger.warning(f"Token refresh failed: {e}")
                creds = None

        if not creds or not creds.valid:
            if not self.secrets_file.exists():
                raise FileNotFoundError(
                    f"YouTube OAuth credentials missing! Please download your client secrets JSON from "
                    f"Google Cloud Console and save it to: {self.secrets_file}"
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(self.secrets_file), YOUTUBE_SCOPES
            )
            creds = flow.run_local_server(port=0)
            with open(self.token_file, "wb") as token:
                pickle.dump(creds, token)

        return build("youtube", "v3", credentials=creds)

    def upload_short(
        self,
        video_path: str,
        title: str,
        description: str,
        tags: Optional[List[str]] = None,
        privacy_status: Optional[str] = None,
        category_id: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Uploads video to YouTube via official API with resumable chunked upload.
        Default privacy status is 'private'.
        """
        if not os.path.exists(video_path):
            raise FileNotFoundError(f"Video file to upload not found: {video_path}")

        status = privacy_status or settings.youtube_privacy_status
        category = category_id or settings.youtube_category_id

        # Ensure title contains #Shorts for YouTube algorithm detection
        final_title = title.strip()
        if "#Shorts" not in final_title and "#shorts" not in final_title:
            if len(final_title) <= 90:
                final_title += " #Shorts"

        youtube = self.get_authenticated_service()

        body = {
            "snippet": {
                "title": final_title[:100],
                "description": description,
                "tags": tags or ["Shorts", "Science", "Technology"],
                "categoryId": category,
            },
            "status": {
                "privacyStatus": status,
                "selfDeclaredMadeForKids": False,
            },
        }

        media = MediaFileUpload(
            video_path,
            chunksize=2 * 1024 * 1024,
            resumable=True,
            mimetype="video/mp4",
        )

        logger.info(f"Initiating YouTube upload for '{final_title}' (privacy: {status})...")
        request = youtube.videos().insert(
            part="snippet,status",
            body=body,
            media_body=media,
        )

        response = None
        while response is None:
            upload_status, response = request.next_chunk()
            if upload_status:
                logger.info(f"Uploaded {int(upload_status.progress() * 100)}%")

        video_id = response.get("id")
        published_url = f"https://youtube.com/shorts/{video_id}"
        logger.info(f"YouTube upload successful! Video URL: {published_url}")

        return {
            "video_id": video_id,
            "title": final_title,
            "privacy_status": status,
            "url": published_url,
        }

    def fetch_latest_comments(self, max_results: int = 50) -> List[Dict[str, str]]:
        """
        Fetches the latest comments from the authenticated user's channel.
        Returns a list of dicts: [{'text': str, 'author': str}]
        """
        if not self.is_authenticated():
            logger.warning("YouTube authentication required to fetch comments.")
            return []

        try:
            youtube = self.get_authenticated_service()
            
            # Use commentThreads API to get recent comments across all videos
            request = youtube.commentThreads().list(
                part="snippet",
                allThreadsRelatedToChannelId="mine",
                order="time",
                maxResults=max_results,
                textFormat="plainText"
            )
            
            response = request.execute()
            comments = []
            
            for item in response.get("items", []):
                snippet = item["snippet"]["topLevelComment"]["snippet"]
                text = snippet.get("textDisplay", "")
                author = snippet.get("authorDisplayName", "Viewer")
                if text:
                    comments.append({"text": text, "author": author})
                    
            logger.info(f"Fetched {len(comments)} recent comments from YouTube.")
            return comments
            
        except Exception as e:
            logger.error(f"Failed to fetch YouTube comments: {e}")
            return []


# Global singleton instance
youtube_service = YouTubeService()
