#!/usr/bin/env python3
"""
Script to prepare the token for GitHub Actions.
"""

import os
import base64
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    if not os.path.exists('token.pickle'):
        logging.error("No token.pickle file found! Run generate_token.py first.")
        return
    
    try:
        # Read the token file
        with open('token.pickle', 'rb') as f:
            token_data = f.read()
        
        # Encode to base64
        token_base64 = base64.b64encode(token_data).decode('utf-8')
        
        # Save to token_base64.txt
        with open('token_base64.txt', 'w') as f:
            f.write(token_base64)
        
        logging.info("Token encoded and saved to token_base64.txt")
        
        # Print instructions
        print("\n" + "="*80)
        print("GITHUB ACTIONS TOKEN UPDATE INSTRUCTIONS")
        print("="*80)
        print("\n1. The token has been encoded and saved to token_base64.txt")
        print("2. To update your GitHub repository:")
        print("   a. Go to your GitHub repository")
        print("   b. Navigate to Settings > Secrets and variables > Actions")
        print("   c. Find the secret named 'YOUTUBE_TOKEN_PICKLE'")
        print("   d. Click 'Update' and paste the contents of token_base64.txt")
        print("\nAlternatively, you can commit and push the token_base64.txt file")
        print("and let the GitHub Actions workflow use it automatically.")
        print("\nThe token will now be automatically refreshed every 3 days by the")
        print("token-refresh.yml workflow, and before each bot run.")
        print("="*80)
        
    except Exception as e:
        logging.error(f"Error preparing token for GitHub: {str(e)}")

if __name__ == "__main__":
    main() 