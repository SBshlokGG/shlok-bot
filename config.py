"""
🎵 Shlok Music Bot - Configuration
Advanced Discord Music Bot with Premium Features
"""

import os
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ═══════════════════════════════════════════════════════════════
# 🔑 BOT CREDENTIALS
# ═══════════════════════════════════════════════════════════════

# Read from environment variable (for Render/cloud deployment)
# IMPORTANT: Set BOT_TOKEN as environment variable in Render
BOT_TOKEN = os.environ.get('BOT_TOKEN', 'YOUR_TOKEN_HERE')
APPLICATION_ID = "1097878151713017896"
PUBLIC_KEY = "f2c775c1330a7202c71f9ad691bee729da46aecf0d883291dc13dd9735293341"

# ═══════════════════════════════════════════════════════════════
# 🎨 BOT APPEARANCE
# ═══════════════════════════════════════════════════════════════

BOT_NAME = "Shlok Music"
BOT_PREFIXES = ['$', '/', 's!', '!']  # Multiple prefixes: $ and / are primary
BOT_PREFIX = "$"  # Primary prefix for display
BOT_COLOR = 0x7289DA  # Discord Blurple
BOT_COLOR_SUCCESS = 0x2ECC71  # Green
BOT_COLOR_ERROR = 0xE74C3C  # Red
BOT_COLOR_WARNING = 0xF39C12  # Orange
BOT_COLOR_INFO = 0x3498DB  # Blue

# ═══════════════════════════════════════════════════════════════
# 🎵 MUSIC SETTINGS
# ═══════════════════════════════════════════════════════════════

@dataclass
class MusicSettings:
    """Music player configuration"""
    default_volume: int = 250
    max_volume: int = 500
    min_volume: int = 0
    
    max_queue_size: int = 500
    max_song_duration: int = 7200  # 2 hours in seconds
    
    auto_disconnect_time: int = 300  # 5 minutes of inactivity
    stay_connected_24_7: bool = True  # 24/7 mode enabled
    
    default_search_limit: int = 5
    max_playlist_size: int = 100
    
    # Audio quality
    audio_bitrate: int = 128  # kbps
    audio_sample_rate: int = 48000  # Hz
    
    # Buffer settings for smooth playback
    buffer_size: int = 32768
    reconnect_attempts: int = 5
    
MUSIC = MusicSettings()

# ═══════════════════════════════════════════════════════════════
# 🎛️ AUDIO EFFECTS PRESETS
# ═══════════════════════════════════════════════════════════════

AUDIO_EFFECTS = {
    "none": {},
    "bass_boost": {
        "equalizer": [(0, 0.25), (1, 0.20), (2, 0.15), (3, 0.10)],
        "description": "🔊 Enhanced bass frequencies"
    },
    "nightcore": {
        "timescale": {"speed": 1.25, "pitch": 1.25, "rate": 1.0},
        "description": "⚡ Faster tempo with higher pitch"
    },
    "vaporwave": {
        "timescale": {"speed": 0.8, "pitch": 0.85, "rate": 1.0},
        "description": "🌊 Slowed and reverbed aesthetic"
    },
    "8d": {
        "rotation": {"rotation_hz": 0.2},
        "description": "🎧 360° rotating audio effect"
    },
    "karaoke": {
        "karaoke": {"level": 1.0, "mono_level": 1.0, "filter_band": 220, "filter_width": 100},
        "description": "🎤 Removes vocals from the track"
    },
    "tremolo": {
        "tremolo": {"frequency": 4.0, "depth": 0.6},
        "description": "〰️ Wavering volume effect"
    },
    "vibrato": {
        "vibrato": {"frequency": 4.0, "depth": 0.6},
        "description": "🎵 Wavering pitch effect"
    },
    "soft": {
        "lowpass": {"smoothing": 20.0},
        "description": "🌙 Soft and mellow sound"
    },
    "chipmunk": {
        "timescale": {"speed": 1.0, "pitch": 1.5, "rate": 1.0},
        "description": "🐿️ High pitched voice"
    },
    "deep": {
        "timescale": {"speed": 1.0, "pitch": 0.7, "rate": 1.0},
        "description": "👹 Deep voice effect"
    },
}

# ═══════════════════════════════════════════════════════════════
# 🎮 REACTION CONTROLS
# ═══════════════════════════════════════════════════════════════

REACTION_CONTROLS = {
    "⏯️": "pause_resume",      # Pause/Resume
    "⏭️": "skip",              # Skip
    "⏹️": "stop",              # Stop
    "🔀": "shuffle",           # Shuffle
    "🔁": "loop_queue",        # Loop queue
    "🔂": "loop_track",        # Loop track
    "🔉": "volume_down",       # Volume down
    "🔊": "volume_up",         # Volume up
    "❤️": "favorite",          # Add to favorites
    "📋": "show_queue",        # Show queue
    "🎵": "lyrics",            # Show lyrics
    "⏮️": "previous",          # Previous track
}

# Reaction emojis in order (for adding to messages)
CONTROL_EMOJIS = ["⏮️", "⏯️", "⏭️", "⏹️", "🔀", "🔁", "🔂", "🔉", "🔊", "❤️", "📋", "🎵"]

# ═══════════════════════════════════════════════════════════════
# 📊 PROGRESS BAR SETTINGS
# ═══════════════════════════════════════════════════════════════

PROGRESS_BAR = {
    "length": 20,
    "filled": "▰",
    "empty": "▱",
    "start_filled": "▰",
    "end_filled": "▰",
    "start_empty": "▱",
    "end_empty": "▱",
}

# ═══════════════════════════════════════════════════════════════
# 🔧 YTDL OPTIONS (Optimized for performance)
# ═══════════════════════════════════════════════════════════════

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': False,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'force_generic_extractor': False,
    'cachedir': False,
    'extract_flat': 'in_playlist',
    'socket_timeout': 30,
    'retries': 5,
    'fragment_retries': 5,
    'skip_unavailable_fragments': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    },
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web'],
            'player_skip': ['js', 'configs']
        }
    },
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin',
    'options': '-vn -b:a 128k'
}

# ═══════════════════════════════════════════════════════════════
# 📝 EMBED TEMPLATES
# ═══════════════════════════════════════════════════════════════

EMBED_ICONS = {
    "music": "🎵",
    "play": "▶️",
    "pause": "⏸️",
    "stop": "⏹️",
    "skip": "⏭️",
    "queue": "📋",
    "volume": "🔊",
    "loop": "🔁",
    "shuffle": "🔀",
    "error": "❌",
    "success": "✅",
    "warning": "⚠️",
    "info": "ℹ️",
    "search": "🔍",
    "loading": "⏳",
    "heart": "❤️",
    "star": "⭐",
    "fire": "🔥",
    "sparkle": "✨",
    "headphones": "🎧",
    "microphone": "🎤",
    "notes": "🎶",
    "cd": "💿",
    "radio": "📻",
}

# ═══════════════════════════════════════════════════════════════
# ⚙️ PERMISSIONS & ROLES
# ═══════════════════════════════════════════════════════════════

DJ_ROLE_NAME = "DJ"
ADMIN_COMMANDS = ["forceskip", "forceplay", "clear", "disconnect", "settings"]

# ═══════════════════════════════════════════════════════════════
# 🎵 LAVALINK NODES (Professional Audio Streaming)
# ═══════════════════════════════════════════════════════════════

LAVALINK_NODES = [
    {
        "uri": "http://node.lewdhutao.my.eu.org:80",
        "password": "youshallnotpass",
        "identifier": "MAIN"
    },
]

# ═══════════════════════════════════════════════════════════════
# 📊 SPOTIFY INTEGRATION (Optional)
# ═══════════════════════════════════════════════════════════════

SPOTIFY_CLIENT_ID = ""  # Add your Spotify client ID
SPOTIFY_CLIENT_SECRET = ""  # Add your Spotify client secret

# ═══════════════════════════════════════════════════════════════
# 🌐 API ENDPOINTS
# ═══════════════════════════════════════════════════════════════

LYRICS_API = "https://api.lyrics.ovh/v1"
GENIUS_API_TOKEN = ""  # Optional: Add Genius API token for better lyrics

# ═══════════════════════════════════════════════════════════════
# 📁 PATHS
# ═══════════════════════════════════════════════════════════════

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
CACHE_DIR = os.path.join(DATA_DIR, "cache")
PLAYLISTS_DIR = os.path.join(DATA_DIR, "playlists")
LOGS_DIR = os.path.join(DATA_DIR, "logs")

# Create directories if they don't exist
for directory in [DATA_DIR, CACHE_DIR, PLAYLISTS_DIR, LOGS_DIR]:
    os.makedirs(directory, exist_ok=True)

# ═══════════════════════════════════════════════════════════════
# 🔄 STATUS ROTATION
# ═══════════════════════════════════════════════════════════════

BOT_ACTIVITIES = [
    {"type": "listening", "name": "/help | Music 24/7"},
    {"type": "watching", "name": "shlok.kesug.com"},
    {"type": "listening", "name": "{users} users"},
    {"type": "playing", "name": "🎵 High Quality Music"},
    {"type": "listening", "name": "{guilds} servers"},
    {"type": "competing", "name": "music streaming"},
]

# Activity rotation interval (seconds)
ACTIVITY_ROTATION_INTERVAL = 30
