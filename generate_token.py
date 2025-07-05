#!/usr/bin/env python3
"""
Script to generate token.pickle file for YouTube API authentication.
Run this script locally to authenticate with YouTube API before deploying to GitHub.
"""

import os
import base64
import sys
from youtube_auth import get_authenticated_service

def main():
    print("Authenticating with YouTube API...")
    print("A browser window will open. Please sign in and grant permissions.")
    
    # This will create the token.pickle file
    youtube = get_authenticated_service()
    
    print("\nAuthentication successful!")
    print("token.pickle file has been created.")
    
    # Encode token.pickle to base64 for GitHub Actions
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as f:
            token_data = f.read()
        
        token_base64 = base64.b64encode(token_data).decode('utf-8')
        
        with open('token_base64.txt', 'w') as f:
            f.write(token_base64)
        
        print("\ntoken_base64.txt has been created.")
        print("Add this as a secret in your GitHub repository with the name YOUTUBE_TOKEN_PICKLE")
    else:
        print("Error: token.pickle was not created.")
        sys.exit(1)

if __name__ == "__main__":
    main() 