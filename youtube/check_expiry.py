#!/usr/bin/env python3
"""
Script to check the expiration date of the current YouTube API token.
"""

import os
import pickle
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_token_expiry():
    if not os.path.exists('token.pickle'):
        logging.error("No token.pickle file found!")
        return
    
    try:
        with open('token.pickle', 'rb') as token_file:
            credentials = pickle.load(token_file)
            
        if not hasattr(credentials, 'expiry'):
            logging.error("Token does not have expiry information!")
            return
        
        expiry = credentials.expiry
        now = datetime.utcnow()
        time_left = expiry - now
        
        logging.info(f"Token expiry date: {expiry}")
        logging.info(f"Current UTC time: {now}")
        logging.info(f"Time left: {time_left}")
        
        # Check if token will expire within 4 days
        expiry_threshold = now + timedelta(days=4)
        if expiry <= expiry_threshold:
            logging.warning(f"Token will expire within 4 days! Refresh recommended.")
        else:
            logging.info(f"Token is still valid for more than 4 days.")
            
        # Show refresh token availability
        if hasattr(credentials, 'refresh_token') and credentials.refresh_token:
            logging.info("Refresh token is available - token can be refreshed automatically.")
        else:
            logging.warning("No refresh token available - manual reauthorization will be needed.")
            
    except Exception as e:
        logging.error(f"Error checking token: {str(e)}")

if __name__ == "__main__":
    check_token_expiry() 