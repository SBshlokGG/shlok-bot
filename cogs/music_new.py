"""
🎵 Professional Music Commands using Wavelink
High-quality audio streaming with Lavalink backend
"""

import asyncio
import logging
from typing import Optional, cast
from datetime import timedelta

import discord
from discord import app_commands
from discord.ext import commands

import wavelink

import config

logger = logging.getLogger('ShlokMusic.Music')

# ═══════════════════════════════════════════════════════════════
# 🎵 CUSTOM PLAYER CLASS
# ═══════════════════════════════════════════════════════════════

class ShlokPlayer(wavelink.Player):
    """Custom player with additional features"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queue: wavelink.Queue = wavelink.Queue()
        self.loop_mode: str = "off"  # off, track, queue
        self.text_channel: Optional[discord.TextChannel] = None
        self.now_playing_message: Optional[discord.Message] = None
        self.dj: Optional[discord.Member] = None
        self.history: list = []
        self.effect: str = "none"

# ═══════════════════════════════════════════════════════════════
# 🎵 MUSIC COG
# ═══════════════════════════════════════════════════════════════

class MusicNew(commands.Cog, name="Music"):
    """🎵 Professional Music Commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        
    async def cog_load(self):
        """Called when cog is loaded"""
        logger.info("✅ Music cog loaded (Wavelink)")
        
    # ═══════════════════════════════════════════════════════════
    # 🔧 HELPER METHODS
    # ═══════════════════════════════════════════════════════════
    
    def format_duration(self, milliseconds: int) -> str:
        """Format duration from milliseconds"""
        seconds = milliseconds // 1000
        hours, remainder = divmod(seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
    
    def create_progress_bar(self, position: int, duration: int, length: int = 15) -> str:
        """Create a visual progress bar"""
        if duration == 0:
            return "▱" * length
        
        progress = int((position / duration) * length)
        return "▰" * progress + "▱" * (length - progress)
    
    async def create_now_playing_embed(self, player: ShlokPlayer, track: wavelink.Playable) -> discord.Embed:
        """Create the now playing embed"""
        duration = self.format_duration(track.length)
        position = self.format_duration(player.position)
        progress = self.create_progress_bar(player.position, track.length)
        
        # Get volume emoji
        vol = player.volume
        if vol == 0:
            vol_emoji = "🔇"
        elif vol < 30:
            vol_emoji = "🔈"
        elif vol < 70:
            vol_emoji = "🔉"
        else:
            vol_emoji = "🔊"
        
        # Loop mode emoji
        loop_emoji = "➡️"
        if player.loop_mode == "track":
            loop_emoji = "🔂"
        elif player.loop_mode == "queue":
            loop_emoji = "🔁"
        
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**[{track.title}]({track.uri})**",
            color=config.BOT_COLOR
        )
        
        embed.add_field(
            name="Duration",
            value=f"`{position}` {progress} `{duration}`",
            inline=False
        )
        
        embed.add_field(name="👤 Artist", value=track.author or "Unknown", inline=True)
        embed.add_field(name=f"{vol_emoji} Volume", value=f"{vol}%", inline=True)
        embed.add_field(name=f"{loop_emoji} Loop", value=player.loop_mode.capitalize(), inline=True)
        
        if player.queue.count > 0:
            embed.add_field(name="📋 Queue", value=f"{player.queue.count} tracks", inline=True)
        
        if player.effect != "none":
            embed.add_field(name="🎛️ Effect", value=player.effect.replace("_", " ").title(), inline=True)
        
        # Try to get thumbnail
        if hasattr(track, 'artwork') and track.artwork:
            embed.set_thumbnail(url=track.artwork)
        elif hasattr(track, 'identifier'):
            # YouTube thumbnail
            embed.set_thumbnail(url=f"https://img.youtube.com/vi/{track.identifier}/maxresdefault.jpg")
        
        if player.dj:
            embed.set_footer(text=f"Requested by {player.dj.display_name}", icon_url=player.dj.display_avatar.url)
        
        return embed
    
    async def update_now_playing(self, player: ShlokPlayer):
        """Update the now playing message"""
        if not player.current or not player.text_channel:
            return
            
        try:
            embed = await self.create_now_playing_embed(player, player.current)
            
            if player.now_playing_message:
                try:
                    await player.now_playing_message.edit(embed=embed)
                except discord.NotFound:
                    player.now_playing_message = await player.text_channel.send(embed=embed)
            else:
                player.now_playing_message = await player.text_channel.send(embed=embed)
                
                # Add reaction controls
                for emoji in config.CONTROL_EMOJIS[:8]:
                    try:
                        await player.now_playing_message.add_reaction(emoji)
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"Error updating now playing: {e}")
    
    # ═══════════════════════════════════════════════════════════
    # 🎧 WAVELINK EVENTS
    # ═══════════════════════════════════════════════════════════
    
    @commands.Cog.listener()
    async def on_wavelink_node_ready(self, payload: wavelink.NodeReadyEventPayload):
        """Fired when Lavalink node is ready"""
        logger.info(f"🎧 Lavalink Node '{payload.node.identifier}' is ready!")
    
    @commands.Cog.listener()
    async def on_wavelink_track_start(self, payload: wavelink.TrackStartEventPayload):
        """Fired when a track starts"""
        player: ShlokPlayer = cast(ShlokPlayer, payload.player)
        track = payload.track
        
        logger.info(f"🎵 Started playing: {track.title}")
        
        # Send now playing message
        await self.update_now_playing(player)
    
    @commands.Cog.listener()
    async def on_wavelink_track_end(self, payload: wavelink.TrackEndEventPayload):
        """Fired when a track ends"""
        player: ShlokPlayer = cast(ShlokPlayer, payload.player)
        
        # Handle loop modes
        if player.loop_mode == "track" and payload.track:
            await player.play(payload.track)
            return
        
        # Add to history
        if payload.track:
            player.history.append(payload.track)
            if len(player.history) > 50:
                player.history.pop(0)
        
        # Play next track
        if not player.queue.is_empty:
            next_track = player.queue.get()
            
            # Loop queue - add current track back
            if player.loop_mode == "queue" and payload.track:
                player.queue.put(payload.track)
            
            await player.play(next_track)
        else:
            # Queue empty
            if player.text_channel:
                embed = discord.Embed(
                    title="📋 Queue Finished",
                    description="The queue is empty! Add more songs with `/play`",
                    color=config.BOT_COLOR_INFO
                )
                await player.text_channel.send(embed=embed, delete_after=30)
    
    @commands.Cog.listener()
    async def on_wavelink_inactive_player(self, player: wavelink.Player):
        """Fired when player becomes inactive"""
        if not config.MUSIC.stay_connected_24_7:
            await player.disconnect()
            if hasattr(player, 'text_channel') and player.text_channel:
                embed = discord.Embed(
                    title="👋 Disconnected",
                    description="Left due to inactivity",
                    color=config.BOT_COLOR_WARNING
                )
                await player.text_channel.send(embed=embed, delete_after=30)
    
    # ═══════════════════════════════════════════════════════════
    # ▶️ PLAY COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(name="play", aliases=["p"], description="Play a song or add it to queue")
    @app_commands.describe(query="Song name or URL (YouTube, Spotify, SoundCloud)")
    async def play(self, ctx: commands.Context, *, query: str):
        """Play a song from YouTube, Spotify, or SoundCloud"""
        
        # Check if user is in voice channel
        if not ctx.author.voice:
            embed = discord.Embed(
                title="❌ Not Connected",
                description="You need to be in a voice channel!",
                color=config.BOT_COLOR_ERROR
            )
            return await ctx.send(embed=embed, delete_after=10)
        
        channel = ctx.author.voice.channel
        
        # Get or create player
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if not player:
            try:
                player = await channel.connect(cls=ShlokPlayer, self_deaf=True)
                player.text_channel = ctx.channel
            except Exception as e:
                logger.error(f"Failed to connect: {e}")
                embed = discord.Embed(
                    title="❌ Connection Failed",
                    description=f"Could not connect to voice channel.\nError: {str(e)[:100]}",
                    color=config.BOT_COLOR_ERROR
                )
                return await ctx.send(embed=embed)
        
        # Move to user's channel if in different channel
        if player.channel != channel:
            await player.move_to(channel)
        
        player.text_channel = ctx.channel
        player.dj = ctx.author
        
        # Show searching message
        loading_embed = discord.Embed(
            title="⏳ Searching...",
            description=f"Looking for: **{query}**",
            color=config.BOT_COLOR
        )
        loading_msg = await ctx.send(embed=loading_embed)
        
        try:
            # Search for tracks
            tracks: wavelink.Search = await wavelink.Playable.search(query)
            
            if not tracks:
                embed = discord.Embed(
                    title="❌ No Results",
                    description=f"No results found for: **{query}**",
                    color=config.BOT_COLOR_ERROR
                )
                return await loading_msg.edit(embed=embed)
            
            # Handle playlists
            if isinstance(tracks, wavelink.Playlist):
                added = 0
                for track in tracks.tracks:
                    player.queue.put(track)
                    added += 1
                
                embed = discord.Embed(
                    title="📋 Playlist Added",
                    description=f"**{tracks.name}**\nAdded **{added}** tracks to the queue!",
                    color=config.BOT_COLOR_SUCCESS
                )
                embed.set_footer(text=f"Requested by {ctx.author.display_name}")
                await loading_msg.edit(embed=embed)
                
                # Start playing if not already
                if not player.playing:
                    track = player.queue.get()
                    await player.play(track)
            else:
                # Single track
                track = tracks[0]
                
                if player.playing:
                    player.queue.put(track)
                    
                    embed = discord.Embed(
                        title="✅ Added to Queue",
                        description=f"**[{track.title}]({track.uri})**",
                        color=config.BOT_COLOR_SUCCESS
                    )
                    embed.add_field(name="👤 Artist", value=track.author or "Unknown", inline=True)
                    embed.add_field(name="⏱️ Duration", value=self.format_duration(track.length), inline=True)
                    embed.add_field(name="📋 Position", value=f"#{player.queue.count}", inline=True)
                    embed.set_footer(text=f"Requested by {ctx.author.display_name}")
                    
                    if hasattr(track, 'artwork') and track.artwork:
                        embed.set_thumbnail(url=track.artwork)
                    
                    await loading_msg.edit(embed=embed)
                else:
                    await player.play(track)
                    await loading_msg.delete()
                    
        except Exception as e:
            logger.error(f"Error playing track: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=f"An error occurred: {str(e)[:200]}",
                color=config.BOT_COLOR_ERROR
            )
            await loading_msg.edit(embed=embed)
    
    # ═══════════════════════════════════════════════════════════
    # ⏸️ PAUSE COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(name="pause", description="Pause the current track")
    async def pause(self, ctx: commands.Context):
        """Pause the current track"""
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if not player:
            return await ctx.send("❌ Not playing anything!", delete_after=10)
        
        if player.paused:
            return await ctx.send("⏸️ Already paused!", delete_after=10)
        
        await player.pause(True)
        
        embed = discord.Embed(
            title="⏸️ Paused",
            description=f"Paused: **{player.current.title}**" if player.current else "Playback paused",
            color=config.BOT_COLOR_WARNING
        )
        await ctx.send(embed=embed, delete_after=15)
    
    # ═══════════════════════════════════════════════════════════
    # ▶️ RESUME COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(name="resume", aliases=["unpause"], description="Resume playback")
    async def resume(self, ctx: commands.Context):
        """Resume the paused track"""
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if not player:
            return await ctx.send("❌ Not playing anything!", delete_after=10)
        
        if not player.paused:
            return await ctx.send("▶️ Already playing!", delete_after=10)
        
        await player.pause(False)
        
        embed = discord.Embed(
            title="▶️ Resumed",
            description=f"Resumed: **{player.current.title}**" if player.current else "Playback resumed",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=15)
    
    # ═══════════════════════════════════════════════════════════
    # ⏭️ SKIP COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(name="skip", aliases=["s", "next"], description="Skip the current track")
    async def skip(self, ctx: commands.Context):
        """Skip to the next track"""
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if not player or not player.current:
            return await ctx.send("❌ Nothing to skip!", delete_after=10)
        
        title = player.current.title
        await player.stop()
        
        embed = discord.Embed(
            title="⏭️ Skipped",
            description=f"Skipped: **{title}**",
            color=config.BOT_COLOR_INFO
        )
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # ⏹️ STOP COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(name="stop", description="Stop playback and clear queue")
    async def stop(self, ctx: commands.Context):
        """Stop playback and clear the queue"""
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if not player:
            return await ctx.send("❌ Not playing anything!", delete_after=10)
        
        player.queue.clear()
        await player.stop()
        
        embed = discord.Embed(
            title="⏹️ Stopped",
            description="Playback stopped and queue cleared!",
            color=config.BOT_COLOR_WARNING
        )
        await ctx.send(embed=embed, delete_after=15)
    
    # ═══════════════════════════════════════════════════════════
    # 🔊 VOLUME COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(name="volume", aliases=["vol", "v"], description="Set the volume")
    @app_commands.describe(level="Volume level (0-150)")
    async def volume(self, ctx: commands.Context, level: int = None):
        """Set or show the volume"""
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if not player:
            return await ctx.send("❌ Not connected!", delete_after=10)
        
        if level is None:
            embed = discord.Embed(
                title="🔊 Current Volume",
                description=f"**{player.volume}%**",
                color=config.BOT_COLOR_INFO
            )
            return await ctx.send(embed=embed, delete_after=15)
        
        level = max(0, min(150, level))
        await player.set_volume(level)
        
        # Volume emoji
        if level == 0:
            emoji = "🔇"
        elif level < 30:
            emoji = "🔈"
        elif level < 70:
            emoji = "🔉"
        else:
            emoji = "🔊"
        
        embed = discord.Embed(
            title=f"{emoji} Volume Set",
            description=f"Volume: **{level}%**",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=15)
    
    # ═══════════════════════════════════════════════════════════
    # 📋 QUEUE COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(name="queue", aliases=["q"], description="Show the music queue")
    async def queue(self, ctx: commands.Context):
        """Show the current queue"""
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if not player:
            return await ctx.send("❌ Not connected!", delete_after=10)
        
        embed = discord.Embed(
            title="📋 Music Queue",
            color=config.BOT_COLOR
        )
        
        # Current track
        if player.current:
            duration = self.format_duration(player.current.length)
            embed.add_field(
                name="🎵 Now Playing",
                value=f"**[{player.current.title}]({player.current.uri})**\n⏱️ {duration}",
                inline=False
            )
        
        # Queue
        if player.queue.count > 0:
            queue_list = ""
            for i, track in enumerate(list(player.queue)[:10], 1):
                duration = self.format_duration(track.length)
                queue_list += f"`{i}.` **{track.title}** - {duration}\n"
            
            if player.queue.count > 10:
                queue_list += f"\n*...and {player.queue.count - 10} more tracks*"
            
            embed.add_field(name="📋 Up Next", value=queue_list, inline=False)
            
            # Total duration
            total_ms = sum(t.length for t in player.queue)
            embed.set_footer(text=f"Total: {player.queue.count} tracks • {self.format_duration(total_ms)}")
        else:
            embed.add_field(name="📋 Up Next", value="Queue is empty!", inline=False)
        
        await ctx.send(embed=embed)
    
    # ═══════════════════════════════════════════════════════════
    # 🔀 SHUFFLE COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(name="shuffle", description="Shuffle the queue")
    async def shuffle(self, ctx: commands.Context):
        """Shuffle the queue"""
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if not player:
            return await ctx.send("❌ Not connected!", delete_after=10)
        
        if player.queue.count < 2:
            return await ctx.send("❌ Need at least 2 tracks to shuffle!", delete_after=10)
        
        player.queue.shuffle()
        
        embed = discord.Embed(
            title="🔀 Queue Shuffled",
            description=f"Shuffled **{player.queue.count}** tracks!",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=15)
    
    # ═══════════════════════════════════════════════════════════
    # 🔁 LOOP COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(name="loop", aliases=["repeat"], description="Toggle loop mode")
    @app_commands.describe(mode="Loop mode: off, track, or queue")
    async def loop(self, ctx: commands.Context, mode: str = None):
        """Toggle or set loop mode"""
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if not player:
            return await ctx.send("❌ Not connected!", delete_after=10)
        
        if mode:
            mode = mode.lower()
            if mode not in ["off", "track", "queue"]:
                return await ctx.send("❌ Invalid mode! Use: `off`, `track`, or `queue`", delete_after=10)
            player.loop_mode = mode
        else:
            # Cycle through modes
            modes = ["off", "track", "queue"]
            current_idx = modes.index(player.loop_mode)
            player.loop_mode = modes[(current_idx + 1) % 3]
        
        mode_emojis = {"off": "➡️", "track": "🔂", "queue": "🔁"}
        
        embed = discord.Embed(
            title=f"{mode_emojis[player.loop_mode]} Loop Mode",
            description=f"Loop mode: **{player.loop_mode.capitalize()}**",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=15)
    
    # ═══════════════════════════════════════════════════════════
    # 📍 NOWPLAYING COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(name="nowplaying", aliases=["np", "current"], description="Show current track")
    async def nowplaying(self, ctx: commands.Context):
        """Show the currently playing track"""
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if not player or not player.current:
            return await ctx.send("❌ Nothing playing!", delete_after=10)
        
        embed = await self.create_now_playing_embed(player, player.current)
        await ctx.send(embed=embed)
    
    # ═══════════════════════════════════════════════════════════
    # ⏮️ PREVIOUS COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(name="previous", aliases=["prev", "back"], description="Play previous track")
    async def previous(self, ctx: commands.Context):
        """Play the previous track from history"""
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if not player:
            return await ctx.send("❌ Not connected!", delete_after=10)
        
        if not player.history:
            return await ctx.send("❌ No history!", delete_after=10)
        
        track = player.history.pop()
        
        # Add current to front of queue
        if player.current:
            player.queue.put_at(0, player.current)
        
        await player.play(track)
        
        embed = discord.Embed(
            title="⏮️ Playing Previous",
            description=f"**{track.title}**",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=15)
    
    # ═══════════════════════════════════════════════════════════
    # ⏩ SEEK COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(name="seek", description="Seek to a position")
    @app_commands.describe(position="Position in seconds or MM:SS format")
    async def seek(self, ctx: commands.Context, position: str):
        """Seek to a position in the track"""
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if not player or not player.current:
            return await ctx.send("❌ Nothing playing!", delete_after=10)
        
        # Parse position
        try:
            if ":" in position:
                parts = position.split(":")
                if len(parts) == 2:
                    seconds = int(parts[0]) * 60 + int(parts[1])
                elif len(parts) == 3:
                    seconds = int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
                else:
                    raise ValueError()
            else:
                seconds = int(position)
        except:
            return await ctx.send("❌ Invalid format! Use seconds or MM:SS", delete_after=10)
        
        milliseconds = seconds * 1000
        
        if milliseconds < 0 or milliseconds > player.current.length:
            return await ctx.send("❌ Position out of range!", delete_after=10)
        
        await player.seek(milliseconds)
        
        embed = discord.Embed(
            title="⏩ Seeked",
            description=f"Seeked to **{self.format_duration(milliseconds)}**",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=15)
    
    # ═══════════════════════════════════════════════════════════
    # 🗑️ CLEAR COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(name="clear", aliases=["cls"], description="Clear the queue")
    async def clear(self, ctx: commands.Context):
        """Clear the queue"""
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if not player:
            return await ctx.send("❌ Not connected!", delete_after=10)
        
        count = player.queue.count
        player.queue.clear()
        
        embed = discord.Embed(
            title="🗑️ Queue Cleared",
            description=f"Removed **{count}** tracks!",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=15)
    
    # ═══════════════════════════════════════════════════════════
    # 🚪 LEAVE COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(name="leave", aliases=["disconnect", "dc"], description="Leave voice channel")
    async def leave(self, ctx: commands.Context):
        """Leave the voice channel"""
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if not player:
            return await ctx.send("❌ Not connected!", delete_after=10)
        
        await player.disconnect()
        
        embed = discord.Embed(
            title="👋 Disconnected",
            description="Left the voice channel!",
            color=config.BOT_COLOR_INFO
        )
        await ctx.send(embed=embed, delete_after=15)
    
    # ═══════════════════════════════════════════════════════════
    # 🔗 JOIN COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(name="join", aliases=["connect", "summon"], description="Join voice channel")
    async def join(self, ctx: commands.Context):
        """Join your voice channel"""
        if not ctx.author.voice:
            return await ctx.send("❌ You're not in a voice channel!", delete_after=10)
        
        channel = ctx.author.voice.channel
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if player:
            if player.channel == channel:
                return await ctx.send("✅ Already in your channel!", delete_after=10)
            await player.move_to(channel)
        else:
            player = await channel.connect(cls=ShlokPlayer, self_deaf=True)
            player.text_channel = ctx.channel
        
        embed = discord.Embed(
            title="🔗 Connected",
            description=f"Joined **{channel.name}**!",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=15)
    
    # ═══════════════════════════════════════════════════════════
    # 🔍 SEARCH COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(name="search", description="Search for tracks")
    @app_commands.describe(query="Search query")
    async def search(self, ctx: commands.Context, *, query: str):
        """Search for tracks and choose one to play"""
        
        loading_embed = discord.Embed(
            title="🔍 Searching...",
            description=f"Looking for: **{query}**",
            color=config.BOT_COLOR
        )
        loading_msg = await ctx.send(embed=loading_embed)
        
        try:
            tracks = await wavelink.Playable.search(query)
            
            if not tracks or isinstance(tracks, wavelink.Playlist):
                embed = discord.Embed(
                    title="❌ No Results",
                    description=f"No results found for: **{query}**",
                    color=config.BOT_COLOR_ERROR
                )
                return await loading_msg.edit(embed=embed)
            
            # Show top 5 results
            embed = discord.Embed(
                title=f"🔍 Search Results for: {query}",
                color=config.BOT_COLOR
            )
            
            description = ""
            for i, track in enumerate(tracks[:5], 1):
                duration = self.format_duration(track.length)
                description += f"**{i}.** [{track.title}]({track.uri})\n"
                description += f"    └ 👤 {track.author} • ⏱️ {duration}\n\n"
            
            embed.description = description
            embed.set_footer(text="Reply with a number (1-5) to play, or 'cancel' to cancel")
            
            await loading_msg.edit(embed=embed)
            
            # Wait for response
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel
            
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=30.0)
                
                if msg.content.lower() == 'cancel':
                    await loading_msg.delete()
                    await msg.delete()
                    return
                
                try:
                    choice = int(msg.content)
                    if 1 <= choice <= min(5, len(tracks)):
                        await msg.delete()
                        ctx.message = msg  # For the play command
                        await self.play(ctx, query=tracks[choice - 1].uri)
                except ValueError:
                    pass
                    
            except asyncio.TimeoutError:
                embed.set_footer(text="Search timed out")
                await loading_msg.edit(embed=embed)
                
        except Exception as e:
            logger.error(f"Search error: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description=str(e)[:200],
                color=config.BOT_COLOR_ERROR
            )
            await loading_msg.edit(embed=embed)
    
    # ═══════════════════════════════════════════════════════════
    # 🎛️ FILTER COMMANDS
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(name="bassboost", aliases=["bass"], description="Toggle bass boost")
    async def bassboost(self, ctx: commands.Context):
        """Toggle bass boost filter"""
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if not player:
            return await ctx.send("❌ Not connected!", delete_after=10)
        
        filters = player.filters
        
        if player.effect == "bass_boost":
            filters.reset()
            player.effect = "none"
            title = "🔊 Bass Boost Disabled"
        else:
            filters.equalizer.set(bands=[
                {"band": 0, "gain": 0.25},
                {"band": 1, "gain": 0.20},
                {"band": 2, "gain": 0.15},
                {"band": 3, "gain": 0.10}
            ])
            player.effect = "bass_boost"
            title = "🔊 Bass Boost Enabled"
        
        await player.set_filters(filters)
        
        embed = discord.Embed(title=title, color=config.BOT_COLOR_SUCCESS)
        await ctx.send(embed=embed, delete_after=15)
    
    @commands.hybrid_command(name="nightcore", description="Toggle nightcore effect")
    async def nightcore(self, ctx: commands.Context):
        """Toggle nightcore filter"""
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if not player:
            return await ctx.send("❌ Not connected!", delete_after=10)
        
        filters = player.filters
        
        if player.effect == "nightcore":
            filters.reset()
            player.effect = "none"
            title = "⚡ Nightcore Disabled"
        else:
            filters.timescale.set(speed=1.25, pitch=1.25, rate=1.0)
            player.effect = "nightcore"
            title = "⚡ Nightcore Enabled"
        
        await player.set_filters(filters)
        
        embed = discord.Embed(title=title, color=config.BOT_COLOR_SUCCESS)
        await ctx.send(embed=embed, delete_after=15)
    
    @commands.hybrid_command(name="vaporwave", description="Toggle vaporwave effect")
    async def vaporwave(self, ctx: commands.Context):
        """Toggle vaporwave filter"""
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if not player:
            return await ctx.send("❌ Not connected!", delete_after=10)
        
        filters = player.filters
        
        if player.effect == "vaporwave":
            filters.reset()
            player.effect = "none"
            title = "🌊 Vaporwave Disabled"
        else:
            filters.timescale.set(speed=0.8, pitch=0.85, rate=1.0)
            player.effect = "vaporwave"
            title = "🌊 Vaporwave Enabled"
        
        await player.set_filters(filters)
        
        embed = discord.Embed(title=title, color=config.BOT_COLOR_SUCCESS)
        await ctx.send(embed=embed, delete_after=15)
    
    @commands.hybrid_command(name="resetfilter", aliases=["filterreset", "nofilter"], description="Reset all filters")
    async def resetfilter(self, ctx: commands.Context):
        """Reset all audio filters"""
        player: ShlokPlayer = cast(ShlokPlayer, ctx.voice_client)
        
        if not player:
            return await ctx.send("❌ Not connected!", delete_after=10)
        
        filters = player.filters
        filters.reset()
        await player.set_filters(filters)
        player.effect = "none"
        
        embed = discord.Embed(
            title="🎛️ Filters Reset",
            description="All audio filters have been disabled!",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=15)


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicNew(bot))
    logger.info("✅ Music cog loaded")
