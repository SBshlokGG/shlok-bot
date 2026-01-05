"""
🎵 Music Player Core Engine
Handles all audio playback and voice connection logic
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum

import discord
from discord.ext import commands

import config
from core.queue import MusicQueue
from core.track import Track

logger = logging.getLogger('ShlokMusic.Player')

# ═══════════════════════════════════════════════════════════════
# 🔄 LOOP MODES
# ═══════════════════════════════════════════════════════════════

class LoopMode(Enum):
    """Loop mode enumeration"""
    OFF = 0
    TRACK = 1
    QUEUE = 2

# ═══════════════════════════════════════════════════════════════
# 🎵 MUSIC PLAYER CLASS
# ═══════════════════════════════════════════════════════════════

class MusicPlayer:
    """
    Advanced Music Player for a Discord Guild
    
    Features:
    - High-quality audio streaming
    - Queue management
    - Loop modes (track/queue)
    - Volume control
    - Audio effects
    - Auto-reconnect
    - 24/7 mode support
    """
    
    def __init__(self, bot: commands.Bot, guild_id: int):
        self.bot = bot
        self.guild_id = guild_id
        
        # Voice connection
        self.voice_client: Optional[discord.VoiceClient] = None
        self.text_channel: Optional[discord.TextChannel] = None
        
        # Queue
        self.queue = MusicQueue()
        
        # Current track
        self.current_track: Optional[Track] = None
        self.now_playing_message: Optional[discord.Message] = None
        
        # Player state
        self.volume = config.MUSIC.default_volume / 100
        self.loop_mode = LoopMode.OFF
        self.is_paused = False
        self.is_playing = False
        
        # Audio effect
        self.current_effect = "none"
        
        # Track timing
        self.track_start_time: Optional[datetime] = None
        self.paused_duration = timedelta()
        self.pause_start_time: Optional[datetime] = None
        
        # History
        self.history: List[Track] = []
        self.max_history = 50
        
        # Favorites per user
        self.favorites: Dict[int, List[Track]] = {}
        
        # Auto-update task
        self._progress_task: Optional[asyncio.Task] = None
        self._play_lock = asyncio.Lock()
        
        # 24/7 mode
        self.stay_connected = config.MUSIC.stay_connected_24_7
        
    @property
    def guild(self) -> Optional[discord.Guild]:
        """Get the guild object"""
        return self.bot.get_guild(self.guild_id)
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to voice"""
        return self.voice_client is not None and self.voice_client.is_connected()
    
    @property
    def elapsed_time(self) -> timedelta:
        """Get elapsed time of current track"""
        if not self.track_start_time:
            return timedelta()
        
        elapsed = datetime.now() - self.track_start_time - self.paused_duration
        
        if self.is_paused and self.pause_start_time:
            elapsed -= (datetime.now() - self.pause_start_time)
        
        return elapsed
    
    # ═══════════════════════════════════════════════════════════
    # 🔊 CONNECTION METHODS
    # ═══════════════════════════════════════════════════════════
    
    async def connect(self, channel: discord.VoiceChannel) -> bool:
        """Connect to a voice channel with retry logic"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Clean up existing connection first
                if self.voice_client:
                    try:
                        if self.voice_client.is_connected():
                            await self.voice_client.move_to(channel)
                            logger.info(f"🔊 Moved to {channel.name} in {channel.guild.name}")
                            return True
                        else:
                            # Cleanup stale connection
                            try:
                                await self.voice_client.disconnect(force=True)
                            except:
                                pass
                            self.voice_client = None
                    except Exception as e:
                        logger.warning(f"⚠️ Error with existing connection: {e}")
                        try:
                            await self.voice_client.disconnect(force=True)
                        except:
                            pass
                        self.voice_client = None
                
                # Fresh connection with longer timeout
                logger.info(f"🔄 Connecting to {channel.name} (attempt {attempt + 1}/{max_retries})...")
                
                self.voice_client = await channel.connect(
                    timeout=60.0,  # Longer timeout
                    reconnect=True,
                    self_deaf=True
                )
                
                # Wait a moment for connection to stabilize
                await asyncio.sleep(0.5)
                
                if self.voice_client and self.voice_client.is_connected():
                    logger.info(f"🔊 Connected to {channel.name} in {channel.guild.name}")
                    return True
                    
            except asyncio.TimeoutError:
                logger.warning(f"⏱️ Timeout connecting to {channel.name} (attempt {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)  # Wait before retry
                continue
            except discord.ClientException as e:
                logger.warning(f"⚠️ Client exception: {e}")
                # Already connected somewhere, try to cleanup
                for vc in self.bot.voice_clients:
                    if vc.guild.id == channel.guild.id:
                        try:
                            await vc.disconnect(force=True)
                        except:
                            pass
                self.voice_client = None
                await asyncio.sleep(1)
                continue
            except Exception as e:
                logger.error(f"❌ Error connecting to voice: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                continue
        
        logger.error(f"❌ Failed to connect after {max_retries} attempts")
        return False
    
    async def disconnect(self):
        """Disconnect from voice channel"""
        try:
            self.stop()
            
            if self.voice_client:
                await self.voice_client.disconnect(force=True)
                self.voice_client = None
            
            # Clear state
            self.current_track = None
            self.is_playing = False
            self.is_paused = False
            
            logger.info(f"👋 Disconnected from voice in guild {self.guild_id}")
            
        except Exception as e:
            logger.error(f"❌ Error disconnecting: {e}")
    
    async def reconnect(self):
        """Reconnect to the last voice channel"""
        if self.voice_client and self.voice_client.channel:
            channel = self.voice_client.channel
            await self.disconnect()
            await asyncio.sleep(1)
            await self.connect(channel)
    
    # ═══════════════════════════════════════════════════════════
    # ▶️ PLAYBACK CONTROLS
    # ═══════════════════════════════════════════════════════════
    
    async def play(self, track: Track) -> bool:
        """Play a track"""
        async with self._play_lock:
            if not self.is_connected:
                logger.error("❌ Not connected to voice channel")
                return False
            
            try:
                # Stop current playback
                if self.voice_client.is_playing():
                    self.voice_client.stop()
                
                if self.voice_client.is_paused():
                    self.voice_client.stop()
                
                logger.info(f"🎵 Getting audio source for: {track.title}")
                
                # Get audio source
                source = await track.get_source()
                if not source:
                    logger.error(f"❌ Failed to get audio source for: {track.title}")
                    # Try to play next track
                    await self.play_next()
                    return False
                
                logger.info(f"🎵 Audio source obtained, applying volume transformer")
                
                # Apply volume
                source = discord.PCMVolumeTransformer(source, volume=self.volume)
                
                logger.info(f"🎵 Starting playback...")
                
                # Play with error handling
                def after_play(error):
                    if error:
                        logger.error(f"❌ Playback error: {error}")
                    self.bot.loop.call_soon_threadsafe(
                        lambda: asyncio.create_task(self._on_track_end(error))
                    )
                
                self.voice_client.play(source, after=after_play)
                
                # Update state
                self.current_track = track
                self.is_playing = True
                self.is_paused = False
                self.track_start_time = datetime.now()
                self.paused_duration = timedelta()
                self.pause_start_time = None
                
                # Add to history
                self._add_to_history(track)
                
                # Update stats
                self.bot.songs_played += 1
                
                logger.info(f"▶️ Now playing: {track.title}")
                
                # Send now playing message
                await self._send_now_playing()
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Error playing track: {e}")
                return False
    
    async def play_next(self):
        """Play the next track in queue"""
        # Handle loop mode
        if self.loop_mode == LoopMode.TRACK and self.current_track:
            await self.play(self.current_track)
            return
        
        if self.loop_mode == LoopMode.QUEUE and self.current_track:
            self.queue.add(self.current_track)
        
        # Get next track
        next_track = self.queue.get_next()
        
        if next_track:
            await self.play(next_track)
        else:
            self.current_track = None
            self.is_playing = False
            
            # Send queue empty message
            if self.text_channel:
                embed = discord.Embed(
                    title="📋 Queue Finished",
                    description="The queue is empty. Add more songs with `!play`",
                    color=config.BOT_COLOR_INFO
                )
                await self.text_channel.send(embed=embed, delete_after=30)
            
            # Handle 24/7 mode
            if not self.stay_connected:
                await asyncio.sleep(config.MUSIC.auto_disconnect_time)
                if not self.is_playing:
                    await self.disconnect()
    
    def pause(self) -> bool:
        """Pause playback"""
        if self.voice_client and self.voice_client.is_playing():
            self.voice_client.pause()
            self.is_paused = True
            self.pause_start_time = datetime.now()
            return True
        return False
    
    def resume(self) -> bool:
        """Resume playback"""
        if self.voice_client and self.voice_client.is_paused():
            self.voice_client.resume()
            self.is_paused = False
            
            if self.pause_start_time:
                self.paused_duration += datetime.now() - self.pause_start_time
                self.pause_start_time = None
            
            return True
        return False
    
    def stop(self):
        """Stop playback"""
        if self.voice_client:
            self.voice_client.stop()
        
        self.current_track = None
        self.is_playing = False
        self.is_paused = False
        self.queue.clear()
    
    async def skip(self) -> bool:
        """Skip current track"""
        if self.voice_client and (self.voice_client.is_playing() or self.voice_client.is_paused()):
            self.voice_client.stop()
            return True
        return False
    
    async def previous(self) -> bool:
        """Play previous track"""
        if self.history:
            track = self.history.pop()
            
            # Add current track back to front of queue
            if self.current_track:
                self.queue.add_to_front(self.current_track)
            
            await self.play(track)
            return True
        return False
    
    def set_volume(self, volume: int) -> bool:
        """Set volume (0-150)"""
        volume = max(config.MUSIC.min_volume, min(config.MUSIC.max_volume, volume))
        self.volume = volume / 100
        
        if self.voice_client and self.voice_client.source:
            self.voice_client.source.volume = self.volume
        
        return True
    
    def toggle_loop(self) -> LoopMode:
        """Toggle loop mode"""
        if self.loop_mode == LoopMode.OFF:
            self.loop_mode = LoopMode.TRACK
        elif self.loop_mode == LoopMode.TRACK:
            self.loop_mode = LoopMode.QUEUE
        else:
            self.loop_mode = LoopMode.OFF
        
        return self.loop_mode
    
    def set_loop_track(self) -> LoopMode:
        """Set loop mode to track"""
        self.loop_mode = LoopMode.TRACK if self.loop_mode != LoopMode.TRACK else LoopMode.OFF
        return self.loop_mode
    
    def set_loop_queue(self) -> LoopMode:
        """Set loop mode to queue"""
        self.loop_mode = LoopMode.QUEUE if self.loop_mode != LoopMode.QUEUE else LoopMode.OFF
        return self.loop_mode
    
    # ═══════════════════════════════════════════════════════════
    # 📊 PROGRESS & NOW PLAYING
    # ═══════════════════════════════════════════════════════════
    
    def get_progress_bar(self) -> str:
        """Generate a progress bar for current track"""
        if not self.current_track or not self.current_track.duration:
            return ""
        
        elapsed = self.elapsed_time.total_seconds()
        total = self.current_track.duration
        
        progress = min(elapsed / total, 1.0) if total > 0 else 0
        
        bar_length = config.PROGRESS_BAR["length"]
        filled_length = int(bar_length * progress)
        
        bar = (
            config.PROGRESS_BAR["filled"] * filled_length +
            config.PROGRESS_BAR["empty"] * (bar_length - filled_length)
        )
        
        elapsed_str = self._format_duration(int(elapsed))
        total_str = self._format_duration(int(total))
        
        return f"`{elapsed_str}` {bar} `{total_str}`"
    
    async def _send_now_playing(self):
        """Send or update now playing message"""
        if not self.text_channel or not self.current_track:
            return
        
        embed = self._create_now_playing_embed()
        
        try:
            # Delete old message
            if self.now_playing_message:
                try:
                    await self.now_playing_message.delete()
                except:
                    pass
            
            # Send new message
            self.now_playing_message = await self.text_channel.send(embed=embed)
            
            # Add reaction controls
            for emoji in config.CONTROL_EMOJIS:
                try:
                    await self.now_playing_message.add_reaction(emoji)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"❌ Error sending now playing: {e}")
    
    def _create_now_playing_embed(self) -> discord.Embed:
        """Create now playing embed"""
        track = self.current_track
        
        embed = discord.Embed(
            color=config.BOT_COLOR
        )
        
        # Title with status
        status = "⏸️ Paused" if self.is_paused else "▶️ Now Playing"
        embed.title = f"{status}"
        
        # Track info
        embed.description = f"**[{track.title}]({track.url})**\n\n{self.get_progress_bar()}"
        
        # Thumbnail
        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)
        
        # Fields
        embed.add_field(
            name="👤 Artist",
            value=track.artist or "Unknown",
            inline=True
        )
        embed.add_field(
            name="⏱️ Duration",
            value=self._format_duration(track.duration) if track.duration else "Live",
            inline=True
        )
        embed.add_field(
            name="🔊 Volume",
            value=f"{int(self.volume * 100)}%",
            inline=True
        )
        
        # Loop mode
        loop_str = {
            LoopMode.OFF: "❌ Off",
            LoopMode.TRACK: "🔂 Track",
            LoopMode.QUEUE: "🔁 Queue"
        }[self.loop_mode]
        
        embed.add_field(name="🔄 Loop", value=loop_str, inline=True)
        embed.add_field(name="📋 Queue", value=f"{len(self.queue)} tracks", inline=True)
        embed.add_field(name="🎛️ Effect", value=self.current_effect.title(), inline=True)
        
        # Requester
        if track.requester:
            embed.set_footer(
                text=f"Requested by {track.requester.display_name}",
                icon_url=track.requester.display_avatar.url
            )
        
        return embed
    
    async def update_now_playing(self):
        """Update the now playing message"""
        if self.now_playing_message and self.current_track:
            try:
                embed = self._create_now_playing_embed()
                await self.now_playing_message.edit(embed=embed)
            except discord.NotFound:
                self.now_playing_message = None
            except:
                pass
    
    # ═══════════════════════════════════════════════════════════
    # 🔧 HELPER METHODS
    # ═══════════════════════════════════════════════════════════
    
    async def _on_track_end(self, error):
        """Called when a track ends"""
        if error:
            logger.error(f"❌ Playback error: {error}")
        
        await self.play_next()
    
    def _add_to_history(self, track: Track):
        """Add track to history"""
        self.history.append(track)
        
        if len(self.history) > self.max_history:
            self.history.pop(0)
    
    @staticmethod
    def _format_duration(seconds: int) -> str:
        """Format seconds to mm:ss or hh:mm:ss"""
        if seconds < 0:
            seconds = 0
        
        hours, remainder = divmod(seconds, 3600)
        minutes, secs = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        return f"{minutes}:{secs:02d}"
    
    # ═══════════════════════════════════════════════════════════
    # ❤️ FAVORITES
    # ═══════════════════════════════════════════════════════════
    
    def add_favorite(self, user_id: int, track: Track) -> bool:
        """Add track to user's favorites"""
        if user_id not in self.favorites:
            self.favorites[user_id] = []
        
        if track not in self.favorites[user_id]:
            self.favorites[user_id].append(track)
            return True
        return False
    
    def remove_favorite(self, user_id: int, track: Track) -> bool:
        """Remove track from user's favorites"""
        if user_id in self.favorites and track in self.favorites[user_id]:
            self.favorites[user_id].remove(track)
            return True
        return False
    
    def get_favorites(self, user_id: int) -> List[Track]:
        """Get user's favorites"""
        return self.favorites.get(user_id, [])
