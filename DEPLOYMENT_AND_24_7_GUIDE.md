# 🎵 Shlok Music Bot - Complete Deployment & 24/7 Setup Guide

**Last Updated:** January 6, 2026  
**Status:** ✅ Ready for Production Deployment  
**All Features:** ✅ Working with `$` and `/` prefixes

---

## 📋 Table of Contents
1. [Quick Summary](#quick-summary)
2. [Feature Overview](#feature-overview)
3. [Prefix Support](#prefix-support)
4. [Deployment Methods](#deployment-methods)
5. [UptimeRobot Setup](#uptimerobot-setup)
6. [Testing Checklist](#testing-checklist)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Quick Summary

Your **Shlok Music Bot** is now ready for production with:
- ✅ **Dual Prefix Support**: Use `$` or `/` for commands
- ✅ **24/7 Mode Enabled**: Built-in keep-alive web server
- ✅ **Web Health Endpoint**: `/health` and `/ping` for monitoring
- ✅ **Beautiful Web Dashboard**: HTML home page at `/`
- ✅ **Slash Commands**: Full Discord slash command support

### What You're Deploying:
```
✅ Advanced Music Player (play, pause, skip, seek, etc.)
✅ Queue Management (queue, shuffle, loop, clear)
✅ Audio Effects (bassboost, nightcore, vaporwave, etc.)
✅ Voice Controls (join, leave, volume)
✅ Utility Commands (help, ping, stats, invite)
✅ Reaction Controls (⏮️ ⏯️ ⏭️ ⏹️ etc.)
```

---

## 🎵 Feature Overview

### Music Commands
```
$play <song>        - Play a song or playlist
$pause              - Pause current song
$resume             - Resume playing
$skip [number]      - Skip to next song
$stop               - Stop and disconnect
$previous           - Play previous song
$seek <seconds>     - Jump to position
$nowplaying         - Show current song
```

### Queue Management
```
$queue              - Show song queue
$shuffle            - Randomize queue
$loop [track/queue] - Toggle loop mode
$clear              - Clear entire queue
$search <query>     - Search for songs
```

### Audio Effects
```
$bassboost          - Enhance bass
$nightcore          - Speed + pitch up
$vaporwave          - Slow + reverb
$resetfilter        - Remove all effects
```

### Voice Controls
```
$join               - Bot joins your voice channel
$leave              - Bot leaves voice channel
$volume <1-100>     - Set volume level
```

### Utility
```
$help               - Show all commands
$ping               - Check bot latency
$stats              - Show bot statistics
$invite             - Get bot invite link
```

### Prefixes Work Interchangeably
```
$play song          ✅ Works
/play song          ✅ Works
s!play song         ✅ Works
!play song          ✅ Works
@Bot play song      ✅ Works (mention prefix)
/play song          ✅ Works (slash commands)
```

---

## 📊 Prefix Support

### What Changed
- **Primary Prefix**: Changed from `s!` to `$`
- **All Prefixes**: `$`, `/`, `s!`, `!`, and `@Bot`
- **Help Text**: Updated to show all available prefixes
- **Configuration**: Updated in `config.py`

### How It Works
The bot's command prefix is now a function that accepts multiple prefixes, making it incredibly flexible for users.

**File Changes:**
- `bot.py` - Updated command_prefix to accept multiple prefixes
- `config.py` - Changed BOT_PREFIXES and BOT_PREFIX
- `cogs/utility_new.py` - Updated help text

---

## 🚀 Deployment Methods

### Method 1: Replit (RECOMMENDED - Easiest, Free)

#### Step 1: Create Replit Account
1. Go to https://replit.com
2. Sign up with GitHub or email
3. Verify your email

#### Step 2: Create New Project
1. Click **"+ Create"** (top left)
2. Search for **"Python"**
3. Click Python template
4. Name: `shlok-music-bot`
5. Click **"Create Replit"**

#### Step 3: Upload Your Files
In the file explorer:
1. Right-click → **"Upload folder"**
2. Upload entire `/Users/ishwarbhingaradiya/Desktop/Shlok/` folder

**File Structure (Keep same):**
```
shlok-music-bot/
├── bot.py
├── run.py
├── config.py
├── requirements.txt
├── start.sh
├── .replit
├── cogs/
│   ├── music_simple.py
│   ├── utility_new.py
│   └── ...
├── core/
│   ├── player.py
│   ├── queue.py
│   ├── track.py
│   └── ...
├── utils/
│   └── keep_alive.py
└── data/
    ├── cache/
    ├── logs/
    └── playlists/
```

#### Step 4: Set Environment Variables
1. Click **🔒 "Secrets"** (left sidebar)
2. Add:
   ```
   Name: BOT_TOKEN
   Value: (your Discord bot token)
   ```
3. Click **"Add Secret"**

#### Step 5: Install Dependencies
1. Open **"Shell"** tab (bottom)
2. Run:
   ```bash
   pip install -r requirements.txt
   ```

#### Step 6: Run the Bot
1. Click **"▶ Run"** (green button, top)
2. Watch logs appear
3. When ready, you should see:
   ```
   🎵 Shlok Music Bot is online!
   🌐 Web server running on port 8000
   ```

#### Step 7: Get Your Public URL
1. Click the **"Webview"** button (top-right area)
2. A URL like `https://shlok-music-bot.username.repl.co` appears
3. Copy this URL - you'll need it for UptimeRobot

#### Step 8: Keep Bot Running 24/7
Two options:

**Option A: UptimeRobot (Free, Recommended)**
- UptimeRobot pings your bot every 5 minutes
- This keeps Replit from putting it to sleep
- See [UptimeRobot Setup](#uptimerobot-setup) below

**Option B: Replit Always On (Paid)**
- $7/month to keep Replit running 24/7
- One-time payment, then bot runs forever
- Go to "Settings" → "Workspace" → "Always On"

---

### Method 2: Local Machine with ngrok (Testing)

#### Step 1: Install Dependencies
```bash
cd /Users/ishwarbhingaradiya/Desktop/Shlok
pip install -r requirements.txt
```

#### Step 2: Start the Bot
```bash
python3 run.py
```

You should see:
```
🎵 Shlok Music Bot is online!
🌐 Web server running on port 8000
```

#### Step 3: Install ngrok
```bash
# macOS with Homebrew
brew install ngrok

# Or download: https://ngrok.com/download
```

#### Step 4: Get ngrok Auth Token
1. Go to https://ngrok.com
2. Sign up (free)
3. Copy your auth token
4. Run: `ngrok config add-authtoken YOUR_TOKEN`

#### Step 5: Expose Your Bot (New Terminal)
```bash
ngrok http 8000
```

You'll see:
```
Forwarding https://abc123.ngrok.io -> http://localhost:8000
```

**Copy `https://abc123.ngrok.io`** - you need this for UptimeRobot

#### Step 6: Set Up UptimeRobot
- See [UptimeRobot Setup](#uptimerobot-setup) below
- Use your ngrok URL as the monitoring target

---

### Method 3: Other Cloud Platforms

#### Railway (Free tier)
1. Go to https://railway.app
2. Connect GitHub or upload files
3. Set start command: `python3 run.py`
4. Deploy and get public URL
5. Add URL to UptimeRobot

#### Heroku (Limited free tier)
1. Go to https://heroku.com
2. Create app and deploy
3. Set environment variable `BOT_TOKEN`
4. Push code and get public URL
5. Add URL to UptimeRobot

---

## 🤖 UptimeRobot Setup (Keep Bot Alive 24/7)

### Why UptimeRobot?
- **Free**: No cost
- **Simple**: Takes 2 minutes to set up
- **Effective**: Pings your bot every 5 minutes
- **Monitoring**: Alerts you if bot goes down

### How It Works
1. UptimeRobot sends HTTP request to `/health` endpoint
2. Your bot's web server responds with status
3. Replit sees activity and keeps bot running
4. Bot never goes to sleep! 🎉

### Setup Steps

#### Step 1: Create UptimeRobot Account
1. Go to https://uptimerobot.com
2. Sign up (free, no credit card needed)
3. Verify email

#### Step 2: Add Monitor
1. Click **"Add New Monitor"**
2. Select **"HTTP(s)"** as monitor type

#### Step 3: Configure Monitor
Fill in these fields:

```
Friendly Name:          Shlok Music Bot
URL:                    https://your-replit-url.repl.co/health
(or https://abc123.ngrok.io/health)

Monitor Type:           HTTP(s)
HTTP Method:            GET
Monitoring Interval:    5 minutes
Timeout:                30 seconds
```

#### Step 4: Save Monitor
1. Scroll down and click **"Create Monitor"**
2. Done! 🎉

**That's it!** UptimeRobot will now:
- Ping your bot every 5 minutes
- Keep Replit from sleeping
- Alert you if anything goes wrong
- Show you uptime statistics

### Verify It's Working
1. Go to https://uptimerobot.com
2. Find your monitor in the list
3. Status should show **GREEN** (Up)
4. Check logs to see ping timestamps

---

## ✅ Testing Checklist

Before going live, test these features:

### Prefix Testing
```
✅ $help                     - Shows commands
✅ /help                     - Works with slash
✅ s!help                    - Works with old prefix
✅ !help                     - Works with single !
✅ @Bot help                 - Works with mention
```

### Music Commands
```
✅ $play rick roll               - Searches and plays
✅ $pause                        - Pauses current song
✅ $resume                       - Resumes
✅ $skip                         - Skips to next
✅ $queue                        - Shows queue
✅ $stop                         - Stops and disconnects
```

### Effects
```
✅ $bassboost                    - Applies bass boost
✅ $nightcore                    - Speeds up music
✅ $resetfilter                  - Removes effects
```

### Utility
```
✅ $ping                         - Shows latency
✅ $stats                        - Shows bot statistics
✅ $invite                       - Shows invite link
```

### Web Server
```
✅ https://your-url/            - Shows HTML page
✅ https://your-url/health      - Shows {"status": "online"}
✅ https://your-url/ping        - Shows health status
```

### UptimeRobot
```
✅ Monitor shows GREEN status
✅ Check time shows updates every 5 minutes
✅ Response time is under 1 second
```

---

## 🔧 Troubleshooting

### Bot Won't Start
**Error:** `Failed to load cog...`

**Solution:**
```bash
pip install -r requirements.txt
# Or specifically:
pip install discord.py yt-dlp aiohttp PyNaCl
```

### Bot Goes Offline After 1 Hour (Replit)
**Reason:** Replit free tier sleeps inactive projects

**Solution:**
1. Set up UptimeRobot (it pings every 5 min, keeping it alive)
2. Or upgrade to Replit Always On ($7/month)

### Commands Don't Work
**Check:**
1. Is prefix correct? Try `$help`
2. Is bot in same server? Invite via `$invite`
3. Is bot in voice channel? Use `$join` first
4. Check bot permissions in server

### No Sound Playing
**Check:**
1. Bot is in voice channel: `$join`
2. FFmpeg is installed: `ffmpeg -version`
3. Try different song: `$play [different song]`

### UptimeRobot Shows RED (Down)
**Check:**
1. Is your bot actually running?
2. Is URL correct in UptimeRobot settings?
3. Check Replit logs for errors
4. Is firewall blocking port 8000?

### Web Server Not Responding
**Fix:**
```bash
# Restart bot
python3 run.py

# Check port is available
lsof -i :8000
```

---

## 📊 Performance Expectations

### Replit + UptimeRobot
- **Uptime**: 99%+ (with UptimeRobot)
- **Latency**: 100-300ms
- **Cost**: $0 (free)
- **Reliability**: Good for small servers

### Response Times
- Commands: < 1 second
- Music start: 2-5 seconds
- Health check: < 500ms

---

## 🔑 Next Steps

### Immediately:
1. ✅ Test all commands locally
2. ✅ Deploy to Replit
3. ✅ Set up UptimeRobot
4. ✅ Verify bot is online

### Later:
1. Invite bot to your Discord server
2. Add DJ role for admin features
3. Customize audio effects if needed
4. Monitor UptimeRobot dashboard

---

## 📞 Support Resources

- **Discord.py Docs**: https://discordpy.readthedocs.io
- **yt-dlp Docs**: https://github.com/yt-dlp/yt-dlp
- **Replit Docs**: https://docs.replit.com
- **UptimeRobot Help**: https://uptimerobot.com/help

---

## 🎉 You're All Set!

Your bot is production-ready with:
- ✅ Flexible prefix support ($, /, !, s!)
- ✅ 24/7 uptime capability
- ✅ Comprehensive command set
- ✅ Beautiful web interface
- ✅ Automated monitoring

**Happy streaming! 🎵**

---

**Bot Version:** 2.0  
**Last Tested:** January 6, 2026  
**Status:** Production Ready ✅
