import os
import pickle
import base64
import logging
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from config import CLIENT_SECRETS_FILE, SCOPES

def get_token_expiry(credentials):
    """Get the expiry datetime of the token"""
    if not credentials or not hasattr(credentials, 'expiry'):
        return None
    return credentials.expiry

def is_token_expiring_soon(credentials, days=4):
    """Check if token will expire within specified days"""
    expiry = get_token_expiry(credentials)
    if not expiry:
        return True  # If no expiry found, assume it needs refresh
    
    now = datetime.utcnow()
    expiry_threshold = now + timedelta(days=days)
    
    return expiry <= expiry_threshold

def load_credentials():
    """Load credentials from token.pickle file"""
    if not os.path.exists('token.pickle'):
        return None
        
    try:
        with open('token.pickle', 'rb') as token_file:
            credentials = pickle.load(token_file)
            return credentials
    except Exception as e:
        logging.error(f"Error loading credentials: {str(e)}")
        return None

def save_credentials(credentials):
    """Save credentials to token.pickle file and update token_base64.txt"""
    try:
        # Save to token.pickle
        with open('token.pickle', 'wb') as token_file:
            pickle.dump(credentials, token_file)
            
        # Update token_base64.txt
        with open('token.pickle', 'rb') as f:
            token_data = f.read()
        
        token_base64 = base64.b64encode(token_data).decode('utf-8')
        
        with open('token_base64.txt', 'w') as f:
            f.write(token_base64)
            
        logging.info(f"Token refreshed and saved. New expiry: {credentials.expiry}")
        return True
    except Exception as e:
        logging.error(f"Error saving credentials: {str(e)}")
        return False

def refresh_token_if_needed(days_threshold=4, force_refresh=False):
    """
    Check if token needs refreshing and refresh it if needed
    Args:
        days_threshold (int): Number of days before expiry to trigger refresh
        force_refresh (bool): If True, force a refresh regardless of expiry
    Returns:
        bool: True if token was refreshed or is still valid, False if refresh failed
    """
    credentials = load_credentials()
    
    if not credentials:
        logging.error("No credentials found to refresh")
        return False
        
    # Check if we need to refresh
    needs_refresh = force_refresh or is_token_expiring_soon(credentials, days_threshold)
    
    if not needs_refresh:
        logging.info(f"Token still valid until {credentials.expiry}. No refresh needed.")
        return True
        
    logging.info(f"Token expiring soon ({credentials.expiry}). Attempting to refresh...")
    
    try:
        # Try to refresh using the refresh token
        if credentials.refresh_token:
            credentials.refresh(Request())
            logging.info(f"Token refreshed successfully. New expiry: {credentials.expiry}")
            return save_credentials(credentials)
        else:
            logging.warning("No refresh token available. Need to re-authenticate.")
            # Try to get new credentials via OAuth flow
            try:
                flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
                new_credentials = flow.run_local_server(port=8080)
                logging.info("Successfully re-authenticated with OAuth flow")
                return save_credentials(new_credentials)
            except Exception as oauth_error:
                logging.error(f"OAuth re-authentication failed: {str(oauth_error)}")
                return False
    except Exception as e:
        logging.error(f"Error refreshing token: {str(e)}")
        return False

def force_new_token():
    """
    Force creation of a new token through OAuth flow
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        logging.info("Forcing creation of new token via OAuth flow")
        flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
        new_credentials = flow.run_local_server(port=8080)
        return save_credentials(new_credentials)
    except Exception as e:
        logging.error(f"Error creating new token: {str(e)}")
        return False 