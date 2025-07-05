import os
import time
import random
import logging
import re
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

class YouTubeBot:
    def __init__(self):
        """Initialize the YouTube bot"""
        self.youtube = get_authenticated_service()
        self.posted_videos = self._load_posted_videos()
        self.comments = self._load_comments()
        self.channel_cache = {}  # Cache to store channel ID lookups
    
    def _load_posted_videos(self):
        """Load list of videos that have already been commented on"""
        if not os.path.exists(POSTED_VIDEOS_FILE):
            with open(POSTED_VIDEOS_FILE, 'w') as f:
                pass
            return set()
        
        with open(POSTED_VIDEOS_FILE, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    
    def _load_comments(self):
        """Load comments from file"""
        if not os.path.exists(COMMENTS_FILE):
            with open(COMMENTS_FILE, 'w') as f:
                f.write("Great video!\nVery informative content!\nThanks for sharing!")
            
        with open(COMMENTS_FILE, 'r') as f:
            return [line.strip() for line in f if line.strip()]
    
    def _save_posted_video(self, video_id):
        """Save video ID to posted videos file"""
        with open(POSTED_VIDEOS_FILE, 'a') as f:
            f.write(f"{video_id}\n")
        self.posted_videos.add(video_id)
    
    def _get_channel_id(self, channel_identifier):
        """
        Convert a channel handle (@username) or custom URL (c/ChannelName) to a channel ID
        If a channel ID is provided, it will be returned as is
        """
        # If it's already a channel ID (starts with UC), return it
        if channel_identifier.startswith('UC'):
            return channel_identifier
        
        # Check if we have this in our cache
        if channel_identifier in self.channel_cache:
            return self.channel_cache[channel_identifier]
        
        try:
            # Handle @username format
            if channel_identifier.startswith('@'):
                username = channel_identifier[1:]  # Remove the @ symbol
                response = self.youtube.search().list(
                    part="snippet",
                    q=f"@{username}",
                    type="channel",
                    maxResults=1
                ).execute()
                
                if response.get('items'):
                    channel_id = response['items'][0]['snippet']['channelId']
                    logging.info(f"Resolved {channel_identifier} to channel ID: {channel_id}")
                    self.channel_cache[channel_identifier] = channel_id
                    return channel_id
            
            # Handle c/ChannelName format
            elif channel_identifier.startswith('c/'):
                channel_name = channel_identifier[2:]  # Remove the c/ prefix
                response = self.youtube.search().list(
                    part="snippet",
                    q=channel_name,
                    type="channel",
                    maxResults=1
                ).execute()
                
                if response.get('items'):
                    channel_id = response['items'][0]['snippet']['channelId']
                    logging.info(f"Resolved {channel_identifier} to channel ID: {channel_id}")
                    self.channel_cache[channel_identifier] = channel_id
                    return channel_id
            
            logging.error(f"Could not resolve {channel_identifier} to a channel ID")
            return None
            
        except HttpError as e:
            logging.error(f"Error resolving channel identifier {channel_identifier}: {str(e)}")
            return None
    
    def get_recent_videos(self, channel_identifier):
        """Get recent videos from a channel"""
        channel_id = self._get_channel_id(channel_identifier)
        
        if not channel_id:
            logging.error(f"Skipping channel {channel_identifier} - could not resolve channel ID")
            return []
        
        try:
            # Increased maxResults to 20 to ensure we have enough videos to find 3 eligible ones
            response = self.youtube.search().list(
                part="snippet",
                channelId=channel_id,
                maxResults=20,
                order="date",
                type="video"
            ).execute()
            
            return [
                {
                    'id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'publishTime': item['snippet']['publishedAt']
                }
                for item in response.get('items', [])
            ]
        except HttpError as e:
            logging.error(f"Error fetching videos for channel {channel_identifier} (ID: {channel_id}): {str(e)}")
            return []
    
    def post_comment(self, video_id):
        """Post a comment on a video with exponential backoff retry"""
        if not self.comments:
            logging.error("No comments available to post")
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
                
                if retry_count < MAX_RETRIES:
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                
        logging.error(f"Failed to post comment on video {video_id} after {MAX_RETRIES} attempts")
        return False
    
    def check_and_comment_videos(self):
        """Check for new videos and post comments if they meet criteria"""
        for channel_identifier in CHANNEL_IDS:
            if not channel_identifier or channel_identifier.startswith('#'):
                continue
                
            channel_identifier = channel_identifier.strip()
            logging.info(f"Checking channel: {channel_identifier}")
            videos = self.get_recent_videos(channel_identifier)
            
            # Filter videos that are at least 3 hours old and not already commented on
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
                    logging.info(f"Video {video_id} not yet eligible for commenting. {hours_left:.2f} hours left.")
            
            # Limit to the 3 most recent eligible videos
            for video in eligible_videos[:3]:
                video_id = video['id']
                logging.info(f"Posting comment on video {video_id}: {video['title']}")
                self.post_comment(video_id)
                # Add 10-second delay between comments
                logging.info("Waiting 10 seconds before next comment...")
                time.sleep(10)
    
    def run(self):
        """Run the bot once"""
        try:
            self.check_and_comment_videos()
        except Exception as e:
            logging.error(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    bot = YouTubeBot()
    bot.run() 
