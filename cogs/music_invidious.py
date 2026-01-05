"""
🎵 Shlok Music Bot - Invidious Edition
Uses Invidious API (privacy YouTube proxy) to avoid YouTube bot detection
"""

import asyncio
import logging
from typing import Optional
import aiohttp

import discord
from discord import app_commands
from discord.ext import commands, tasks
import yt_dlp

import config

logger = logging.getLogger('ShlokMusic')

# ═══════════════════════════════════════════════════════════════
# 🎵 INVIDIOUS INSTANCES (public proxies that don't block bots)
# ═══════════════════════════════════════════════════════════════

INVIDIOUS_INSTANCES = [
    'https://invidious.io',
    'https://inv.vern.cc',
    'https://iv.ggtyler.dev',
    'https://invidious.fdn.fr',
    'https://vid.puffyan.us',
]

# ═══════════════════════════════════════════════════════════════
# 🎵 AUDIO EXTRACTION - SIMPLIFIED
# ═══════════════════════════════════════════════════════════════

YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': True,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'extract_flat': False,
    'socket_timeout': 30,
    'retries': 3,
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

# ═══════════════════════════════════════════════════════════════
# 🎵 SONG CLASS
# ═══════════════════════════════════════════════════════════════

class Song:
    def __init__(self, title: str, url: str, requester: discord.Member, duration: int = 0, thumbnail: str = '', video_id: str = ''):
        self.title = title
        self.url = url
        self.video_id = video_id
        self.requester = requester
        self.duration = duration
        self.thumbnail = thumbnail
        self.stream_url = None
    
    @property
    def duration_str(self) -> str:
        if not self.duration:
            return "🔴 LIVE"
        m, s = divmod(int(self.duration), 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
    
    async def extract_stream(self, instance: str = 'https://invidious.io'):
        """Extract stream URL from Invidious (not YouTube!)"""
        if self.stream_url:
            return self.stream_url
        
        try:
            # Use Invidious API to get video data directly
            async with aiohttp.ClientSession() as session:
                url = f"{instance}/api/v1/videos/{self.video_id}"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        # Get best audio format from Invidious
                        formats = data.get('formatStreams', [])
                        if formats:
                            # Find best audio-only format
                            audio_formats = [f for f in formats if f.get('type', '').startswith('audio')]
                            if audio_formats:
                                # Use first audio format (Invidious provides direct stream URLs)
                                self.stream_url = audio_formats[0].get('url', '')
                                if self.stream_url:
                                    logger.info(f"✅ Extracted stream from Invidious for: {self.title}")
                                    return self.stream_url
        except Exception as e:
            logger.debug(f"Invidious stream extraction failed: {str(e)[:100]}")
        
        return None
    
    def create_source(self) -> Optional[discord.FFmpegPCMAudio]:
        if not self.stream_url:
            return None
        try:
            return discord.FFmpegPCMAudio(self.stream_url, **FFMPEG_OPTIONS)
        except Exception as e:
            logger.error(f"FFmpeg error: {e}")
            return None

# ═══════════════════════════════════════════════════════════════
# 🔍 MUSIC SEARCH (INVIDIOUS API - NO BOT DETECTION)
# ═══════════════════════════════════════════════════════════════

async def search_invidious(query: str, limit: int = 5) -> list[dict]:
    """
    Search videos using Invidious API (no bot detection)
    
    Args:
        query: Search query
        limit: Number of results
        
    Returns:
        List of video data
    """
    async with aiohttp.ClientSession() as session:
        for instance in INVIDIOUS_INSTANCES:
            try:
                url = f"{instance}/api/v1/search?q={query}&type=video"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data[:limit] if data else []
            except Exception as e:
                logger.debug(f"Invidious instance {instance} failed: {str(e)[:50]}")
                continue
    
    return []

async def search_music(query: str, requester: discord.Member, limit: int = 1) -> tuple[list[Song], str]:
    """
    Search for music using Invidious (primary) or YouTube fallback
    
    Returns:
        Tuple of (songs_list, instance_used)
    """
    instance_used = None
    
    # Try Invidious first (no bot detection)
    logger.info(f"🔍 Searching Invidious for: {query}")
    for instance in INVIDIOUS_INSTANCES:
        try:
            async with aiohttp.ClientSession() as session:
                url = f"{instance}/api/v1/search?q={query}&type=video"
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    if resp.status == 200:
                        results = await resp.json()
                        
                        if results:
                            instance_used = instance
                            songs = []
                            for result in results[:limit]:
                                try:
                                    title = result.get('title', 'Unknown')
                                    video_id = result.get('videoId', '')
                                    duration = result.get('lengthSeconds', 0)
                                    thumbnail = result.get('thumbnail', '')
                                    
                                    if video_id:
                                        url = f"https://www.youtube.com/watch?v={video_id}"
                                        song = Song(title, url, requester, int(duration) if duration else 0, thumbnail, video_id)
                                        songs.append(song)
                                except:
                                    continue
                            
                            if songs:
                                logger.info(f"✅ Found {len(songs)} song(s) on Invidious ({instance})")
                                return songs, instance_used
        except Exception as e:
            logger.debug(f"Invidious instance {instance} failed: {str(e)[:50]}")
            continue
    
    logger.warning(f"❌ All Invidious instances failed for: {query}")
    return [], None

# ═══════════════════════════════════════════════════════════════
# 🎵 MUSIC PLAYER
# ═══════════════════════════════════════════════════════════════

class MusicPlayer:
    def __init__(self):
        self.queue = []
        self.current = None
        self.is_playing = False
        self.is_paused = False
    
    async def play_song(self, song: Song):
        """Play a song"""
        try:
            # Extract stream URL
            await song.extract_stream()
            
            if not song.stream_url:
                logger.error("❌ Could not extract stream URL")
                return False
            
            self.current = song
            self.is_playing = True
            self.is_paused = False
            return True
        except Exception as e:
            logger.error(f"Play error: {e}")
            return False
    
    async def play_next(self):
        """Play next song in queue"""
        if self.queue:
            song = self.queue.pop(0)
            return await self.play_song(song)
        self.is_playing = False
        return False

# ═══════════════════════════════════════════════════════════════
# 🎵 MUSIC COG
# ═══════════════════════════════════════════════════════════════

class MusicInvidious(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.players = {}
    
    def get_player(self, ctx) -> MusicPlayer:
        if ctx.guild.id not in self.players:
            self.players[ctx.guild.id] = MusicPlayer()
        return self.players[ctx.guild.id]
    
    @app_commands.command(name="play", description="▶️ Play a song")
    @app_commands.describe(query="Song name or URL")
    async def play(self, interaction: discord.Interaction, *, query: str):
        """Play a song"""
        await interaction.response.defer()
        
        # Check voice channel
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.followup.send("❌ You must be in a voice channel!", ephemeral=True)
        
        # Connect to voice
        channel = interaction.user.voice.channel
        try:
            vc = await channel.connect(timeout=10, reconnect=True, self_deaf=True)
        except:
            if not interaction.guild.voice_client:
                return await interaction.followup.send("❌ Could not connect to voice!", ephemeral=True)
            vc = interaction.guild.voice_client
        
        # Send searching message
        await interaction.followup.send(f"🔍 **Searching:** `{query}`...")
        
        try:
            # Search for music using Invidious
            songs, instance = await search_music(query, interaction.user, limit=1)
            
            if not songs:
                return await interaction.followup.send("❌ **No results found!**", ephemeral=True)
            
            song = songs[0]
            player = self.get_player(interaction)
            
            # Extract stream from Invidious (not YouTube!)
            await song.extract_stream(instance or INVIDIOUS_INSTANCES[0])
            
            if not song.stream_url:
                return await interaction.followup.send("❌ **Could not extract audio stream!**", ephemeral=True)
            
            # Play or queue
            if vc.is_playing() or vc.is_paused():
                player.queue.append(song)
                embed = discord.Embed(
                    title="✅ Added to Queue",
                    description=f"**{song.title}**",
                    color=0x2ECC71
                )
                embed.add_field(name="Duration", value=song.duration_str, inline=False)
                await interaction.followup.send(embed=embed)
            else:
                source = song.create_source()
                if not source:
                    return await interaction.followup.send("❌ **FFmpeg error!**", ephemeral=True)
                
                vc.play(source)
                embed = discord.Embed(
                    title="▶️ Now Playing",
                    description=f"**{song.title}**",
                    color=0x2ECC71
                )
                embed.add_field(name="Duration", value=song.duration_str, inline=False)
                if song.thumbnail:
                    embed.set_thumbnail(url=song.thumbnail)
                await interaction.followup.send(embed=embed)
        
        except Exception as e:
            logger.error(f"Play error: {e}", exc_info=True)
            await interaction.followup.send(f"❌ **Error:** {str(e)[:100]}", ephemeral=True)
    
    @app_commands.command(name="pause", description="⏸️ Pause playback")
    async def pause(self, interaction: discord.Interaction):
        """Pause the current song"""
        vc = interaction.guild.voice_client
        if not vc or not vc.is_playing():
            return await interaction.response.send_message("❌ Nothing playing!", ephemeral=True)
        
        vc.pause()
        await interaction.response.send_message("⏸️ **Paused**", ephemeral=True)
    
    @app_commands.command(name="resume", description="▶️ Resume playback")
    async def resume(self, interaction: discord.Interaction):
        """Resume the current song"""
        vc = interaction.guild.voice_client
        if not vc or not vc.is_paused():
            return await interaction.response.send_message("❌ Nothing paused!", ephemeral=True)
        
        vc.resume()
        await interaction.response.send_message("▶️ **Resumed**", ephemeral=True)
    
    @app_commands.command(name="stop", description="⏹️ Stop playback")
    async def stop(self, interaction: discord.Interaction):
        """Stop playback and disconnect"""
        vc = interaction.guild.voice_client
        if vc:
            vc.stop()
            await vc.disconnect()
        
        await interaction.response.send_message("⏹️ **Stopped**", ephemeral=True)
    
    @app_commands.command(name="queue", description="📋 Show queue")
    async def queue(self, interaction: discord.Interaction):
        """Show the current queue"""
        player = self.get_player(interaction)
        
        if not player.queue:
            return await interaction.response.send_message("📋 **Queue is empty!**", ephemeral=True)
        
        embed = discord.Embed(title="📋 Queue", color=0x3498DB)
        for i, song in enumerate(player.queue[:10], 1):
            embed.add_field(name=f"#{i}", value=f"**{song.title}** ({song.duration_str})", inline=False)
        
        await interaction.response.send_message(embed=embed)

async def setup(bot):
    await bot.add_cog(MusicInvidious(bot))
