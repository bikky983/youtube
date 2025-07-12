# YouTube Auto-Comment Bot

A Python bot that monitors YouTube channels for new videos and automatically posts comments after a 3-hour delay from the upload time.

## Features

- Monitors specified YouTube channels for new videos
- Posts auto-comments with a 3-hour delay from upload time
- Avoids duplicate comments using a simple text file tracking system
- Rotates through a list of custom comments
- Handles errors with retry mechanism and exponential backoff
- Can run locally or via GitHub Actions
- **Supports channel handles (@username) and custom URLs (c/ChannelName)** - no need to find channel IDs!

## Setup

### Prerequisites

- Python 3.7+
- A Google account with YouTube API access
- OAuth 2.0 client credentials (already created as client_secret.json)

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/youtube-auto-comment-bot.git
   cd youtube-auto-comment-bot
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Configure the bot:
   - `client_secret.json` - Already in place
   - `channel_ids.txt` - Edit to include the YouTube channels you want to monitor
   - `comments.txt` - Edit to include the comments you want to post

### Configuration

1. Edit `channel_ids.txt` with the YouTube channels you want to monitor (one per line):
   ```
   # You can use any of these formats:
   @username
   c/ChannelName
   UC-channel-id
   ```

   For example:
   ```
   @MKBHD
   c/TechLinked
   UCX6OQ3DkcsbYNE6H8uQQuVA
   ```

2. Edit `comments.txt` with your preferred comments (one per line):
   ```
   Great video! Really enjoyed it.
   This content is so helpful, thank you for sharing!
   Amazing work as always!
   ```

## Usage

### First-Time Authentication

Before running on GitHub Actions, you must authenticate locally:

1. Run the authentication script:
   ```
   python generate_token.py
   ```

2. A browser window will open - sign in with your Google account and grant permissions

3. After authentication, two files will be created:
   - `token.pickle` - Authentication token
   - `token_base64.txt` - Base64-encoded token for GitHub

4. Add the contents of `token_base64.txt` as a GitHub secret named `YOUTUBE_TOKEN_PICKLE`

### Running Locally

Run the bot once:
```
python main.py --run-once
```

Run the bot continuously with a custom check interval (in seconds):
```
python main.py --interval 1800
```

### GitHub Actions Setup

Add these secrets to your GitHub repository:

1. `YOUTUBE_CLIENT_SECRET`: Contents of your client_secret.json file
2. `YOUTUBE_CHANNEL_IDS`: List of channel handles/names (one per line or comma-separated)
   ```
   @MKBHD,c/TechLinked,UC-channel-id
   ```
3. `YOUTUBE_COMMENTS`: List of comments (one per line)
4. `YOUTUBE_TOKEN_PICKLE`: Contents of token_base64.txt
5. `GH_PA_TOKEN`: GitHub Personal Access Token with repo scope

The bot will run automatically according to the schedule in the GitHub workflow file.

## Finding YouTube Channels

You can use any of these formats to specify YouTube channels:

1. **Channel Handle** (easiest): 
   - Look at the channel URL: `https://www.youtube.com/@username`
   - Use `@username` in your channel_ids.txt file

2. **Custom URL**:
   - Look at the channel URL: `https://www.youtube.com/c/ChannelName`
   - Use `c/ChannelName` in your channel_ids.txt file

3. **Channel ID** (if you prefer):
   - Go to a YouTube channel page
   - View the page source (right-click > "View Page Source")
   - Search for "channelId"
   - The ID starts with "UC" followed by alphanumeric characters

## License

This project is licensed under the MIT License - see the LICENSE file for details. 