#!/usr/bin/env python3
"""
Script to manually trigger a token refresh.
"""

import logging
import argparse
from token_manager import refresh_token_if_needed, force_new_token

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    parser = argparse.ArgumentParser(description='YouTube API Token Refresh Tool')
    parser.add_argument(
        '--force-new',
        action='store_true',
        help='Force creation of a completely new token via OAuth flow'
    )
    args = parser.parse_args()
    
    if args.force_new:
        logging.info("Forcing creation of a completely new token...")
        if force_new_token():
            logging.info("New token created successfully!")
        else:
            logging.error("Failed to create new token!")
    else:
        logging.info("Attempting to refresh the YouTube API token...")
        # Force refresh regardless of expiry date
        if refresh_token_if_needed(days_threshold=4, force_refresh=True):
            logging.info("Token refresh completed successfully!")
        else:
            logging.error("Token refresh failed!")

if __name__ == "__main__":
    main() 