#!/usr/bin/env python3
"""
🎵 Shlok Music Bot - 24/7 Launcher
Run this file to start the bot with auto-restart and keep-alive features
"""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.keep_alive import start_keep_alive, auto_restart_wrapper
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('Launcher')


async def run_bot():
    """Import and run the bot"""
    from bot import main
    await main()


def main():
    """Main launcher function"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║   🎵  S H L O K   M U S I C   B O T  🎵                       ║
    ║                                                              ║
    ║   High-Quality Discord Music Streaming                       ║
    ║   24/7 Mode Enabled                                          ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Start keep-alive web server (for uptime monitoring services)
    # UptimeRobot will ping this server to keep the bot alive
    # Note: Bot already has its own web server in bot.py, so we don't need this
    # start_keep_alive(port=3000)
    
    logger.info("🚀 Starting Shlok Music Bot...")
    
    try:
        # Run with auto-restart on crashes
        asyncio.run(auto_restart_wrapper(run_bot, max_retries=10, delay=30))
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.critical(f"❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
