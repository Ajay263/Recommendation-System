import pickle
import streamlit as st
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import base64
from PIL import Image, ImageOps
import requests
from io import BytesIO
import pandas as pd
import random

st.set_page_config(
    page_title="Spotify Music Recommender",
    page_icon="🎵",
    layout="wide",
)

def add_spotify_styling():
    st.markdown("""
    <style>
    /* Main background and text colors */
    .stApp {
        background-color: #121212;
        color: #FFFFFF;
    }
    
    /* Header styles */
    .main-header {
        font-family: 'Gotham', 'Montserrat', sans-serif;
        font-size: 32px;
        font-weight: 700;
        color: white;
        margin-bottom: 0px;
        padding-top: 20px;
    }
    
    .sub-header {
        font-family: 'Gotham', 'Montserrat', sans-serif;
        font-size: 18px;
        font-weight: 400;
        color: #b3b3b3;
        margin-top: 0px;
        margin-bottom: 25px;
    }
    
    /* Custom song card styling */
    .song-card {
        background-color: #181818;
        border-radius: 8px;
        padding: 16px;
        transition: background-color 0.3s ease;
    }
    
    .song-card:hover {
        background-color: #282828;
    }
    
    .song-title {
        font-family: 'Gotham', 'Montserrat', sans-serif;
        font-size: 16px;
        font-weight: 700;
        color: white;
        margin-top: 10px;
        margin-bottom: 5px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    .song-artist {
        font-family: 'Gotham', 'Montserrat', sans-serif;
        font-size: 14px;
        font-weight: 400;
        color: #b3b3b3;
        margin-top: 0px;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
    
    /* Custom selectbox */
    div[data-baseweb="select"] {
        background-color: #333333 !important;
        border-radius: 4px !important;
        border: none !important;
    }
    
    div[data-baseweb="select"] > div {
        background-color: #333333 !important;
        color: white !important;
        border: none !important;
        font-family: 'Gotham', 'Montserrat', sans-serif !important;
    }
    
    /* Custom button */
    .stButton > button {
        background-color: #1DB954 !important;
        color: white !important;
        font-family: 'Gotham', 'Montserrat', sans-serif !important;
        font-weight: 700 !important;
        padding: 8px 32px !important;
        border: none !important;
        border-radius: 50px !important;
        cursor: pointer !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
    }
    
    .stButton > button:hover {
        background-color: #1ed760 !important;
        transform: scale(1.04) !important;
    }
    
    /* Container styling */
    .main-container {
        background-color: #181818;
        border-radius: 10px;
        padding: 20px;
        margin-bottom: 20px; 
    }
    
    /* Section titles */
    .section-title {
        font-family: 'Gotham', 'Montserrat', sans-serif;
        font-size: 24px;
        font-weight: 700;
        color: white;
        margin-bottom: 20px;
    }
    
    /* Footer */
    .footer {
        font-family: 'Gotham', 'Montserrat', sans-serif;
        font-size: 12px;
        color: #b3b3b3;
        text-align: center;
        margin-top: 50px;
        padding-bottom: 20px;
    }
    
    /* Hiding default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Album cover image styling */
    .album-cover {
        border-radius: 8px;
        width: 100%;
        aspect-ratio: 1/1;
        object-fit: cover;
    }
    
    /* Now playing section */
    .now-playing {
        background-color: #282828;
        border-radius: 8px;
        padding: 16px;
        display: flex;
        margin-bottom: 20px;
    }
    
    /* Progress bar */
    .stProgress > div > div {
        background-color: #1DB954 !important;
    }
    
    /* Navigation sidebar */
    .sidebar .sidebar-content {
        background-color: #000000;
    }
    </style>
    """, unsafe_allow_html=True)

CLIENT_ID = "043f4e87912443e481d8ffc0ca636933"
CLIENT_SECRET = "02081bca59eb43b395fbde990a804f29"

client_credentials_manager = SpotifyClientCredentials(client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)


def get_song_details(song_name, artist_name):
    '''Get album cover and additional track info'''
    search_query = f"track:{song_name} artist:{artist_name}"
    results = sp.search(q=search_query, type="track")

    default_image = "https://i.postimg.cc/0QNxYz4V/social.png"
    
    if results and results["tracks"]["items"]:
        track = results["tracks"]["items"][0]
        album_cover_url = track["album"]["images"][0]["url"] if track["album"]["images"] else default_image
        artist = track["artists"][0]["name"]
        album = track["album"]["name"]
        preview_url = track["preview_url"]
        return {
            "image_url": album_cover_url,
            "artist": artist,
            "album": album,
            "preview_url": preview_url
        }
    else:
        return {
            "image_url": default_image,
            "artist": artist_name,
            "album": "Unknown Album",
            "preview_url": None
        }


def get_rounded_image(image_url):
    '''Creating a rounded image'''
    try:
        response = requests.get(image_url)
        img = Image.open(BytesIO(response.content))
        mask = Image.new('L', img.size, 0)
        width, height = img.size
        radius = min(width, height) // 10  
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        return buffered.getvalue()
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return None

def recommend(song, music_df, similarity_matrix):
    '''Recommendation inference engine'''
    try:
        index = music_df[music_df['song'] == song].index[0]
        distances = sorted(list(enumerate(similarity_matrix[index])), reverse=True, key=lambda x: x[1])
        
        recommended_songs = []
        
        for i in distances[1:11]:  
            song_name = music_df.iloc[i[0]].song
            artist_name = music_df.iloc[i[0]].artist
            
            song_details = get_song_details(song_name, artist_name)
            
            recommended_songs.append({
                "song": song_name,
                "artist": artist_name, 
                "image_url": song_details["image_url"],
                "album": song_details["album"],
                "preview_url": song_details["preview_url"]
            })
        
        return recommended_songs
    except Exception as e:
        st.error(f"Error generating recommendations: {e}")
        return []


def generate_listening_history(music_df, num_items=5):
    '''Generating some  mock up listening history'''
    indices = random.sample(range(len(music_df)), num_items)
    history = []
    
    for idx in indices:
        song_name = music_df.iloc[idx].song
        artist_name = music_df.iloc[idx].artist
        
        song_details = get_song_details(song_name, artist_name)
        
        history.append({
            "song": song_name,
            "artist": artist_name,
            "image_url": song_details["image_url"],
            "album": song_details["album"]
        })
    
    return history


def display_song_card(song_info, show_play_button=False):
    ''' Displaying  album cover with artist and title'''
    col1, col2 = st.columns([1, 4])
    
    with col1:
        st.image(song_info["image_url"], use_container_width=True)
       
    
    with col2:
        st.markdown(f"<div style='padding-left:10px;'><p style='font-size:16px; font-weight:bold; margin-bottom:5px;'>{song_info['song']}</p><p style='font-size:14px; color:#b3b3b3;'>{song_info['artist']}</p><p style='font-size:12px; color:#b3b3b3;'>{song_info['album']}</p></div>", unsafe_allow_html=True)
        
        if show_play_button and song_info["preview_url"]:
            st.audio(song_info["preview_url"], format="audio/mp3")


def main():
    add_spotify_styling()
    try:
        music = pickle.load(open('models/df.pkl', 'rb'))
        similarity = pickle.load(open('models/similarity.pkl', 'rb'))
    except Exception as e:
        st.error(f"Error loading data files: {e}")
        return
    left_col, main_col = st.columns([1, 3])
    
    with left_col:
        st.markdown("<h3 style='color: #1DB954; font-family: Gotham, Montserrat, sans-serif;'>Spotify</h3>", unsafe_allow_html=True)
        
        # Navigation menu
        st.markdown("""
        <div style='background-color:#121212; padding:10px; border-radius:5px; margin-bottom:20px;'>
            <p style='color:white; font-weight:bold;'>🏠 Home</p>
            <p style='color:#b3b3b3;'>🔍 Search</p>
            <p style='color:#b3b3b3;'>📚 Your Library</p>
            <p style='color:#b3b3b3;'>➕ Create Playlist</p>
            <p style='color:#b3b3b3;'>❤️ Liked Songs</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Recently played section
        st.markdown("<p style='color:white; font-weight:bold; margin-top:30px;'>Recently Played</p>", unsafe_allow_html=True)
        
        # Generating  pseudo listening history
        history = generate_listening_history(music, 3)
        
        for item in history:
            st.markdown(f"""
            <div style='display:flex; align-items:center; margin-bottom:10px; padding:5px; border-radius:5px; background-color:#181818;'>
                <img src='{item["image_url"]}' style='width:40px; height:40px; border-radius:5px;' />
                <div style='margin-left:10px;'>
                    <p style='margin:0; font-size:14px; color:white;'>{item["song"]}</p>
                    <p style='margin:0; font-size:12px; color:#b3b3b3;'>{item["artist"]}</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    with main_col:
        # Header
        st.markdown("<h1 class='main-header'>Music Recommender</h1>", unsafe_allow_html=True)
        st.markdown("<p class='sub-header'>Discover new songs based on your favorites</p>", unsafe_allow_html=True)
        
        # Container for the search
        st.markdown("<div class='main-container'>", unsafe_allow_html=True)
        st.markdown("<p class='section-title'>Find Recommendations</p>", unsafe_allow_html=True)
        
        # Song selection
        music_list = music['song'].values
        selected_song = st.selectbox(
            "Search for a song",
            music_list
        )
        
        # Details for the selected song
        if selected_song:
            artist_name = music[music['song'] == selected_song]['artist'].values[0]
            selected_song_details = get_song_details(selected_song, artist_name)
            
            # Currently selected song
            st.markdown("<p style='font-size:18px; font-weight:bold; margin-top:20px;'>Currently Selected:</p>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            
            with col2:
                st.image(selected_song_details["image_url"], use_container_width=True)
                st.markdown(f"<p class='song-title' style='text-align:center;'>{selected_song}</p>", unsafe_allow_html=True)
                st.markdown(f"<p class='song-artist' style='text-align:center;'>{selected_song_details['artist']}</p>", unsafe_allow_html=True)
                
                # Recommendation button
                show_recommendations = st.button('Get Recommendations')
        
        st.markdown("</div>", unsafe_allow_html=True)
        
        # Displaying  recommendations
        if 'show_recommendations' in locals() and show_recommendations:
            recommended_songs = recommend(selected_song, music, similarity)
            
            if recommended_songs:
                st.markdown("<div class='main-container'>", unsafe_allow_html=True)
                st.markdown("<p class='section-title'>Recommended Songs</p>", unsafe_allow_html=True)
                
                # 5-column layout for recommendations
                cols = st.columns(5)
                
                # Displaying 5 recommendations
                for i, song_info in enumerate(recommended_songs[:5]):
                    with cols[i]:
                        st.image(song_info["image_url"], use_container_width=True)
                        st.markdown(f"<p class='song-title'>{song_info['song']}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p class='song-artist'>{song_info['artist']}</p>", unsafe_allow_html=True)
                        
                        # If preview URL is available, show a play button
                        if song_info["preview_url"]:
                            st.audio(song_info["preview_url"], format="audio/mp3")
                
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Displaying  "More Like This" section
                st.markdown("<div class='main-container'>", unsafe_allow_html=True)
                st.markdown("<p class='section-title'>More Songs You Might Like</p>", unsafe_allow_html=True)
                
                # Creating  5-column layout for additional recommendations
                cols = st.columns(5)
                
                # Displaying  the next 5 recommendations
                for i, song_info in enumerate(recommended_songs[5:10]):
                    with cols[i]:
                        st.image(song_info["image_url"], use_container_width=True)
                        st.markdown(f"<p class='song-title'>{song_info['song']}</p>", unsafe_allow_html=True)
                        st.markdown(f"<p class='song-artist'>{song_info['artist']}</p>", unsafe_allow_html=True)
                        
                        if song_info["preview_url"]:
                            st.audio(song_info["preview_url"], format="audio/mp3")
                
                st.markdown("</div>", unsafe_allow_html=True)
        
        # "Now Playing" feature at the bottom
        st.markdown("<div style='position:fixed; bottom:0; left:0; right:0; background-color:#282828; padding:10px; display:flex; align-items:center;'>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 5])
        
        with col1:
            if 'show_recommendations' in locals() and show_recommendations and recommended_songs:
                now_playing = recommended_songs[0]
                st.image(now_playing["image_url"], width=60)
        
        with col2:
            if 'show_recommendations' in locals() and show_recommendations and recommended_songs:
                st.markdown(f"<p style='margin:0; color:white; font-weight:bold;'>{recommended_songs[0]['song']}</p>", unsafe_allow_html=True)
                st.markdown(f"<p style='margin:0; color:#b3b3b3;'>{recommended_songs[0]['artist']}</p>", unsafe_allow_html=True)
                
                # Mock  progress bar
                st.progress(0.3)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Footer
    st.markdown("<div class='footer'>© 2025 Spotify Music Recommender</div>", unsafe_allow_html=True)

if __name__ == "__main__":
    main()