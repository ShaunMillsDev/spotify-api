import http.server
import socketserver
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

# Check if access token is in cache
if not auth_manager.get_cached_token():
    # Open the authorization URL in the user's web browser
    auth_url = auth_manager.get_authorize_url()
    webbrowser.open(auth_url)

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

with socketserver.TCPServer(("", 3000), MyHandler) as httpd:
    print("Listening for incoming requests...")
    httpd.handle_request()

# Create the Spotify object with authentication
sp = spotipy.Spotify(auth=access_token)

# Get the user's playlists
playlists = sp.current_user_playlists()['items']

# Ask the user to input a song name
song_name = input("\nEnter a song name: ")

playlist_count = 0

# Iterate over the user's playlists and check if the song exists in each playlist
for playlist in playlists:
    playlist_count += 1
    playlist_id = playlist['id']
    playlist_name = playlist['name']
    playlist_tracks = sp.playlist_tracks(playlist_id)['items']
    
    for track in playlist_tracks:
        track_name = track['track']['name']
        if track_name.lower() == song_name.lower():
            print(f"The song '{track_name}' is in the playlist '{playlist_name}' which is playlist number {playlist_count}")
    
print()
