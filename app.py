import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import streamlit as st
import random
from itertools import combinations

# Set up your Spotify API credentials
SPOTIPY_CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
SPOTIPY_CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
SPOTIPY_REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# Display album covers and song information
header_col1, _, header_col2, _ = st.columns((8, 2, 2, 2))

# Initialize Spotify API client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=SPOTIPY_CLIENT_ID,
                                               client_secret=SPOTIPY_CLIENT_SECRET,
                                               redirect_uri=SPOTIPY_REDIRECT_URI,
                                               scope="playlist-modify-private playlist-read-private"))

# Cache the song fetching process to avoid re-fetching on every rerun
@st.cache_data
def get_songs_from_playlist(playlist_id: str) -> list:
    try:
        playlist_count = sp.playlist(playlist_id)['tracks']['total']
        print(playlist_count)
        playlist = sp.playlist_items(playlist_id, limit=playlist_count)
        songs = []
        for item in playlist['items']:
            track = item['track']
            cover_url = track['album']['images'][1]['url']  # Medium size cover
            songs.append({
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'url': track['external_urls']['spotify'],
                'id': track['id'],
                'cover': cover_url,  # Add the cover URL
                'rating': 1000  # Initial Elo rating
            })
        return songs
    except Exception as e:
        print(e)
        return None

def extract_playlist_id(playlist_url: str) -> str:
    return playlist_url.strip().split('/')[-1].split('?')[0]

# Function to update Elo ratings
def update_elo(winner_rating: float, loser_rating: float, k: int = 32) -> tuple[float, float]:
    expected_winner = 1 / (1 + 10 ** ((loser_rating - winner_rating) / 400))
    expected_loser = 1 / (1 + 10 ** ((winner_rating - loser_rating) / 400))
    new_winner_rating = winner_rating + k * (1 - expected_winner)
    new_loser_rating = loser_rating + k * (0 - expected_loser)
    return new_winner_rating, new_loser_rating

def get_next_pair():
    # Find a new pair of songs that hasn't been used yet.
    available_pairs = [
        pair for pair in st.session_state['all_pairs']
        if (pair[0]['id'], pair[1]['id']) not in st.session_state['used_pairs']
    ]
    
    # If no more unused pairs, reshuffle the pairs
    if not available_pairs:
        st.session_state['used_pairs'] = set()  # Reset the used pairs
        available_pairs = st.session_state['all_pairs']
        random.shuffle(available_pairs)

    # Pick the first pair from available unused pairs
    next_pair = available_pairs[0]
    # Store the pair as a tuple of song IDs to make it hashable
    st.session_state['used_pairs'].add((next_pair[0]['id'], next_pair[1]['id']))
    return next_pair


if "playlist_id" not in st.session_state:
    st.session_state["playlist_id"] = None

# Display the current pair of songs or final results
with header_col1:
    st.title(':violet[SPOTIRANK]')

if st.session_state["playlist_id"] == None:
    playlist_url = st.text_input("Spotify Playlist Link")
    playlist_submission = st.button("Submit")
    number_of_comparisons = st.select_slider("How many times would you like to compare each song?", range(21)[5:], 10)

    songs = None
    if playlist_url is not None and playlist_submission:
        playlist_id = extract_playlist_id(playlist_url)
        songs = get_songs_from_playlist(playlist_id)

    if songs == None and playlist_submission:
        st.subheader(":red[Invalid URL]")
    elif playlist_submission:
        playlist_length = len(songs)
        st.session_state["playlist_id"] = playlist_id

        # Track the current comparison index (stored in session state)
        st.session_state['comparison_index'] = 0

        # Shuffle songs once and store in session state
        st.session_state['shuffled_songs'] = random.sample(songs, playlist_length)

        # Create all unique combinations of songs (only once)
        all_combinations = list(combinations(st.session_state['shuffled_songs'], 2))
        random.shuffle(all_combinations)  # Shuffle pairs initially
        st.session_state['all_pairs'] = all_combinations
        st.session_state['used_pairs'] = set()  # Set to track used pairs as tuples of song IDs
        st.session_state['target_comparisons'] = playlist_length * number_of_comparisons  # Target of 10x comparisons
        st.session_state['comparison_count'] = 0  # Track how many comparisons have been made

        st.rerun()
else: 
    # Check if we still have pairs to compare
    if st.session_state['comparison_count'] < st.session_state['target_comparisons'] and st.session_state['comparison_count'] >= 0:
        current_pair = get_next_pair()
        with header_col2:
            st.text("")
            st.text("")
            st.text("")
            st.caption(f":violet[{st.session_state['comparison_count']}/{st.session_state['target_comparisons']}]")
    else:
        current_pair = None


    if current_pair is None:
        # Sort songs by their Elo rating
        ranked_songs = sorted(st.session_state['shuffled_songs'], key=lambda song: song['rating'], reverse=True)

        st.write("## Final Ranked Songs:")
        for rank, song in enumerate(ranked_songs, 1):
            st.write(f"{rank}. {song['name']} - {song['artist']} - [Listen on Spotify]({song['url']}) - Elo: {song['rating']:.2f}")

        # Option to create a new playlist
        if st.button("Create New Ranked Playlist"):
            user_id = sp.current_user()['id']  # Get current user's Spotify ID

            # Create a new playlist
            new_playlist = sp.user_playlist_create(user=user_id, name="ONEHUNDRED", public=False, description="The creme")
            new_playlist_id = new_playlist['id']

            # Add songs to the new playlist in ranked order (best to worst)
            song_ids = [song['id'] for song in ranked_songs]  # List of song IDs in ranked order
            sp.playlist_add_items(playlist_id=new_playlist_id, items=song_ids)

            st.write(f"New playlist created: [View Playlist on Spotify](https://open.spotify.com/playlist/{new_playlist_id})")
    else:
        song_1, song_2 = current_pair
        col1, col2 = st.columns(2)
        with col1:
            st.header(f"**Option 1**")
            st.image(song_1['cover'], width=200)  # Display cover of song 1
            st.markdown(f"#### {song_1['name']}")
            st.caption(f"{song_1['artist']}")
            st.write(f"[Listen on Spotify]({song_1['url']})")
            if st.button(f"Vote Option 1"):
                song_1['rating'], song_2['rating'] = update_elo(song_1['rating'], song_2['rating'])
                st.session_state['comparison_count'] += 1
                st.rerun()  # Only refresh to move to the next pair

        with col2:
            st.header("**Option 2**")
            st.image(song_2['cover'], width=200)  # Display cover of song 2
            st.markdown(f"#### {song_2['name']}")
            st.caption(f"{song_2['artist']}")
            st.write(f"[Listen on Spotify]({song_2['url']})")
            if st.button(f"Vote Option 2"):
                song_2['rating'], song_1['rating'] = update_elo(song_2['rating'], song_1['rating'])
                st.session_state['comparison_count'] += 1
                st.rerun()  # Only refresh to move to the next pair