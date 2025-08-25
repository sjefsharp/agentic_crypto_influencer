import os
from dotenv import load_dotenv

load_dotenv()

GOOGLE_GENAI_API_KEY = os.getenv("GOOGLE_GENAI_API_KEY")
X_CLIENT_ID = os.getenv("X_API_CLIENT_ID")
X_CLIENT_SECRET = os.getenv("X_API_CLIENT_SECRET")
X_API_KEY = os.getenv("X_API_KEY")
X_API_SECRET = os.getenv("X_API_SECRET")
X_ACCESS_TOKEN = os.getenv("X_ACCESS_TOKEN")
X_ACCESS_TOKEN_SECRET = os.getenv("X_ACCESS_TOKEN_SECRET")
X_ENDPOINT = os.getenv("X_ENDPOINT")
X_TWEETS_ENDPOINT = os.environ.get("X_TWEETS_ENDPOINT")
X_REDIRECT_URI = "http://localhost:5000/callback"
X_SCOPES = "tweet.read tweet.write tweet.moderate.write users.email users.read follows.read follows.write offline.access space.read mute.read mute.write like.read like.write list.read list.write block.read block.write bookmark.read bookmark.write media.write"
