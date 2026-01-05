# 🎵 Shlok Music Bot

<div align="center">
  <img src="https://img.shields.io/badge/Discord.py-2.3+-blue?style=for-the-badge&logo=discord" alt="Discord.py">
  <img src="https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python" alt="Python">
  <img src="https://img.shields.io/badge/License-MIT-green?style=for-the-badge" alt="License">
  <img src="https://img.shields.io/badge/Status-24/7-brightgreen?style=for-the-badge" alt="Status">
</div>

<div align="center">
  <h3>🎧 High-Quality Discord Music Bot with Premium Features</h3>
  <p>Advanced music streaming, reaction controls, audio effects, and 24/7 playback</p>
</div>

---

## ✨ Features

### 🎵 Music Playback
- **High-quality streaming** from YouTube and more
- **Smooth playback** with optimized buffering
- **Volume control** (0-150%)
- **Loop modes** (track/queue/off)
- **Seek functionality**

### 🎮 Reaction Controls
Control music without typing commands! Just react to the Now Playing message:

| Reaction | Action |
|:--------:|--------|
| ⏮️ | Previous track |
| ⏯️ | Pause/Resume |
| ⏭️ | Skip track |
| ⏹️ | Stop & clear queue |
| 🔀 | Shuffle queue |
| 🔁 | Loop queue |
| 🔂 | Loop track |
| 🔉 | Volume down |
| 🔊 | Volume up |
| ❤️ | Add to favorites |
| 📋 | Show queue |
| 🎵 | Show lyrics |

### 📋 Advanced Queue System
- **Unlimited queue size**
- **Shuffle & reverse**
- **Move tracks** between positions
- **Skip to specific track**
- **Remove duplicates**
- **Sort by duration/title**
- **Save queues as playlists**

### 🎛️ Audio Effects
Apply real-time audio effects:
- 🔊 **Bass Boost** - Enhanced bass
- ⚡ **Nightcore** - Faster + higher pitch
- 🌊 **Vaporwave** - Slowed aesthetic
- 🎧 **8D Audio** - Rotating sound
- 🎤 **Karaoke** - Remove vocals
- 〰️ **Tremolo** - Wavering volume
- 🎵 **Vibrato** - Wavering pitch
- 🌙 **Soft** - Mellow sound
- 🐿️ **Chipmunk** - High pitch
- 👹 **Deep** - Low pitch

### 🔄 24/7 Mode
- **Always online** - Never stops
- **Auto-reconnect** on disconnects
- **Persistent voice connection**
- **Health monitoring**

### 📝 Additional Features
- 🎤 **Lyrics fetching**
- ❤️ **Favorites system**
- 📊 **Detailed statistics**
- ⚙️ **Per-server settings**
- 🎯 **Slash commands** support

---

## 🚀 Quick Start

### Prerequisites
- **Python 3.10+**
- **FFmpeg** installed on your system
- **Discord Bot Token**

### Installation

1. **Clone or download the bot:**
```bash
cd /path/to/Shlok
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install FFmpeg:**

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt install ffmpeg
```

**Windows:**
Download from [FFmpeg website](https://ffmpeg.org/download.html) and add to PATH

4. **Configure the bot:**
Edit `config.py` and update your bot token if needed.

5. **Run the bot:**
```bash
python bot.py
```

---

## 📖 Commands

### 🎵 Music Commands
| Command | Aliases | Description |
|---------|---------|-------------|
| `!play <query>` | `!p` | Play a song or add to queue |
| `!search <query>` | `!find` | Search and choose from results |
| `!pause` | - | Pause playback |
| `!resume` | `!unpause` | Resume playback |
| `!skip` | `!s`, `!next` | Skip current track |
| `!previous` | `!prev` | Play previous track |
| `!stop` | - | Stop & clear queue |
| `!nowplaying` | `!np` | Show current track |
| `!volume <0-150>` | `!vol` | Set volume |
| `!loop [mode]` | `!l` | Toggle loop mode |
| `!playnow <query>` | `!pn` | Play immediately |
| `!join` | `!j` | Join voice channel |
| `!leave` | `!dc` | Leave voice channel |

### 📋 Queue Commands
| Command | Aliases | Description |
|---------|---------|-------------|
| `!queue [page]` | `!q` | View queue |
| `!shuffle` | `!mix` | Shuffle queue |
| `!clear` | `!empty` | Clear queue |
| `!remove <pos>` | `!rm` | Remove track |
| `!move <from> <to>` | `!mv` | Move track |
| `!skipto <pos>` | `!jump` | Skip to position |
| `!playnext <query>` | `!pnext` | Add to play next |
| `!reverse` | `!rev` | Reverse queue |
| `!removedupes` | `!dedup` | Remove duplicates |
| `!sort duration/title` | - | Sort queue |

### 🎛️ Effects Commands
| Command | Description |
|---------|-------------|
| `!effect` | View all effects |
| `!effect <name>` | Apply effect |
| `!effect reset` | Remove effects |
| `!lyrics [query]` | Get lyrics |
| `!equalizer` | View EQ presets |
| `!speed <0.5-2.0>` | Change speed |
| `!pitch <-12 to 12>` | Change pitch |
| `!favorite add` | Add to favorites |
| `!favorite list` | View favorites |

### 🔧 Utility Commands
| Command | Description |
|---------|-------------|
| `!help [command]` | Show help |
| `!stats` | Bot statistics |
| `!ping` | Check latency |
| `!invite` | Get invite link |
| `!settings` | View settings |
| `!settings 247 on/off` | Toggle 24/7 |
| `!cleanup [amount]` | Clean bot messages |

---

## 🔧 Configuration

Edit `config.py` to customize:

```python
# Bot Settings
BOT_PREFIX = "!"
BOT_COLOR = 0x7289DA

# Music Settings  
MUSIC.default_volume = 50
MUSIC.max_volume = 150
MUSIC.stay_connected_24_7 = True
MUSIC.auto_disconnect_time = 300

# And much more...
```

---

## 🌐 Hosting 24/7

### Option 1: VPS (Recommended)
Host on a VPS like DigitalOcean, Vultr, or AWS EC2.

### Option 2: Railway/Render
Deploy for free with:
- Railway.app
- Render.com
- Fly.io

### Option 3: Local Machine
Keep your computer running with the bot script.

### Using PM2 (for VPS):
```bash
# Install PM2
npm install -g pm2

# Start bot
pm2 start bot.py --interpreter python3

# Auto-restart on crash
pm2 startup
pm2 save
```

---

## 📁 Project Structure

```
Shlok/
├── bot.py              # Main entry point
├── config.py           # Configuration
├── requirements.txt    # Dependencies
├── README.md           # Documentation
│
├── core/               # Core modules
│   ├── __init__.py
│   ├── player.py       # Music player
│   ├── queue.py        # Queue management
│   └── track.py        # Track model
│
├── cogs/               # Command modules
│   ├── __init__.py
│   ├── music.py        # Music commands
│   ├── queue.py        # Queue commands
│   ├── effects.py      # Effects commands
│   ├── utility.py      # Utility commands
│   └── events.py       # Event handlers
│
├── utils/              # Utilities
│   ├── __init__.py
│   └── keep_alive.py   # 24/7 features
│
└── data/               # Data storage
    ├── cache/
    ├── playlists/
    └── logs/
```

---

## ❓ Troubleshooting

### Bot won't join voice channel
- Check if bot has `Connect` and `Speak` permissions
- Make sure you're in a voice channel

### No audio playing
- Verify FFmpeg is installed: `ffmpeg -version`
- Check volume isn't at 0

### Commands not working
- Verify prefix (default: `!`)
- Check bot has `Send Messages` permission

### Bot disconnects randomly
- Enable 24/7 mode: `!settings 247 on`
- Check your internet connection

---

## 📜 License

MIT License - Feel free to use and modify!

---

## 💖 Support

If you like this bot, give it a ⭐!

---

<div align="center">
  <p>Made with ❤️ for Discord</p>
  <p>🎵 <b>Shlok Music Bot</b> - Your Ultimate Music Experience 🎵</p>
</div>
