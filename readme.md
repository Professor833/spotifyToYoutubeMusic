
# Spotify to YouTube Playlist Transfer

This Python script transfers your playlists from Spotify to YouTube, handling the entire process of playlist fetching, track searching, and adding tracks to a corresponding YouTube playlist. It is designed to work with the Spotify and YouTube APIs, allowing you to save progress and continue from where you left off in case of interruptions or quota limits.

## Features
- **Transfer Playlists**: Automatically transfer your Spotify playlists to YouTube, creating new playlists and adding tracks from Spotify to YouTube.
- **Progress Persistence**: Progress is saved to a JSON file so that if a failure occurs (e.g., API quota exceeded), the script can resume from where it left off.
- **OAuth Authentication**: Securely authenticate with both Spotify and YouTube using OAuth.

## Prerequisites
- Python 3.x
- Spotify and YouTube API credentials
- Config file (`config.ini`) with the necessary API keys and user IDs

## Setup

### Step 1: Clone the Repository
Clone this repository to your local machine.
```bash
git clone https://github.com/Professor833/spotifyToYoutubeMusic.git
cd spotifyToYoutubeMusic
```

### Step 2: Install Required Libraries
Install the required Python packages listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Step 3: Configure API Credentials
Create a `config.ini` file in the root directory and fill in your Spotify and YouTube credentials. Here's an example of what it should look like:

```ini
[SPOTIFY]
SPOTIFY_CLIENT_ID = your_spotify_client_id
SPOTIFY_CLIENT_SECRET = your_spotify_client_secret
SPOTIFY_REDIRECT_URI = your_spotify_redirect_uri
SPOTIFY_USER_ID = your_spotify_user_id

[YOUTUBE]
YOUTUBE_API_KEY = your_youtube_api_key
```

### Step 4: Setup OAuth for YouTube
For YouTube OAuth, place the OAuth client credentials JSON file (downloadable from the [Google Developer Console](https://console.developers.google.com/)) in the specified location in your script, and update the path in `CLIENT_SECRETS_FILE`.

### Step 5: Run the Script
Once you have set up the credentials and installed the dependencies, you can run the script:
```bash
python main.py
```

The script will:
1. Authenticate with Spotify.
2. Fetch all your Spotify playlists.
3. Authenticate with YouTube.
4. Create corresponding YouTube playlists and add songs from Spotify.

## Progress Handling
The script stores progress in a JSON file (`playlist_transfer_progress.json`). If it runs into an API quota limit or any other issue, it will save the current state and allow you to resume later without duplicating already transferred tracks or playlists.

### Resuming the Transfer
If the script is interrupted, simply rerun it and it will pick up from where it left off.

## Customization
You can customize which playlists to skip by adding the playlist names to the `skip_playlists` list in the script.

```python
skip_playlists = ['playlist_name_to_skip']
```

## Troubleshooting
- Ensure your `config.ini` is properly configured with correct API credentials.
- If the browser doesn't open automatically during Spotify authentication, you can manually open the URL printed in the console.

## License
This project is licensed under the MIT License.
