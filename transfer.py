import os
import json
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import webbrowser
import google_auth_oauthlib.flow
import googleapiclient.discovery
import googleapiclient.errors
import configparser


config = configparser.ConfigParser()
config.read('config.ini')

# Spotify credentials
SPOTIFY_CLIENT_ID = config['SPOTIFY']['SPOTIFY_CLIENT_ID']
SPOTIFY_CLIENT_SECRET = config['SPOTIFY']['SPOTIFY_CLIENT_SECRET']
SPOTIFY_REDIRECT_URI = config['SPOTIFY']['SPOTIFY_REDIRECT_URI']

# YouTube API credentials
YOUTUBE_API_KEY = config['YOUTUBE']['YOUTUBE_API_KEY']

skip_playlists = []
skip_playlists = [x.lower() for x in skip_playlists]

# File to store progress
PROGRESS_FILE = 'playlist_transfer_progress.json'
my_spotify_user_id = config['SPOTIFY']['SPOTIFY_USER_ID']


def load_progress():
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, 'r') as file:
            return json.load(file)
    return {"completed_playlists": [], "current_playlist": None, "tracks_done": []}


def save_progress(progress):
    with open(PROGRESS_FILE, 'w') as file:
        json.dump(progress, file, indent=4)


def authenticate_spotify():
    scope = "playlist-read-private"
    sp_oauth = SpotifyOAuth(client_id=SPOTIFY_CLIENT_ID,
                            client_secret=SPOTIFY_CLIENT_SECRET,
                            redirect_uri=SPOTIFY_REDIRECT_URI,
                            scope=scope)

    # Open the authorization URL manually if the web browser fails to launch
    auth_url = sp_oauth.get_authorize_url()
    print(f"Opening this URL in your browser to authorize the app: {auth_url}")
    webbrowser.open(auth_url)

    # Prompt the user to enter the URL they were redirected to after authorization
    redirect_response = input("Paste the full redirect URL here: ")

    # Get the access token using the authorization code from the redirect response
    token_info = sp_oauth.get_access_token(
        code=sp_oauth.parse_response_code(redirect_response))

    if token_info:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        return sp
    else:
        print("Could not retrieve token. Check your credentials and OAuth setup.")
        return None


def authenticate_youtube():
    # Disable OAuthlib's HTTPS verification when running locally.
    CLIENT_SECRETS_FILE = '/Users/lalit/lalitWorkspace/spotifyToYTMusic/oauth_client_secret.json'
    # Specify the scopes you need to access YouTube Data API
    SCOPES = ["https://www.googleapis.com/auth/youtube.force-ssl"]

    # *DO NOT* leave this option enabled in production.
    os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

    # Get credentials and create an API client
    flow = google_auth_oauthlib.flow.InstalledAppFlow.from_client_secrets_file(
        CLIENT_SECRETS_FILE, SCOPES)
    credentials = flow.run_local_server(port=8080)

    youtube = googleapiclient.discovery.build(
        "youtube", "v3", credentials=credentials)
    return youtube


def get_spotify_playlists(sp):
    playlists = []
    results = sp.current_user_playlists(limit=50)
    playlists.extend(results['items'])

    # Handle pagination (in case the user has more than 50 playlists)
    while results['next']:
        results = sp.next(results)
        playlists.extend(results['items'])

    return playlists


def get_spotify_playlist_tracks(sp, playlist_id):
    tracks = []
    results = sp.playlist_tracks(playlist_id, limit=100)
    tracks.extend(results['items'])

    # Handle pagination for tracks
    while results['next']:
        results = sp.next(results)
        tracks.extend(results['items'])

    return tracks


def search_youtube(youtube, query):
    request = youtube.search().list(
        part="snippet",
        q=query,
        maxResults=1,
        type="video"
    )
    response = request.execute()
    return response['items'][0]['id']['videoId'] if response['items'] else None


def add_song_to_youtube_playlist(youtube, video_id, playlist_id):
    request = youtube.playlistItems().insert(
        part="snippet",
        body={
            "snippet": {
                "playlistId": playlist_id,
                "resourceId": {
                    "kind": "youtube#video",
                    "videoId": video_id
                }
            }
        }
    )
    response = request.execute()
    return response


def create_youtube_playlist(youtube, title, description=""):
    request = youtube.playlists().insert(
        part="snippet,status",
        body={
            "snippet": {
                "title": title,
                "description": description
            },
            "status": {
                "privacyStatus": "private"
            }
        }
    )
    response = request.execute()
    return response['id']


def get_youtube_playlist_id(youtube, title):
    request = youtube.playlists().list(
        part="snippet",
        mine=True,
        maxResults=50
    )
    response = request.execute()
    for item in response['items']:
        if item['snippet']['title'] == title:
            return item['id']
    return None


def main():
    progress = load_progress()

    # Step 1: Authenticate with Spotify
    sp = authenticate_spotify()

    # Step 2: Get all the user's Spotify playlists
    playlists = get_spotify_playlists(sp)
    # save playlist to json file
    with open('playlists.json', 'w') as file:
        json.dump(playlists, file, indent=4)

    print('total my playlists before >> ', len(playlists))
    # remove all the playlists that do not have owner.id as as your owner ID (which are not created by you)
    playlists = [playlist for playlist in playlists if playlist['owner']
                 ['id'] == my_spotify_user_id]
    print('total my playlists >> ', len(playlists))

    # Step 3: Authenticate YouTube
    # youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
    youtube = authenticate_youtube()

    # Step 4: Loop through each playlist
   # Step 4: Loop through each playlist, skipping completed ones
    for playlist in playlists:
        if playlist['name'].lower() in skip_playlists or playlist['name'] in progress['completed_playlists']:
            print(f"------> skipping {playlist['name']}")
            continue

        print(f"Processing Spotify playlist: {playlist['name']}")

        # Step 5: Fetch all tracks in the current playlist
        tracks = get_spotify_playlist_tracks(sp, playlist['id'])

        # Step 6: Check if resuming from an incomplete playlist
        if progress['current_playlist'] == playlist['name']:
            tracks_done = progress['tracks_done']
        else:
            progress['current_playlist'] = playlist['name']
            progress['tracks_done'] = []
            tracks_done = []

        # # if resuming from an incomplete playlist don't create a new playlist on youtube
        # if progress['current_playlist'] == playlist['name']:
        #     youtube_playlist_id = get_youtube_playlist_id(
        #         youtube, playlist['name'])
        #     print(
        #         f"{'-' * 10} Resuming YouTube playlist: {playlist['name']} {'-' * 10}")
        # else:
        #     youtube_playlist_id = create_youtube_playlist(
        #         youtube, playlist['name'])
        #     print(
        #         f"{'-' * 10} Created YouTube playlist: {playlist['name']} {'-' * 10}")
        # Step 7: Create a corresponding YouTube playlist
        youtube_playlist_id = create_youtube_playlist(
            youtube, playlist['name'])
        print(
            f"{'-' * 10} Created YouTube playlist: {playlist['name']} {'-' * 10}")

        # Step 8: For each track, search for it on YouTube and add it to the playlist
        for item in tracks:
            track = item['track']
            if not track:
                print("Skipping track (no track data found).")
                continue
            track_name = track['name']
            artist_name = track['artists'][0]['name']

            # Skip tracks that are already added
            if track_name in tracks_done:
                continue

            query = f"{track_name} {artist_name}"
            print(f"Searching YouTube for {query}...")
            video_id = None
            try:
                video_id = search_youtube(youtube, query)
            except Exception as e:
                print(
                    f"An error occurred while searching YouTube for {query}.", 'error > ', e)
                continue

            if video_id:
                try:
                    add_song_to_youtube_playlist(
                        youtube, video_id, youtube_playlist_id)
                    print(
                        f"Added {track_name} by {artist_name} to {playlist['name']} playlist.")

                    # Update progress
                    progress['tracks_done'].append(track_name)
                    save_progress(progress)

                except Exception as e:
                    print(
                        f"An error occurred while adding {track_name} by {artist_name} to the YouTube playlist.", 'error > ', e)

                    # Handle quota exceeded
                    if 'quotaExceeded' in str(e):
                        print(
                            "YouTube API quota exceeded. Saving progress and exiting.")
                        save_progress(progress)
                        return
            else:
                print(
                    f"Could not find {track_name} by {artist_name} on YouTube.")

        # Playlist complete
        progress['completed_playlists'].append(playlist['name'])
        progress['current_playlist'] = None
        progress['tracks_done'] = []
        save_progress(progress)

    print("All playlists processed!")


if __name__ == "__main__":
    main()
