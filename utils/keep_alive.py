"""
🔄 Keep Alive Module
Keeps the bot running 24/7 with multiple strategies
"""

import asyncio
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

logger = logging.getLogger('ShlokMusic.KeepAlive')

# ═══════════════════════════════════════════════════════════════
# 🌐 WEB SERVER FOR UPTIME MONITORING
# ═══════════════════════════════════════════════════════════════

class KeepAliveHandler(BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks"""
    
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>🎵 Shlok Music Bot</title>
            <style>
                body {
                    font-family: 'Segoe UI', sans-serif;
                    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .container {
                    text-align: center;
                    padding: 40px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                }
                h1 { 
                    font-size: 3em; 
                    margin-bottom: 10px;
                }
                .status {
                    color: #2ecc71;
                    font-size: 1.5em;
                }
                .pulse {
                    animation: pulse 2s infinite;
                }
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎵 Shlok Music Bot</h1>
                <p class="status pulse">✅ Online & Running</p>
                <p>High-quality Discord music streaming 24/7</p>
            </div>
        </body>
        </html>
        """
        
        self.wfile.write(html.encode())
    
    def log_message(self, format, *args):
        """Suppress HTTP logs"""
        pass


def run_server(port: int = 8080):
    """Run the keep-alive HTTP server"""
    try:
        server = HTTPServer(('0.0.0.0', port), KeepAliveHandler)
        logger.info(f"🌐 Keep-alive server running on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.error(f"❌ Failed to start keep-alive server: {e}")


def start_keep_alive(port: int = 8080):
    """Start the keep-alive server in a background thread"""
    thread = threading.Thread(target=run_server, args=(port,), daemon=True)
    thread.start()
    logger.info("🔄 Keep-alive service started")
    return thread


# ═══════════════════════════════════════════════════════════════
# 🔄 AUTO-RESTART WRAPPER
# ═══════════════════════════════════════════════════════════════

async def auto_restart_wrapper(main_func, max_retries: int = 5, delay: int = 30):
    """
    Wrapper that automatically restarts the bot on crashes
    
    Args:
        main_func: The main bot function to run
        max_retries: Maximum consecutive restart attempts
        delay: Delay between restarts in seconds
    """
    retries = 0
    
    while retries < max_retries:
        try:
            logger.info(f"🚀 Starting bot (attempt {retries + 1}/{max_retries})...")
            await main_func()
        except Exception as e:
            retries += 1
            logger.error(f"❌ Bot crashed: {e}")
            
            if retries < max_retries:
                logger.info(f"🔄 Restarting in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                logger.critical(f"❌ Max retries ({max_retries}) reached. Giving up.")
                raise
        else:
            # Reset retries on successful run (graceful shutdown)
            retries = 0
            break


# ═══════════════════════════════════════════════════════════════
# 💓 HEARTBEAT SYSTEM
# ═══════════════════════════════════════════════════════════════

class Heartbeat:
    """
    Heartbeat system for monitoring bot health
    """
    
    def __init__(self, interval: int = 30):
        self.interval = interval
        self.last_beat = None
        self.running = False
        self._task = None
    
    async def start(self, bot):
        """Start the heartbeat"""
        self.running = True
        self._task = asyncio.create_task(self._heartbeat_loop(bot))
        logger.info("💓 Heartbeat started")
    
    async def stop(self):
        """Stop the heartbeat"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("💔 Heartbeat stopped")
    
    async def _heartbeat_loop(self, bot):
        """Main heartbeat loop"""
        while self.running:
            try:
                self.last_beat = asyncio.get_event_loop().time()
                
                # Check bot health
                if not bot.is_closed():
                    latency = bot.latency * 1000
                    
                    if latency > 1000:
                        logger.warning(f"⚠️ High latency detected: {latency:.0f}ms")
                    
                    # Check voice connections
                    for guild_id, player in bot.music_players.items():
                        if player.voice_client and not player.voice_client.is_connected():
                            logger.warning(f"⚠️ Lost voice connection in guild {guild_id}")
                            try:
                                await player.reconnect()
                            except:
                                pass
                
                await asyncio.sleep(self.interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Heartbeat error: {e}")
                await asyncio.sleep(5)


# ═══════════════════════════════════════════════════════════════
# 📊 HEALTH CHECK
# ═══════════════════════════════════════════════════════════════

def get_health_status(bot) -> dict:
    """
    Get comprehensive health status of the bot
    
    Returns:
        dict: Health status information
    """
    return {
        "status": "online" if not bot.is_closed() else "offline",
        "latency_ms": round(bot.latency * 1000, 2),
        "guilds": len(bot.guilds),
        "voice_connections": sum(1 for p in bot.music_players.values() if p.is_connected),
        "uptime_seconds": (asyncio.get_event_loop().time() - bot.start_time.timestamp()) if bot.start_time else 0,
        "songs_played": bot.songs_played,
        "commands_used": bot.commands_used,
    }
