"""
🎵 Shlok Music Bot - Main Entry Point
Simple & Reliable Discord Music Bot with Web Server for Monitoring
"""

import asyncio
import logging
import sys
import os
from datetime import datetime
from aiohttp import web

import discord
from discord.ext import commands, tasks
from discord import opus

import config

# ═══════════════════════════════════════════════════════════════
# 🌐 WEB SERVER FOR UPTIME MONITORING
# ═══════════════════════════════════════════════════════════════

WEB_PORT = int(os.environ.get('PORT', 3000))

async def handle_health(request):
    """Health check endpoint for UptimeRobot"""
    return web.json_response({
        'status': 'online',
        'bot': 'Shlok Music',
        'timestamp': datetime.now().isoformat()
    })

async def handle_home(request):
    """Home page"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎵 Shlok Music Bot</title>
        <style>
            body { font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                   color: white; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .container { text-align: center; padding: 40px; background: rgba(0,0,0,0.3); border-radius: 20px; }
            h1 { font-size: 3em; margin-bottom: 10px; }
            p { font-size: 1.2em; opacity: 0.9; }
            .status { background: #2ecc71; padding: 10px 30px; border-radius: 50px; display: inline-block; margin-top: 20px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎵 Shlok Music Bot</h1>
            <p>High-Quality Discord Music Streaming</p>
            <div class="status">✅ Online</div>
        </div>
    </body>
    </html>
    """
    return web.Response(text=html, content_type='text/html')

async def start_web_server():
    """Start the web server for monitoring"""
    app = web.Application()
    app.router.add_get('/', handle_home)
    app.router.add_get('/health', handle_health)
    app.router.add_get('/ping', handle_health)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', WEB_PORT)
    await site.start()
    print(f"🌐 Web server running on port {WEB_PORT}")
    return runner

# ═══════════════════════════════════════════════════════════════
# 🔊 LOAD OPUS LIBRARY
# ═══════════════════════════════════════════════════════════════

def load_opus():
    """Load the opus library for voice support"""
    if opus.is_loaded():
        return True
    
    # Try common opus library paths on macOS
    opus_paths = [
        '/opt/homebrew/lib/libopus.dylib',  # Apple Silicon Homebrew
        '/opt/homebrew/lib/libopus.0.dylib',
        '/usr/local/lib/libopus.dylib',  # Intel Homebrew
        '/usr/local/lib/libopus.0.dylib',
        '/usr/lib/libopus.dylib',
        '/usr/lib/libopus.so.0',
        'libopus.so.0',
        'opus',
    ]
    
    for path in opus_paths:
        try:
            opus.load_opus(path)
            if opus.is_loaded():
                return True
        except Exception:
            continue
    
    return False

# Load opus at module level
if not load_opus():
    print("⚠️ Warning: Could not load opus library. Voice may not work.")
else:
    print("✅ Opus library loaded successfully")

# ═══════════════════════════════════════════════════════════════
# 📝 LOGGING SETUP
# ═══════════════════════════════════════════════════════════════

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            os.path.join(config.LOGS_DIR, f'bot_{datetime.now().strftime("%Y%m%d")}.log'),
            encoding='utf-8'
        )
    ]
)

logger = logging.getLogger('ShlokMusic')

# ═══════════════════════════════════════════════════════════════
# 🤖 BOT CLASS
# ═══════════════════════════════════════════════════════════════

class ShlokMusicBot(commands.Bot):
    """Simple & Reliable Discord Music Bot"""
    
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        intents.guilds = True
        intents.members = True
        intents.reactions = True
        
        super().__init__(
            command_prefix=commands.when_mentioned_or('s!', '$', '!'),
            intents=intents,
            application_id=config.APPLICATION_ID,
            case_insensitive=True,
            strip_after_prefix=True,
            help_command=None,
        )
        
        self.start_time = None
        self.activity_index = 0
        
    async def setup_hook(self):
        """Initialize the bot"""
        logger.info("🔧 Setting up Shlok Music Bot...")
        
        # Load cogs
        cogs = [
            'cogs.music_simple',
            'cogs.utility_new',
        ]
        
        for cog in cogs:
            try:
                await self.load_extension(cog)
                logger.info(f"✅ Loaded: {cog}")
            except Exception as e:
                logger.error(f"❌ Failed to load {cog}: {e}")
                import traceback
                traceback.print_exc()
        
        # Force sync slash commands globally
        try:
            synced = await self.tree.sync()
            logger.info(f"✅ Synced {len(synced)} slash commands globally")
        except Exception as e:
            logger.error(f"❌ Failed to sync: {e}")
    
    async def on_ready(self):
        """Bot is ready"""
        self.start_time = datetime.now()
        
        logger.info("━" * 50)
        logger.info(f"🎵 {config.BOT_NAME} is online!")
        logger.info(f"📊 Servers: {len(self.guilds)}")
        logger.info(f"👥 Users: {sum(g.member_count for g in self.guilds):,}")
        logger.info(f"🤖 {self.user} (ID: {self.user.id})")
        logger.info(f"📡 Latency: {round(self.latency * 1000)}ms")
        logger.info("━" * 50)
        
        if not self.rotate_activity.is_running():
            self.rotate_activity.start()
    
    @tasks.loop(seconds=30)
    async def rotate_activity(self):
        """Rotate status"""
        activities = config.BOT_ACTIVITIES
        data = activities[self.activity_index % len(activities)]
        
        name = data["name"].format(
            guilds=len(self.guilds),
            users=sum(g.member_count for g in self.guilds)
        )
        
        activity_type = {
            "playing": discord.ActivityType.playing,
            "listening": discord.ActivityType.listening,
            "watching": discord.ActivityType.watching,
            "competing": discord.ActivityType.competing,
        }.get(data["type"], discord.ActivityType.playing)
        
        await self.change_presence(
            activity=discord.Activity(type=activity_type, name=name),
            status=discord.Status.online
        )
        
        self.activity_index += 1
    
    @rotate_activity.before_loop
    async def before_rotate(self):
        await self.wait_until_ready()
    
    async def close(self):
        """Cleanup"""
        logger.info("🛑 Shutting down...")
        
        for vc in self.voice_clients:
            try:
                await vc.disconnect()
            except:
                pass
        
        await super().close()

# ═══════════════════════════════════════════════════════════════
# 🚀 MAIN
# ═══════════════════════════════════════════════════════════════

async def main():
    bot = ShlokMusicBot()
    web_runner = None
    
    try:
        # Start web server for UptimeRobot monitoring
        web_runner = await start_web_server()
        
        # Start the bot
        await bot.start(config.BOT_TOKEN)
    except discord.LoginFailure:
        logger.critical("❌ Invalid token!")
    except Exception as e:
        logger.critical(f"❌ Error: {e}")
    finally:
        if web_runner:
            await web_runner.cleanup()
        await bot.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Stopped by user")
