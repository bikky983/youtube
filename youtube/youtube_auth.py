import os
import pickle
import logging
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import CLIENT_SECRETS_FILE, API_SERVICE_NAME, API_VERSION, SCOPES

def get_authenticated_service(force_new_token=False):
    """
    Authenticate with YouTube API using OAuth 2.0
    Returns an authenticated YouTube API service instance
    
    Args:
        force_new_token (bool): If True, forces creation of a new token regardless of existing token
    """
    credentials = None

    # Check if token pickle file exists and we're not forcing a new token
    if not force_new_token and os.path.exists('token.pickle'):
        logging.info("Loading credentials from token.pickle")
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    # If credentials don't exist or are invalid, refresh or create new ones
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            logging.info("Refreshing expired credentials")
            credentials.refresh(Request())
            logging.info(f"Credentials refreshed. New expiry: {credentials.expiry}")
        else:
            logging.info("Creating new credentials via OAuth flow")
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=8080)
            logging.info(f"New credentials created. Expiry: {credentials.expiry}")
        
        # Save credentials for future use
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)
            logging.info("Credentials saved to token.pickle")

    # Build YouTube API service
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials) 