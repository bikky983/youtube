#!/usr/bin/env python3
"""
Script to validate YouTube channel IDs and handles in your channel_ids.txt file.
This helps identify any problematic channels that might not be resolving correctly.
"""

import os
import logging
import argparse
from googleapiclient.errors import HttpError
from youtube_auth import get_authenticated_service
from config import CHANNEL_IDS_FILE

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def validate_channel(youtube, channel_identifier):
    """
    Validate a channel identifier and return detailed information
    Returns: (success, channel_id, channel_title, subscriber_count)
    """
    try:
        # First try direct channel lookup if it looks like a channel ID
        if channel_identifier.startswith('UC') and len(channel_identifier) == 24:
            response = youtube.channels().list(
                part="snippet,statistics",
                id=channel_identifier
            ).execute()
            
            items = response.get('items', [])
            if items:
                channel = items[0]
                return (
                    True,
                    channel['id'],
                    channel['snippet']['title'],
                    channel['statistics'].get('subscriberCount', 'hidden')
                )
        
        # For handles and usernames, use search
        search_query = channel_identifier
        response = youtube.search().list(
            part="snippet",
            q=search_query,
            type="channel",
            maxResults=1
        ).execute()
        
        items = response.get('items', [])
        if items:
            channel_id = items[0]['snippet']['channelId']
            title = items[0]['snippet']['title']
            
            # Get subscriber count
            channel_response = youtube.channels().list(
                part="statistics",
                id=channel_id
            ).execute()
            
            channel_items = channel_response.get('items', [])
            subscriber_count = 'unknown'
            if channel_items:
                subscriber_count = channel_items[0]['statistics'].get('subscriberCount', 'hidden')
            
            return (True, channel_id, title, subscriber_count)
        
        return (False, None, None, None)
        
    except HttpError as e:
        logging.error(f"API error for {channel_identifier}: {str(e)}")
        return (False, None, None, None)
    except Exception as e:
        logging.error(f"Unexpected error for {channel_identifier}: {str(e)}")
        return (False, None, None, None)

def load_channel_ids():
    """Load channel IDs from file"""
    if not os.path.exists(CHANNEL_IDS_FILE):
        logging.error(f"Channel IDs file not found: {CHANNEL_IDS_FILE}")
        return []
    
    try:
        with open(CHANNEL_IDS_FILE, 'r', encoding='utf-8') as f:
            return [line.strip() for line in f if line.strip() and not line.startswith('#')]
    except Exception as e:
        logging.error(f"Error loading channel IDs: {str(e)}")
        return []

def main():
    parser = argparse.ArgumentParser(description='YouTube Channel Validator')
    parser.add_argument('--fix', action='store_true', help='Create a fixed channel_ids.txt with correct IDs')
    args = parser.parse_args()
    
    logging.info("Validating YouTube channels...")
    
    # Get authenticated YouTube service
    youtube = get_authenticated_service()
    
    # Load channel IDs
    channel_identifiers = load_channel_ids()
    if not channel_identifiers:
        logging.error("No channel identifiers found to validate")
        return
    
    logging.info(f"Found {len(channel_identifiers)} channel identifiers to validate")
    
    # Results for fixed file
    fixed_channels = []
    
    # Validate each channel
    print("\n{:<30} {:<24} {:<40} {:<15}".format("Channel Identifier", "Channel ID", "Channel Title", "Subscribers"))
    print("-" * 110)
    
    for identifier in channel_identifiers:
        success, channel_id, title, subscribers = validate_channel(youtube, identifier)
        
        if success:
            print("{:<30} {:<24} {:<40} {:<15}".format(
                identifier, 
                channel_id, 
                title[:38] + '..' if title and len(title) > 40 else title or 'N/A',
                subscribers
            ))
            
            # Add to fixed list
            if args.fix:
                fixed_channels.append(channel_id)  # Use actual channel ID
        else:
            print("{:<30} {:<24} {:<40} {:<15}".format(
                identifier, "NOT FOUND", "N/A", "N/A"
            ))
    
    # Create fixed file if requested
    if args.fix and fixed_channels:
        fixed_file = "fixed_" + CHANNEL_IDS_FILE
        with open(fixed_file, 'w', encoding='utf-8') as f:
            for channel in fixed_channels:
                f.write(f"{channel}\n")
        logging.info(f"Created fixed channel IDs file: {fixed_file}")

if __name__ == "__main__":
    main() 