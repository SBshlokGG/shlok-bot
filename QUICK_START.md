# 🎵 Shlok Music Bot - Quick Start Reference

## 🚀 ONE-TIME SETUP (5 minutes)

### Local Testing
```bash
cd /Users/ishwarbhingaradiya/Desktop/Shlok
pip install -r requirements.txt
python3 run.py
```

### Deploy to Replit
1. Go to https://replit.com
2. Create new Python project
3. Upload your `/Shlok` folder
4. Add BOT_TOKEN to secrets
5. Click "Run"
6. Get your public URL from webview
7. Copy URL to UptimeRobot

### Keep 24/7 Alive
1. Go to https://uptimerobot.com
2. Add new HTTP monitor
3. URL: `https://your-replit-url/health`
4. Interval: 5 minutes
5. Done! ✅

---

## 💬 COMMAND EXAMPLES

### All These Work (Use Any!)
```
$play song name
/play song name
s!play song name
!play song name
@Bot play song name
/play song name (slash command)
```

### Music
```
$play adele rolling in the deep    🎵 Play a song
$pause                              ⏸️ Pause music
$skip                               ⏭️ Skip to next
$queue                              📋 Show queue
$stop                               ⏹️ Stop & leave
```

### Effects
```
$bassboost                          🔊 Deep bass
$nightcore                          ⚡ Speed up
$vaporwave                          🌊 Slow down
$resetfilter                        🔄 Remove effects
```

### Info
```
$help                               📖 Show commands
$ping                               📡 Check latency
$stats                              📊 Bot statistics
$invite                             🔗 Invite link
```

---

## 🌐 WEB ENDPOINTS

Your bot has a web server! Visit:

```
https://your-replit-url/              Main page (beautiful dashboard)
https://your-replit-url/health        Health check (for UptimeRobot)
https://your-replit-url/ping          Status endpoint
```

---

## 📋 MONITORING DASHBOARD

**UptimeRobot Dashboard:**
- Shows if bot is online/offline
- Response time for each ping
- 24-hour uptime graph
- Alert notifications

**Replit Logs:**
- Click "Run" → see console logs
- Shows all commands executed
- Errors appear in red

---

## ❌ QUICK FIXES

**Bot offline?**
→ Start on Replit or run `python3 run.py`

**Commands not working?**
→ Check prefix is `$` or `/`
→ Bot needs permissions in server

**No sound?**
→ Use `$join` first
→ Check bot is in your voice channel

**UptimeRobot shows DOWN?**
→ Check Replit logs
→ Verify URL is correct in settings
→ Restart bot

---

## 📞 FILES TO KNOW

- `bot.py` - Main bot logic
- `config.py` - Settings & tokens
- `cogs/music_simple.py` - Music commands
- `cogs/utility_new.py` - Help & utility
- `requirements.txt` - Python packages
- `.replit` - Replit configuration
- `DEPLOYMENT_AND_24_7_GUIDE.md` - Full guide (this file!)

---

## 🎯 CHECKLIST

Before deploying:
- [ ] Updated prefixes to $ and /
- [ ] All music commands tested
- [ ] Web server running correctly
- [ ] UptimeRobot monitor created
- [ ] Bot online on Replit
- [ ] Can play music in Discord

---

**Everything is ready! Deploy now! 🚀**
