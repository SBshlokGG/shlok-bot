"""
🎵 Shlok Music Bot - Premium Music Experience
Advanced Discord Music Bot with Beautiful UI
"""

import asyncio
import logging
from typing import Optional
import random
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands, tasks
import yt_dlp

import config

logger = logging.getLogger('ShlokMusic')

# ═══════════════════════════════════════════════════════════════
# 🎵 AUDIO SETTINGS - HIGH QUALITY
# ═══════════════════════════════════════════════════════════════

YTDL_OPTIONS = {
    'format': 'bestaudio[acodec=opus]/bestaudio[acodec=aac]/bestaudio/best',
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'ytsearch',
    'source_address': '0.0.0.0',
    'extract_flat': False,
    'cachedir': False,
    'geo_bypass': True,
    'socket_timeout': 60,
    'retries': 10,
    'fragment_retries': 10,
    'skip_unavailable_fragments': True,
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Cache-Control': 'max-age=0',
    },
    'extractor_args': {
        'youtube': {
            'player_client': ['android', 'web', 'mweb'],
            'player_skip': ['js', 'configs'],
            'skip_webpage': False,
        }
    },
    'youtube_include_dash_manifest': False,
    'writesubtitles': False,
    'writeautomaticsub': False,
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 10 -nostdin',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)


# ═══════════════════════════════════════════════════════════════
# 🎵 SONG CLASS
# ═══════════════════════════════════════════════════════════════

class Song:
    def __init__(self, data: dict, requester: discord.Member):
        self.data = data
        self.requester = requester
        self.title = data.get('title', 'Unknown')
        self.url = data.get('webpage_url', data.get('url', ''))
        self.duration = data.get('duration', 0)
        self.thumbnail = data.get('thumbnail', '')
        self.artist = data.get('uploader', data.get('artist', 'Unknown'))
        self.stream_url = self._get_stream_url(data)
    
    def _get_stream_url(self, data: dict) -> str:
        if data.get('url') and 'manifest' not in data.get('url', ''):
            return data['url']
        
        formats = data.get('formats', [])
        if not formats:
            return data.get('url', '')
        
        audio_formats = [f for f in formats if f.get('acodec') != 'none']
        
        if not audio_formats:
            return formats[-1].get('url', '') if formats else ''
        
        def score_format(f):
            codec = f.get('acodec', '')
            abr = f.get('abr', 0) or f.get('tbr', 0) or 0
            codec_score = 100 if 'opus' in codec else (80 if 'aac' in codec else 50)
            vcodec = f.get('vcodec', 'none')
            video_penalty = 0 if vcodec in ('none', None) else -20
            return codec_score + abr + video_penalty
        
        audio_formats.sort(key=score_format, reverse=True)
        return audio_formats[0].get('url', '')
    
    @property
    def duration_str(self) -> str:
        if not self.duration:
            return "🔴 LIVE"
        m, s = divmod(int(self.duration), 60)
        h, m = divmod(m, 60)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
    
    def create_source(self) -> Optional[discord.FFmpegPCMAudio]:
        if not self.stream_url:
            return None
        try:
            return discord.FFmpegPCMAudio(self.stream_url, **FFMPEG_OPTIONS)
        except Exception as e:
            logger.error(f"FFmpeg error: {e}")
            return None
    
    @classmethod
    async def from_query(cls, query: str, requester: discord.Member, loop=None) -> Optional['Song']:
        loop = loop or asyncio.get_event_loop()
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                if not query.startswith('http'):
                    query = f"ytsearch:{query}"
                
                data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=False))
                
                if not data:
                    logger.warning(f"No data returned for query: {query}")
                    return None
                
                if 'entries' in data:
                    if not data.get('entries'):
                        logger.warning(f"No entries found for query: {query}")
                        return None
                    data = data['entries'][0]
                
                if not data:
                    logger.warning(f"Data is None for query: {query}")
                    return None
                
                return cls(data, requester)
            except Exception as e:
                error_msg = str(e)
                # Check if it's a bot detection error
                is_bot_detection = 'bot' in error_msg.lower() or 'sign in' in error_msg.lower()
                
                if is_bot_detection and attempt < max_retries - 1:
                    logger.warning(f"YouTube bot detection (attempt {attempt + 1}/{max_retries}), retrying in {retry_delay}s...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 1.5  # Exponential backoff
                    continue
                else:
                    if is_bot_detection:
                        logger.error(f"❌ YouTube is blocking requests after {max_retries} retries. This is a YouTube anti-bot measure.")
                    else:
                        logger.error(f"Extract error for query '{query}': {error_msg[:100]}")
                    return None
        
        return None


# ═══════════════════════════════════════════════════════════════
# 🎵 MUSIC PLAYER CLASS
# ═══════════════════════════════════════════════════════════════

class MusicPlayer:
    def __init__(self, ctx: commands.Context):
        self.bot = ctx.bot
        self.guild = ctx.guild
        self.channel = ctx.channel
        self.voice: Optional[discord.VoiceClient] = ctx.voice_client
        self.queue: list[Song] = []
        self.current: Optional[Song] = None
        self.volume = 0.5
        self.loop = False
        self.now_playing_msg: Optional[discord.Message] = None
    
    def _create_progress_bar(self, current: int, total: int, length: int = 12) -> str:
        """Create a visual progress bar"""
        if total == 0:
            return "🔴 LIVE"
        filled = int(length * current / total)
        bar = "▰" * filled + "▱" * (length - filled)
        return f"`{bar}`"
    
    def _get_volume_emoji(self) -> str:
        """Get volume emoji based on level"""
        if self.volume == 0:
            return "🔇"
        elif self.volume < 0.3:
            return "🔈"
        elif self.volume < 0.7:
            return "🔉"
        else:
            return "🔊"
    
    async def send_action_message(self, action: str, emoji: str = "✅"):
        """Send a temporary action feedback message"""
        embed = discord.Embed(
            description=f"{emoji} **{action}**",
            color=0x2ECC71
        )
        msg = await self.channel.send(embed=embed)
        await asyncio.sleep(5)
        try:
            await msg.delete()
        except:
            pass
    
    async def play_song(self, song: Song):
        """Play a specific song"""
        self.voice = self.guild.voice_client
        
        if not self.voice or not self.voice.is_connected():
            logger.error("Not connected to voice")
            return
        
        if self.voice.is_playing():
            self.voice.stop()
            await asyncio.sleep(0.5)
        
        self.current = song
        
        try:
            source = song.create_source()
            if not source:
                logger.error(f"No source for: {song.title}")
                await self.play_next()
                return
            
            source = discord.PCMVolumeTransformer(source, volume=self.volume)
            
            def after(error):
                if error:
                    logger.error(f"Playback error: {error}")
                asyncio.run_coroutine_threadsafe(self.play_next(), self.bot.loop)
            
            self.voice.play(source, after=after)
            await self.send_now_playing()
            
        except Exception as e:
            logger.error(f"Play error: {e}")
            await self.play_next()
    
    async def play_next(self):
        """Play next song from queue"""
        await asyncio.sleep(0.3)
        
        self.voice = self.guild.voice_client
        
        if not self.voice or not self.voice.is_connected():
            return
        
        if self.loop and self.current:
            fresh = await Song.from_query(self.current.url, self.current.requester, self.bot.loop)
            if fresh:
                await self.play_song(fresh)
            else:
                await self.play_song(self.current)
            return
        
        if self.queue:
            song = self.queue.pop(0)
            await self.play_song(song)
        else:
            self.current = None
            if self.channel:
                embed = discord.Embed(
                    title="",
                    description="```\n🎵 Queue finished! Add more songs with s!play\n```",
                    color=0x3498DB
                )
                await self.channel.send(embed=embed, delete_after=30)
    
    async def send_now_playing(self):
        """Send beautiful now playing embed"""
        if not self.current:
            return
        
        song = self.current
        vol_emoji = self._get_volume_emoji()
        vol_bar = "█" * int(self.volume * 10) + "░" * (10 - int(self.volume * 10))
        
        # Create beautiful embed
        embed = discord.Embed(color=0x9B59B6)
        
        # Title with animated emoji effect
        embed.title = "▶️ Now Playing"
        
        # Song info in a clean format
        embed.description = f"### 🎵 [{song.title}]({song.url})\n"
        embed.description += f"```yaml\n"
        embed.description += f"Artist   : {song.artist[:30]}\n"
        embed.description += f"Duration : {song.duration_str}\n"
        embed.description += f"Volume   : {vol_emoji} {int(self.volume*100)}% [{vol_bar}]\n"
        if self.loop:
            embed.description += f"Loop     : 🔁 Enabled\n"
        embed.description += f"```"
        
        # Queue info
        if self.queue:
            next_songs = "\n".join([f"` {i+1} ` {s.title[:35]}..." if len(s.title) > 35 else f"` {i+1} ` {s.title}" for i, s in enumerate(self.queue[:3])])
            if len(self.queue) > 3:
                next_songs += f"\n` + ` *{len(self.queue) - 3} more in queue*"
            embed.add_field(name="📋 Up Next", value=next_songs, inline=False)
        
        # Thumbnail
        if song.thumbnail:
            embed.set_thumbnail(url=song.thumbnail)
        
        # Footer with controls hint
        embed.set_footer(
            text=f"🎧 Requested by {song.requester.display_name} • React to control",
            icon_url=song.requester.display_avatar.url
        )
        
        embed.timestamp = datetime.now()
        
        # Delete old message
        if self.now_playing_msg:
            try:
                await self.now_playing_msg.delete()
            except:
                pass
        
        self.now_playing_msg = await self.channel.send(embed=embed)
        
        # Add reactions: Play/Pause, Skip, Stop, Vol Down, Vol Up
        reactions = ['⏯️', '⏭️', '⏹️', '🔉', '🔊']
        for emoji in reactions:
            try:
                await self.now_playing_msg.add_reaction(emoji)
                await asyncio.sleep(0.25)
            except:
                pass
    
    async def update_now_playing(self):
        """Update the now playing embed"""
        if not self.current or not self.now_playing_msg:
            return
        
        song = self.current
        vol_emoji = self._get_volume_emoji()
        vol_bar = "█" * int(self.volume * 10) + "░" * (10 - int(self.volume * 10))
        
        embed = discord.Embed(color=0x9B59B6)
        embed.title = "▶️ Now Playing"
        
        embed.description = f"### 🎵 [{song.title}]({song.url})\n"
        embed.description += f"```yaml\n"
        embed.description += f"Artist   : {song.artist[:30]}\n"
        embed.description += f"Duration : {song.duration_str}\n"
        embed.description += f"Volume   : {vol_emoji} {int(self.volume*100)}% [{vol_bar}]\n"
        if self.loop:
            embed.description += f"Loop     : 🔁 Enabled\n"
        embed.description += f"```"
        
        if self.queue:
            next_songs = "\n".join([f"` {i+1} ` {s.title[:35]}..." if len(s.title) > 35 else f"` {i+1} ` {s.title}" for i, s in enumerate(self.queue[:3])])
            if len(self.queue) > 3:
                next_songs += f"\n` + ` *{len(self.queue) - 3} more in queue*"
            embed.add_field(name="📋 Up Next", value=next_songs, inline=False)
        
        if song.thumbnail:
            embed.set_thumbnail(url=song.thumbnail)
        
        embed.set_footer(
            text=f"🎧 Requested by {song.requester.display_name} • React to control",
            icon_url=song.requester.display_avatar.url
        )
        embed.timestamp = datetime.now()
        
        try:
            await self.now_playing_msg.edit(embed=embed)
        except:
            pass
    
    def stop(self):
        self.queue.clear()
        self.current = None
        self.loop = False
        if self.voice and self.voice.is_playing():
            self.voice.stop()


# ═══════════════════════════════════════════════════════════════
# 🎵 MUSIC COG
# ═══════════════════════════════════════════════════════════════

class MusicSimple(commands.Cog, name="Music"):
    """🎵 Premium music experience"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players: dict[int, MusicPlayer] = {}
        self.command_cooldowns = {}  # Track command invocations to prevent duplicates
        self.voice_check.start()
    
    def cog_unload(self):
        self.voice_check.cancel()
    
    @tasks.loop(seconds=120)
    async def voice_check(self):
        """Keep voice connections alive"""
        for guild_id in list(self.players.keys()):
            try:
                player = self.players[guild_id]
                if player.voice and player.voice.is_connected():
                    channel = player.voice.channel
                    if channel and len([m for m in channel.members if not m.bot]) == 0:
                        if not config.MUSIC.stay_connected_24_7:
                            await player.voice.disconnect()
                            del self.players[guild_id]
            except:
                pass
    
    @voice_check.before_loop
    async def before_voice_check(self):
        await self.bot.wait_until_ready()
    
    def get_player(self, ctx: commands.Context) -> MusicPlayer:
        if ctx.guild.id not in self.players:
            self.players[ctx.guild.id] = MusicPlayer(ctx)
        else:
            self.players[ctx.guild.id].voice = ctx.voice_client
            self.players[ctx.guild.id].channel = ctx.channel
        return self.players[ctx.guild.id]
    
    def _check_duplicate_invoke(self, ctx: commands.Context) -> bool:
        """Prevent hybrid command from invoking twice (slash + prefix)"""
        import time
        cmd_key = f"{ctx.guild.id}_{ctx.author.id}_{ctx.command.name}"
        current_time = time.time()
        
        if cmd_key in self.command_cooldowns:
            last_invoke = self.command_cooldowns[cmd_key]
            # If invoked within 0.5 seconds, it's a duplicate
            if current_time - last_invoke < 0.5:
                return True
        
        self.command_cooldowns[cmd_key] = current_time
        # Clean old entries
        if len(self.command_cooldowns) > 100:
            oldest_key = min(self.command_cooldowns, key=self.command_cooldowns.get)
            del self.command_cooldowns[oldest_key]
        return False
    
    async def ensure_voice(self, ctx: commands.Context) -> bool:
        if not ctx.author.voice:
            embed = discord.Embed(description="❌ **Join a voice channel first!**", color=0xE74C3C)
            await ctx.send(embed=embed, delete_after=5)
            return False
        
        channel = ctx.author.voice.channel
        perms = channel.permissions_for(ctx.guild.me)
        
        if not perms.connect or not perms.speak:
            embed = discord.Embed(description="❌ **I need Connect and Speak permissions!**", color=0xE74C3C)
            await ctx.send(embed=embed, delete_after=5)
            return False
        
        if not ctx.voice_client:
            try:
                await channel.connect(timeout=30.0, reconnect=True, self_deaf=True)
            except Exception as e:
                logger.error(f"Connect error: {e}")
                embed = discord.Embed(description="❌ **Could not connect to voice!**", color=0xE74C3C)
                await ctx.send(embed=embed, delete_after=5)
                return False
        elif ctx.voice_client.channel != channel:
            try:
                await ctx.voice_client.move_to(channel)
            except:
                pass
        
        return True
    
    # ═══════════════════════════════════════════════════════════════
    # 🎵 COMMANDS
    # ═══════════════════════════════════════════════════════════════
    
    @app_commands.command(name="play", description="🎵 Play a song")
    @app_commands.describe(query="Song name or YouTube URL")
    async def play(self, interaction: discord.Interaction, *, query: str):
        # Acknowledge the interaction immediately to avoid timeout
        await interaction.response.defer()
        
        ctx = await commands.Context.from_interaction(interaction)
        if self._check_duplicate_invoke(ctx):
            return
        
        # Check voice channel
        if not ctx.author.voice or not ctx.author.voice.channel:
            await interaction.followup.send("❌ You must be in a voice channel!", ephemeral=True)
            return
        
        # Connect to voice if not already connected
        if not ctx.voice_client:
            try:
                await ctx.author.voice.channel.connect(timeout=30.0, reconnect=True, self_deaf=True)
            except Exception as e:
                logger.error(f"Connect error: {e}")
                await interaction.followup.send(f"❌ Could not connect to voice: {str(e)[:50]}", ephemeral=True)
                return
        
        player = self.get_player(ctx)
        
        # Send initial search message
        search_embed = discord.Embed(
            description=f"🔍 **Searching:** `{query}`",
            color=0x3498DB
        )
        await interaction.followup.send(embed=search_embed)
        
        try:
            song = await Song.from_query(query, ctx.author, self.bot.loop)
            
            if not song:
                error_embed = discord.Embed(description="❌ **No results found!**", color=0xE74C3C)
                return await interaction.followup.send(embed=error_embed)
            
            if not song.stream_url:
                error_embed = discord.Embed(description="❌ **Could not get audio stream!**", color=0xE74C3C)
                return await interaction.followup.send(embed=error_embed)
            
            vc = ctx.voice_client
            
            if vc and (vc.is_playing() or vc.is_paused()):
                player.queue.append(song)
                queue_embed = discord.Embed(color=0x2ECC71)
                queue_embed.description = f"✅ **Added to Queue** • Position #{len(player.queue)}\n\n"
                queue_embed.description += f"🎵 **[{song.title}]({song.url})**\n"
                queue_embed.description += f"```yaml\nDuration: {song.duration_str}\n```"
                if song.thumbnail:
                    queue_embed.set_thumbnail(url=song.thumbnail)
                await interaction.followup.send(embed=queue_embed)
            else:
                await player.play_song(song)
                
        except Exception as e:
            logger.error(f"Play error: {e}", exc_info=True)
            error_embed = discord.Embed(description=f"❌ **Error:** {str(e)[:100]}", color=0xE74C3C)
            await interaction.followup.send(embed=error_embed)
    
    @app_commands.command(name="pause", description="⏸️ Pause playback")
    async def pause(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        if self._check_duplicate_invoke(ctx):
            return
        vc = ctx.voice_client
        if not vc or not vc.is_playing():
            embed = discord.Embed(description="❌ **Nothing is playing!**", color=0xE74C3C)
            return await ctx.send(embed=embed, delete_after=5)
        vc.pause()
        embed = discord.Embed(description="⏸️ **Paused playback**", color=0xF39C12)
        await ctx.send(embed=embed, delete_after=5)
    
    @app_commands.command(name="resume", description="▶️ Resume playback")
    async def resume(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        if self._check_duplicate_invoke(ctx):
            return
        vc = ctx.voice_client
        if not vc or not vc.is_paused():
            embed = discord.Embed(description="❌ **Not paused!**", color=0xE74C3C)
            return await ctx.send(embed=embed, delete_after=5)
        vc.resume()
        embed = discord.Embed(description="▶️ **Resumed playback**", color=0x2ECC71)
        await ctx.send(embed=embed, delete_after=5)
    
    @app_commands.command(name="skip", description="⏭️ Skip song")
    async def skip(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        if self._check_duplicate_invoke(ctx):
            return
        vc = ctx.voice_client
        if not vc or not (vc.is_playing() or vc.is_paused()):
            embed = discord.Embed(description="❌ **Nothing to skip!**", color=0xE74C3C)
            return await ctx.send(embed=embed, delete_after=5)
        player = self.get_player(ctx)
        player.loop = False
        vc.stop()
        embed = discord.Embed(description="⏭️ **Skipped to next song**", color=0x3498DB)
        await ctx.send(embed=embed, delete_after=5)
    
    @app_commands.command(name="stop", description="⏹️ Stop and clear queue")
    async def stop(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        if self._check_duplicate_invoke(ctx):
            return
        vc = ctx.voice_client
        if not vc:
            embed = discord.Embed(description="❌ **Not connected!**", color=0xE74C3C)
            return await ctx.send(embed=embed, delete_after=5)
        self.get_player(ctx).stop()
        embed = discord.Embed(description="⏹️ **Stopped playback and cleared queue**", color=0xE74C3C)
        await ctx.send(embed=embed, delete_after=5)
    
    @app_commands.command(name="queue", description="📋 Show queue")
    async def queue(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        if self._check_duplicate_invoke(ctx):
            return
        player = self.get_player(ctx)
        
        embed = discord.Embed(title="📋 Music Queue", color=0x9B59B6)
        
        if player.current:
            status = "🔁 " if player.loop else "▶️ "
            embed.add_field(
                name=f"{status} Now Playing",
                value=f"**{player.current.title}**\n`{player.current.duration_str}`",
                inline=False
            )
        
        if player.queue:
            queue_list = []
            total_duration = 0
            for i, song in enumerate(player.queue[:10], 1):
                queue_list.append(f"` {i} ` **{song.title[:40]}** `{song.duration_str}`")
                if song.duration:
                    total_duration += song.duration
            
            if len(player.queue) > 10:
                queue_list.append(f"\n*... and {len(player.queue) - 10} more songs*")
            
            embed.add_field(name="📋 Up Next", value="\n".join(queue_list), inline=False)
            
            if total_duration:
                m, s = divmod(total_duration, 60)
                h, m = divmod(m, 60)
                duration_str = f"{h}h {m}m" if h else f"{m}m"
                embed.set_footer(text=f"📊 {len(player.queue)} songs • Total: {duration_str}")
        else:
            embed.add_field(name="📋 Up Next", value="*Queue is empty*", inline=False)
        
        await ctx.send(embed=embed)
    
    @app_commands.command(name="volume", description="🔊 Set volume")
    @app_commands.describe(level="Volume level (0-100)")
    async def volume(self, interaction: discord.Interaction, level: int = None):
        ctx = await commands.Context.from_interaction(interaction)
        if self._check_duplicate_invoke(ctx):
            return
        player = self.get_player(ctx)
        
        if level is None:
            vol_bar = "█" * int(player.volume * 10) + "░" * (10 - int(player.volume * 10))
            embed = discord.Embed(
                description=f"🔊 **Volume:** `{int(player.volume*100)}%`\n`[{vol_bar}]`",
                color=0x9B59B6
            )
            return await ctx.send(embed=embed, delete_after=10)
        
        level = max(0, min(100, level))
        player.volume = level / 100
        
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = player.volume
        
        vol_bar = "█" * int(player.volume * 10) + "░" * (10 - int(player.volume * 10))
        embed = discord.Embed(
            description=f"🔊 **Volume set to** `{level}%`\n`[{vol_bar}]`",
            color=0x2ECC71
        )
        await ctx.send(embed=embed, delete_after=5)
        await player.update_now_playing()
    
    @app_commands.command(name="volumeup", description="🔊 Volume +10%")
    async def volumeup(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        if self._check_duplicate_invoke(ctx):
            return
        player = self.get_player(ctx)
        old_vol = int(player.volume * 100)
        player.volume = min(1.0, player.volume + 0.1)
        new_vol = int(player.volume * 100)
        
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = player.volume
        
        vol_bar = "█" * int(player.volume * 10) + "░" * (10 - int(player.volume * 10))
        embed = discord.Embed(
            description=f"🔊 **Volume:** `{old_vol}%` → `{new_vol}%`\n`[{vol_bar}]`",
            color=0x2ECC71
        )
        await ctx.send(embed=embed, delete_after=5)
        await player.update_now_playing()
    
    @app_commands.command(name="volumedown", description="🔉 Volume -10%")
    async def volumedown(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        if self._check_duplicate_invoke(ctx):
            return
        player = self.get_player(ctx)
        old_vol = int(player.volume * 100)
        player.volume = max(0.0, player.volume - 0.1)
        new_vol = int(player.volume * 100)
        
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = player.volume
        
        vol_bar = "█" * int(player.volume * 10) + "░" * (10 - int(player.volume * 10))
        embed = discord.Embed(
            description=f"🔉 **Volume:** `{old_vol}%` → `{new_vol}%`\n`[{vol_bar}]`",
            color=0xF39C12
        )
        await ctx.send(embed=embed, delete_after=5)
        await player.update_now_playing()
    
    @app_commands.command(name="loop", description="🔁 Toggle loop")
    async def loop(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        if self._check_duplicate_invoke(ctx):
            return
        player = self.get_player(ctx)
        player.loop = not player.loop
        if player.loop:
            embed = discord.Embed(description="🔁 **Loop enabled** - Current song will repeat", color=0x2ECC71)
        else:
            embed = discord.Embed(description="➡️ **Loop disabled** - Queue will continue normally", color=0x3498DB)
        await ctx.send(embed=embed, delete_after=5)
        await player.update_now_playing()
    
    @app_commands.command(name="shuffle", description="🔀 Shuffle queue")
    async def shuffle(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        if self._check_duplicate_invoke(ctx):
            return
        player = self.get_player(ctx)
        if len(player.queue) < 2:
            embed = discord.Embed(description="❌ **Need 2+ songs to shuffle!**", color=0xE74C3C)
            return await ctx.send(embed=embed, delete_after=5)
        random.shuffle(player.queue)
        embed = discord.Embed(description=f"🔀 **Shuffled {len(player.queue)} songs!**", color=0x2ECC71)
        await ctx.send(embed=embed, delete_after=5)
    
    @app_commands.command(name="np", description="🎵 Now playing")
    async def np(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        if self._check_duplicate_invoke(ctx):
            return
        player = self.get_player(ctx)
        if not player.current:
            embed = discord.Embed(description="❌ **Nothing playing!**", color=0xE74C3C)
            return await ctx.send(embed=embed, delete_after=5)
        await player.send_now_playing()
    
    @app_commands.command(name="clear", description="🗑️ Clear queue")
    async def clear(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        if self._check_duplicate_invoke(ctx):
            return
        player = self.get_player(ctx)
        count = len(player.queue)
        player.queue.clear()
        embed = discord.Embed(description=f"🗑️ **Cleared {count} songs from queue!**", color=0xF39C12)
        await ctx.send(embed=embed, delete_after=5)
    
    @app_commands.command(name="remove", description="🗑️ Remove song from queue")
    @app_commands.describe(position="Position in queue (1, 2, 3...)")
    async def remove(self, interaction: discord.Interaction, position: int):
        ctx = await commands.Context.from_interaction(interaction)
        if self._check_duplicate_invoke(ctx):
            return
        player = self.get_player(ctx)
        if position < 1 or position > len(player.queue):
            embed = discord.Embed(description=f"❌ **Invalid position!** Queue has {len(player.queue)} songs.", color=0xE74C3C)
            return await ctx.send(embed=embed, delete_after=5)
        
        removed = player.queue.pop(position - 1)
        embed = discord.Embed(description=f"🗑️ **Removed:** {removed.title}", color=0xF39C12)
        await ctx.send(embed=embed, delete_after=5)
    
    @app_commands.command(name="leave", description="👋 Leave voice")
    async def leave(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        if self._check_duplicate_invoke(ctx):
            return
        if not ctx.voice_client:
            embed = discord.Embed(description="❌ **Not connected!**", color=0xE74C3C)
            return await ctx.send(embed=embed, delete_after=5)
        
        if ctx.guild.id in self.players:
            self.players[ctx.guild.id].stop()
            del self.players[ctx.guild.id]
        
        await ctx.voice_client.disconnect()
        embed = discord.Embed(description="👋 **Disconnected from voice!**", color=0x3498DB)
        await ctx.send(embed=embed, delete_after=5)
    
    @app_commands.command(name="join", description="🔗 Join voice channel")
    async def join(self, interaction: discord.Interaction):
        ctx = await commands.Context.from_interaction(interaction)
        if self._check_duplicate_invoke(ctx):
            return
        if not ctx.author.voice:
            embed = discord.Embed(description="❌ **Join a voice channel first!**", color=0xE74C3C)
            return await ctx.send(embed=embed, delete_after=5)
        
        channel = ctx.author.voice.channel
        
        if ctx.voice_client:
            await ctx.voice_client.move_to(channel)
        else:
            await channel.connect(timeout=30.0, reconnect=True, self_deaf=True)
        
        embed = discord.Embed(description=f"🔗 **Connected to** `{channel.name}`", color=0x2ECC71)
        await ctx.send(embed=embed, delete_after=5)
    
    # ═══════════════════════════════════════════════════════════════
    # 🎮 REACTION CONTROLS
    # ═══════════════════════════════════════════════════════════════
    
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        if user.bot or not reaction.message.guild:
            return
        
        player = self.players.get(reaction.message.guild.id)
        if not player or not player.now_playing_msg:
            return
        
        if reaction.message.id != player.now_playing_msg.id:
            return
        
        vc = reaction.message.guild.voice_client
        if not vc:
            return
        
        # Remove user's reaction
        try:
            await reaction.remove(user)
        except:
            pass
        
        emoji = str(reaction.emoji)
        action_msg = None
        
        # Handle controls with feedback messages
        if emoji == '⏯️':
            if vc.is_paused():
                vc.resume()
                action_msg = "▶️ **Resumed playback**"
            elif vc.is_playing():
                vc.pause()
                action_msg = "⏸️ **Paused playback**"
                
        elif emoji == '⏭️':
            player.loop = False
            vc.stop()
            action_msg = "⏭️ **Skipped to next song**"
            
        elif emoji == '⏹️':
            player.stop()
            action_msg = "⏹️ **Stopped playback**"
            
        elif emoji == '🔀':
            if len(player.queue) >= 2:
                random.shuffle(player.queue)
                action_msg = f"🔀 **Shuffled {len(player.queue)} songs**"
                await player.update_now_playing()
                
        elif emoji == '🔁':
            player.loop = not player.loop
            if player.loop:
                action_msg = "🔁 **Loop enabled**"
            else:
                action_msg = "➡️ **Loop disabled**"
            await player.update_now_playing()
            
        elif emoji == '🔉':
            old_vol = int(player.volume * 100)
            player.volume = max(0.0, player.volume - 0.1)
            new_vol = int(player.volume * 100)
            if vc.source:
                vc.source.volume = player.volume
            action_msg = f"🔉 **Volume:** `{old_vol}%` → `{new_vol}%`"
            await player.update_now_playing()
            
        elif emoji == '🔊':
            old_vol = int(player.volume * 100)
            player.volume = min(1.0, player.volume + 0.1)
            new_vol = int(player.volume * 100)
            if vc.source:
                vc.source.volume = player.volume
            action_msg = f"🔊 **Volume:** `{old_vol}%` → `{new_vol}%`"
            await player.update_now_playing()
        
        # Send feedback message
        if action_msg:
            embed = discord.Embed(description=action_msg, color=0x2ECC71)
            msg = await player.channel.send(embed=embed)
            await asyncio.sleep(5)
            try:
                await msg.delete()
            except:
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicSimple(bot))
    logger.info("✅ Music cog loaded")
