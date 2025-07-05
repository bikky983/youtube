import os
import pickle
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import CLIENT_SECRETS_FILE, API_SERVICE_NAME, API_VERSION, SCOPES

def get_authenticated_service():
    """
    Authenticate with YouTube API using OAuth 2.0
    Returns an authenticated YouTube API service instance
    """
    credentials = None

    # Check if token pickle file exists
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            credentials = pickle.load(token)

    # If credentials don't exist or are invalid, refresh or create new ones
    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
            credentials = flow.run_local_server(port=8080)
        
        # Save credentials for future use
        with open('token.pickle', 'wb') as token:
            pickle.dump(credentials, token)

    # Build YouTube API service
    return build(API_SERVICE_NAME, API_VERSION, credentials=credentials) 