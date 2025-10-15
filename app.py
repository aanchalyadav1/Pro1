# app.py
import streamlit as st
from deepface import DeepFace
import cv2
import numpy as np
from spotipy.oauth2 import SpotifyOAuth
import spotipy
from dotenv import load_dotenv
import os
from auth import signup, login
from db import init_db
import sqlite3

# Initialize DB
init_db()

# Load environment variables
load_dotenv()

# Spotify authentication
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=os.getenv("fb79f67e486247c4b8a0308d1c482646"),
    client_secret=os.getenv("cce4a58dcb5e43b392861a8d20b89a1d"),
    redirect_uri=os.getenv("https://example.com/callback"),
    scope="user-library-read"
))

# --- UI ---
st.title("🎵 Mood-Based Music Recommender")

# Sidebar for Login / Signup / Forgot Password
choice = st.sidebar.selectbox("Choose Action", ["Login", "Signup", "Forgot Password"])
email = st.sidebar.text_input("Email")
password = st.sidebar.text_input("Password", type="password")

# SIGNUP
if choice == "Signup" and st.sidebar.button("Create Account"):
    if signup(email, password):
        st.success("Account created! Please login.")
    else:
        st.error("Email already exists.")

# LOGIN
if choice == "Login" and st.sidebar.button("Login"):
    if login(email, password):
        st.success("Logged in successfully!")
        st.session_state['user'] = email
    else:
        st.error("Invalid credentials.")

# FORGOT PASSWORD
if choice == "Forgot Password":
    from email_utils import send_reset_email
    import secrets
    email_fp = st.sidebar.text_input("Enter your email to reset password")
    if st.sidebar.button("Send Reset Link"):
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=?", (email_fp,))
        if c.fetchone():
            token = secrets.token_urlsafe(16)
            from db import save_reset_token
            save_reset_token(email_fp, token)
            send_reset_email(email_fp, token)
            st.success("Reset link sent to your email!")
        else:
            st.error("Email not found")
        conn.close()

# --- Emotion Detection & Spotify Recommendations ---
if 'user' in st.session_state:
    option = st.radio("Input method:", ["Upload Image", "Use Camera"])
    img = None

    # Upload Image
    if option == "Upload Image":
        uploaded_file = st.file_uploader("Upload your photo", type=["jpg","png","jpeg"])
        if uploaded_file:
            file_bytes = np.asarray(bytearray(uploaded_file.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, 1)
            st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), caption="Uploaded Image", use_column_width=True)

    # Use Camera
    elif option == "Use Camera":
        img_file_buffer = st.camera_input("Take a picture")
        if img_file_buffer:
            file_bytes = np.asarray(bytearray(img_file_buffer.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, 1)
            st.image(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), caption="Captured Image", use_column_width=True)

    # Emotion Detection
    if img is not None:
        result = DeepFace.analyze(img, actions=['emotion'], enforce_detection=False)
        emotion = result['dominant_emotion']
        st.success(f"Detected Emotion: {emotion}")

        # Map emotion to Spotify keyword
        emotion_map = {
            "happy": "happy",
            "sad": "sad",
            "angry": "rock",
            "surprise": "pop",
            "neutral": "chill",
            "disgust": "lo-fi",
            "fear": "ambient"
        }
        keyword = emotion_map.get(emotion, "chill")

        # Search Spotify for playlists
        results = sp.search(q=keyword, type='playlist', limit=5)

        st.subheader(f"🎶 Recommended Playlists for {emotion.capitalize()} Mood:")
        for idx, item in enumerate(results['playlists']['items']):
            st.markdown(f"**{idx+1}. [{item['name']}]({item['external_urls']['spotify']})**")
            st.components.v1.iframe(item['external_urls']['spotify'], width=300, height=380)# Main Streamlit app
print('Streamlit app code here')
