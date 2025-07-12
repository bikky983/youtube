import os
import time
import random
import logging
from datetime import datetime, timezone, timedelta
from googleapiclient.errors import HttpError
from youtube_auth import get_authenticated_service
from config import (
    CHANNEL_IDS, POSTED_VIDEOS_FILE, COMMENTS_FILE, 
    ERROR_LOG_FILE, COMMENT_DELAY, MAX_RETRIES, INITIAL_RETRY_DELAY
)

# Configure logging
logging.basicConfig(
    filename=ERROR_LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# YouTube API costs (in units)
API_COSTS = {
    'search.list': 100,      # Channel resolution + video search
    'commentThreads.insert': 50
}

MAX_QUOTA = 9500  # Stop when reaching this limit

class YouTubeBot:
    def __init__(self):
        """Initialize the YouTube bot"""
        self.youtube = get_authenticated_service()
        self.posted_videos = self._load_posted_videos()
        self.comments = self._load_comments()
        self.quota_used = 0  # Track quota for current run
        self.channel_cache = {}  # Cache resolved channel IDs for current run only
    
    def _load_posted_videos(self):
        """Load list of videos that have already been commented on"""
        if not os.path.exists(POSTED_VIDEOS_FILE):
            return set()
        
        try:
            with open(POSTED_VIDEOS_FILE, 'r', encoding='utf-8') as f:
                return set(line.strip() for line in f if line.strip())
        except UnicodeDecodeError:
            with open(POSTED_VIDEOS_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                return set(line.strip() for line in f if line.strip())
    
    def _load_comments(self):
        """Load comments from file"""
        if not os.path.exists(COMMENTS_FILE):
            default_comments = [
                "Great video!",
                "Very informative content!",
                "Thanks for sharing!"
            ]
            with open(COMMENTS_FILE, 'w', encoding='utf-8') as f:
                f.write("\n".join(default_comments))
        
        try:
            with open(COMMENTS_FILE, 'r', encoding='utf-8') as f:
                return [line.strip() for line in f if line.strip()]
        except UnicodeDecodeError:
            # Fallback to read with errors ignored
            with open(COMMENTS_FILE, 'r', encoding='utf-8', errors='ignore') as f:
                return [line.strip() for line in f if line.strip()]
    
    def _save_posted_video(self, video_id):
        """Save video ID to posted videos file"""
        with open(POSTED_VIDEOS_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{video_id}\n")
        self.posted_videos.add(video_id)
    
    def _use_quota(self, cost):
        """Check if we can use quota without exceeding limit"""
        if self.quota_used + cost > MAX_QUOTA:
            logging.warning(f"Quota limit reached: {self.quota_used}/{MAX_QUOTA}")
            return False
        self.quota_used += cost
        logging.info(f"Quota used: {self.quota_used}/{MAX_QUOTA}")
        return True
    
    def get_channel_videos(self, channel_identifier):
        """
        Get channel ID and recent videos in a single API call
        Returns: (channel_id, videos) or (None, []) on failure
        """
        # Check if we already resolved this identifier
        if channel_identifier in self.channel_cache:
            channel_id = self.channel_cache[channel_identifier]
            logging.info(f"Using cached channel ID: {channel_identifier} → {channel_id}")
            return channel_id, []
        
        # Check quota before API call
        if not self._use_quota(API_COSTS['search.list']):
            return None, []
        
        try:
            # Determine search parameters based on identifier type
            if channel_identifier.startswith('UC') and len(channel_identifier) == 24:
                # Direct channel ID search
                request = self.youtube.search().list(
                    part="snippet",
                    channelId=channel_identifier,
                    maxResults=10,
                    order="date",
                    type="video"
                )
            else:
                # Handle @username or custom URL
                request = self.youtube.search().list(
                    part="snippet",
                    q=channel_identifier,
                    maxResults=10,
                    order="date",
                    type="video"
                )
            
            response = request.execute()
            items = response.get('items', [])
            
            if not items:
                logging.error(f"No videos found for: {channel_identifier}")
                return None, []
            
            # Get channel ID from first video
            channel_id = items[0]['snippet']['channelId']
            self.channel_cache[channel_identifier] = channel_id
            logging.info(f"Resolved {channel_identifier} to channel ID: {channel_id}")
            
            # Extract videos
            videos = [
                {
                    'id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'publishTime': item['snippet']['publishedAt']
                }
                for item in items
            ]
            
            return channel_id, videos
            
        except HttpError as e:
            logging.error(f"Error processing {channel_identifier}: {str(e)}")
            if e.resp.status == 403 and 'quotaExceeded' in str(e):
                self.quota_used = MAX_QUOTA  # Set to limit to stop further processing
            return None, []
    
    def post_comment(self, video_id):
        """Post a comment on a video with exponential backoff retry"""
        if not self.comments:
            logging.error("No comments available to post")
            return False
            
        # Check quota before proceeding
        if not self._use_quota(API_COSTS['commentThreads.insert']):
            return False
            
        comment_text = random.choice(self.comments)
        retry_count = 0
        retry_delay = INITIAL_RETRY_DELAY
        
        while retry_count < MAX_RETRIES:
            try:
                self.youtube.commentThreads().insert(
                    part="snippet",
                    body={
                        "snippet": {
                            "videoId": video_id,
                            "topLevelComment": {
                                "snippet": {
                                    "textOriginal": comment_text
                                }
                            }
                        }
                    }
                ).execute()
                
                logging.info(f"Successfully commented on video {video_id}")
                self._save_posted_video(video_id)
                return True
                
            except HttpError as e:
                retry_count += 1
                logging.error(f"Error posting comment to {video_id} (attempt {retry_count}): {str(e)}")
                
                # Handle quota errors
                if e.resp.status == 403 and 'quotaExceeded' in str(e):
                    self.quota_used = MAX_QUOTA
                    return False
                
                if retry_count < MAX_RETRIES:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                
        logging.error(f"Failed to post comment on video {video_id} after {MAX_RETRIES} attempts")
        return False
    
    def check_and_comment_videos(self):
        """Check for new videos and post comments if they meet criteria"""
        for channel_identifier in CHANNEL_IDS:
            # Check quota before processing each channel
            if self.quota_used >= MAX_QUOTA:
                logging.critical(f"Stopping - quota limit reached: {self.quota_used}/{MAX_QUOTA}")
                return
                
            if not channel_identifier or channel_identifier.startswith('#'):
                continue
                
            channel_identifier = channel_identifier.strip()
            logging.info(f"Processing channel: {channel_identifier}")
            
            # Get channel ID and videos in single API call
            channel_id, videos = self.get_channel_videos(channel_identifier)
            
            if not channel_id or not videos:
                continue
            
            # Filter videos that are at least 3 hours old and not commented
            eligible_videos = []
            for video in videos:
                video_id = video['id']
                
                # Skip if already commented
                if video_id in self.posted_videos:
                    continue
                
                # Check if video is at least 3 hours old
                publish_time = datetime.fromisoformat(video['publishTime'].replace('Z', '+00:00'))
                current_time = datetime.now(timezone.utc)
                time_difference = current_time - publish_time
                
                if time_difference.total_seconds() >= COMMENT_DELAY:
                    eligible_videos.append(video)
                else:
                    hours_left = (COMMENT_DELAY - time_difference.total_seconds()) / 3600
                    logging.info(f"Video {video_id} not yet eligible. {hours_left:.2f} hours left.")
            
            # Process eligible videos
            for video in eligible_videos[:3]:  # Limit to 3 most recent
                video_id = video['id']
                
                # Check quota before each comment
                if self.quota_used >= MAX_QUOTA:
                    logging.critical(f"Quota limit reached during commenting: {self.quota_used}/{MAX_QUOTA}")
                    return
                
                logging.info(f"Posting comment on video {video_id}: {video['title']}")
                self.post_comment(video_id)
                
                # Add delay between comments
                logging.info("Waiting 10 seconds before next comment...")
                time.sleep(10)
    
    def run(self):
        """Run the bot once"""
        try:
            self.check_and_comment_videos()
            logging.info(f"Run completed. Total quota used: {self.quota_used}/{MAX_QUOTA}")
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    bot = YouTubeBot()
    bot.run()
