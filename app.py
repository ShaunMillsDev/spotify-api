import http.server
import socketserver
import time
import webbrowser
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json

# Open and read the configuration file
with open('config.json', 'r') as f:
    config_data = f.read()

# Load the JSON data from the configuration file
config = json.loads(config_data)

# Retrieve the client ID and secret from the config dictionary
client_id = config['client_id']
client_secret = config['client_secret']
redirect_uri = config['redirect_uri']
scope = config['scope']

# Use the client ID and secret to create a SpotifyOAuth object
auth_manager = SpotifyOAuth(client_id=client_id,
                            client_secret=client_secret,
                            redirect_uri=redirect_uri,
                            scope=scope,
                            open_browser=False)

# Create a temporary HTTP server to receive the authorization token
class MyHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        global access_token

        if self.path.startswith('/callback'):
            # Retrieve the authorization code from the URL parameters
            code = self.path.split('code=')[1]

            # Exchange the authorization code for an access token
            token_info = auth_manager.get_access_token(code, as_dict=False)
            access_token = token_info

            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b'<html><body><h1>Authorization successful!</h1></body></html>')
        else:
            super().do_GET()

# Check if access token is in cache and is still valid
cached_token = auth_manager.get_cached_token()

# Check if the cached token exists and is not expired
if not cached_token or int(cached_token['expires_at']) < int(time.time()):
    # Open the authorization URL in the user's web browser
    auth_url = auth_manager.get_authorize_url()
    webbrowser.open(auth_url)

    with socketserver.TCPServer(("", 3000), MyHandler) as httpd:
        print("Listening for incoming requests...")
        httpd.handle_request()
else:
    access_token = cached_token['access_token']

# Create the Spotify object with authentication
sp = spotipy.Spotify(auth=access_token)

def get_all_playlists(spotify_instance):
    playlists = []
    limit = 50
    offset = 0
    while True:
        response = spotify_instance.current_user_playlists(limit=limit, offset=offset)
        playlists += response['items']
        if response['next']:
            offset += limit
        else:
            break
    return playlists

# Get the user's playlists
playlists = get_all_playlists(sp)

# Ask the user to input a song name
song_name = input("\nEnter a song name: ")

playlist_count = 0

matching_playlists = []

# Iterate over the user's playlists and check if the song exists in each playlist
for playlist in playlists:
    playlist_count += 1
    print(f"Playlist: #{playlist_count}: {playlist['name']}")
    playlist_id = playlist['id']
    playlist_name = playlist['name']
    playlist_tracks = sp.playlist_tracks(playlist_id)['items']
    
    for track in playlist_tracks:
        track_name = track['track']['name']
        if song_name.lower() in track_name.lower():
            matching_playlists.append([playlist_name, playlist_count])

for song in matching_playlists:
    print(f"Found in playlist: '{song[0]}' which is playlist #{song[1]} in your list")

print()
