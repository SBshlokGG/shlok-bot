"""
🎵 Music Commands Cog
All music-related commands for Shlok Music Bot
"""

import asyncio
import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

import config
from core import Track, TrackExtractor, LoopMode

logger = logging.getLogger('ShlokMusic.Music')

# ═══════════════════════════════════════════════════════════════
# 🎵 MUSIC COG
# ═══════════════════════════════════════════════════════════════

class Music(commands.Cog, name="Music"):
    """🎵 Music playback commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def get_player(self, ctx):
        """Get or create music player for the guild"""
        return self.bot.get_player(ctx.guild.id)
    
    # ═══════════════════════════════════════════════════════════
    # 🔧 HELPER METHODS
    # ═══════════════════════════════════════════════════════════
    
    async def ensure_voice(self, ctx) -> bool:
        """Ensure user is in a voice channel and bot can join"""
        if not ctx.author.voice:
            embed = discord.Embed(
                title="❌ Not Connected",
                description="You need to be in a voice channel to use this command!",
                color=config.BOT_COLOR_ERROR
            )
            try:
                await ctx.interaction.followup.send(embed=embed, ephemeral=True)
            except:
                await ctx.send(embed=embed, delete_after=10)
            return False
        
        player = self.get_player(ctx)
        
        # Connect if not already connected
        if not player.is_connected:
            channel = ctx.author.voice.channel
            
            # Check permissions
            permissions = channel.permissions_for(ctx.guild.me)
            if not permissions.connect or not permissions.speak:
                embed = discord.Embed(
                    title="❌ Missing Permissions",
                    description="I need `Connect` and `Speak` permissions in that channel!",
                    color=config.BOT_COLOR_ERROR
                )
                try:
                    await ctx.interaction.followup.send(embed=embed, ephemeral=True)
                except:
                    await ctx.send(embed=embed, delete_after=10)
                return False
            
            success = await player.connect(channel)
            if not success:
                embed = discord.Embed(
                    title="❌ Connection Failed",
                    description="Failed to connect to the voice channel. Please try again.",
                    color=config.BOT_COLOR_ERROR
                )
                try:
                    await ctx.interaction.followup.send(embed=embed, ephemeral=True)
                except:
                    await ctx.send(embed=embed, delete_after=10)
                return False
        
        # Store text channel for messages
        player.text_channel = ctx.channel
        
        return True
    
    async def create_search_embed(self, tracks: list[Track], query: str) -> discord.Embed:
        """Create embed for search results"""
        embed = discord.Embed(
            title=f"🔍 Search Results for: {query}",
            color=config.BOT_COLOR
        )
        
        description = ""
        for i, track in enumerate(tracks[:5], 1):
            duration = track.duration_formatted if track.duration else "Live"
            description += f"**{i}.** [{track.title}]({track.url})\n"
            description += f"    └ 👤 {track.artist} • ⏱️ {duration}\n\n"
        
        embed.description = description
        embed.set_footer(text="Reply with a number (1-5) to select, or 'cancel' to cancel")
        
        return embed
    
    # ═══════════════════════════════════════════════════════════
    # ▶️ PLAY COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="play",
        aliases=["p", "add"],
        description="Play a song or add it to the queue"
    )
    @app_commands.describe(query="Song name or URL to play")
    async def play(self, ctx: commands.Context, *, query: str):
        """
        Play a song or add it to the queue
        
        Usage:
            !play <song name or URL>
            !play https://youtube.com/watch?v=...
            !play Never Gonna Give You Up
        """
        # Defer the interaction immediately to avoid timeout
        if not ctx.interaction.response.is_done():
            try:
                await ctx.interaction.response.defer()
            except:
                pass
        
        if not await self.ensure_voice(ctx):
            return
        
        player = self.get_player(ctx)
        
        # Show loading message
        loading_embed = discord.Embed(
            title="⏳ Searching...",
            description=f"Looking for: **{query}**",
            color=config.BOT_COLOR
        )
        try:
            loading_msg = await ctx.interaction.followup.send(embed=loading_embed)
        except:
            loading_msg = await ctx.send(embed=loading_embed)
        
        try:
            # Search for tracks
            tracks = await TrackExtractor.search(query, requester=ctx.author, limit=1)
            
            if not tracks:
                embed = discord.Embed(
                    title="❌ No Results",
                    description=f"No results found for: **{query}**",
                    color=config.BOT_COLOR_ERROR
                )
                try:
                    await loading_msg.edit(embed=embed)
                except:
                    await ctx.interaction.followup.send(embed=embed)
                return
            
            track = tracks[0]
            
            # Check duration limit
            if track.duration and track.duration > config.MUSIC.max_song_duration:
                embed = discord.Embed(
                    title="❌ Track Too Long",
                    description=f"Track exceeds maximum duration of {config.MUSIC.max_song_duration // 60} minutes",
                    color=config.BOT_COLOR_ERROR
                )
                try:
                    await loading_msg.edit(embed=embed)
                except:
                    await ctx.interaction.followup.send(embed=embed)
                return
            
            # Add to queue or play immediately
            if player.is_playing or player.is_paused:
                position = len(player.queue) + 1
                player.queue.append(track)
                
                embed = discord.Embed(
                    title="✅ Added to Queue",
                    description=f"**[{track.title}]({track.url})**",
                    color=config.BOT_COLOR_SUCCESS
                )
                embed.add_field(name="Position", value=f"#{position}", inline=False)
                
                try:
                    await loading_msg.edit(embed=embed)
                except:
                    await ctx.interaction.followup.send(embed=embed)
            else:
                try:
                    await loading_msg.delete()
                except:
                    pass
                await player.play(track)
                embed = discord.Embed(
                    title="▶️ Now Playing",
                    description=f"**{track.title}**",
                    color=config.BOT_COLOR_SUCCESS
                )
                try:
                    await ctx.interaction.followup.send(embed=embed)
                except:
                    await ctx.send(embed=embed)
            
            self.bot.commands_used += 1
            
        except Exception as e:
            logger.error(f"Error in play command: {e}", exc_info=True)
            embed = discord.Embed(
                title="❌ Error",
                description=f"Error: {str(e)[:80]}",
                color=config.BOT_COLOR_ERROR
            )
            try:
                await loading_msg.edit(embed=embed)
            except:
                try:
                    await ctx.interaction.followup.send(embed=embed, ephemeral=True)
                except:
                    await ctx.send(embed=embed)
    
    # ═══════════════════════════════════════════════════════════
    # 🔍 SEARCH COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="search",
        aliases=["find", "lookup"],
        description="Search for a song and choose from results"
    )
    @app_commands.describe(query="Song name to search")
    async def search(self, ctx: commands.Context, *, query: str):
        """
        Search for songs and choose from results
        
        Usage:
            !search <song name>
        """
        if not await self.ensure_voice(ctx):
            return
        
        # Search for multiple results
        tracks = await TrackExtractor.search(query, requester=ctx.author, limit=5)
        
        if not tracks:
            embed = discord.Embed(
                title="❌ No Results",
                description=f"No results found for: **{query}**",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Create search results embed
        embed = await self.create_search_embed(tracks, query)
        search_msg = await ctx.send(embed=embed)
        
        # Add number reactions
        reactions = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "❌"]
        for emoji in reactions[:len(tracks) + 1]:
            await search_msg.add_reaction(emoji)
        
        def check(reaction, user):
            return (
                user == ctx.author and 
                reaction.message.id == search_msg.id and 
                str(reaction.emoji) in reactions
            )
        
        try:
            reaction, user = await self.bot.wait_for('reaction_add', timeout=30.0, check=check)
            
            await search_msg.delete()
            
            if str(reaction.emoji) == "❌":
                return
            
            # Get selected track
            index = reactions.index(str(reaction.emoji))
            if index < len(tracks):
                track = tracks[index]
                player = self.get_player(ctx)
                
                if player.is_playing or player.is_paused:
                    player.queue.add(track)
                    
                    embed = discord.Embed(
                        title="✅ Added to Queue",
                        description=f"**[{track.title}]({track.url})**",
                        color=config.BOT_COLOR_SUCCESS
                    )
                    await ctx.send(embed=embed, delete_after=10)
                else:
                    await player.play(track)
                    
        except asyncio.TimeoutError:
            await search_msg.delete()
            embed = discord.Embed(
                title="⏱️ Timed Out",
                description="Search selection timed out.",
                color=config.BOT_COLOR_WARNING
            )
            await ctx.send(embed=embed, delete_after=5)
    
    # ═══════════════════════════════════════════════════════════
    # ⏸️ PAUSE COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="pause",
        description="Pause the current track"
    )
    async def pause(self, ctx: commands.Context):
        """Pause the current track"""
        player = self.get_player(ctx)
        
        if not player.is_playing:
            embed = discord.Embed(
                title="❌ Nothing Playing",
                description="There's nothing playing right now!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        if player.is_paused:
            embed = discord.Embed(
                title="⚠️ Already Paused",
                description="The music is already paused! Use `!resume` to continue.",
                color=config.BOT_COLOR_WARNING
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        player.pause()
        
        embed = discord.Embed(
            title="⏸️ Paused",
            description=f"Paused: **{player.current_track.title}**",
            color=config.BOT_COLOR
        )
        await ctx.send(embed=embed, delete_after=10)
        await player.update_now_playing()
    
    # ═══════════════════════════════════════════════════════════
    # ▶️ RESUME COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="resume",
        aliases=["unpause", "continue"],
        description="Resume the paused track"
    )
    async def resume(self, ctx: commands.Context):
        """Resume the paused track"""
        player = self.get_player(ctx)
        
        if not player.is_paused:
            embed = discord.Embed(
                title="❌ Not Paused",
                description="The music isn't paused!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        player.resume()
        
        embed = discord.Embed(
            title="▶️ Resumed",
            description=f"Resumed: **{player.current_track.title}**",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=10)
        await player.update_now_playing()
    
    # ═══════════════════════════════════════════════════════════
    # ⏭️ SKIP COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="skip",
        aliases=["s", "next"],
        description="Skip the current track"
    )
    async def skip(self, ctx: commands.Context):
        """Skip the current track"""
        player = self.get_player(ctx)
        
        if not player.current_track:
            embed = discord.Embed(
                title="❌ Nothing Playing",
                description="There's nothing to skip!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        skipped_track = player.current_track
        await player.skip()
        
        embed = discord.Embed(
            title="⏭️ Skipped",
            description=f"Skipped: **{skipped_track.title}**",
            color=config.BOT_COLOR
        )
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # ⏮️ PREVIOUS COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="previous",
        aliases=["prev", "back"],
        description="Play the previous track"
    )
    async def previous(self, ctx: commands.Context):
        """Play the previous track"""
        player = self.get_player(ctx)
        
        success = await player.previous()
        
        if not success:
            embed = discord.Embed(
                title="❌ No Previous Track",
                description="There's no previous track in history!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        embed = discord.Embed(
            title="⏮️ Playing Previous",
            description=f"Now playing: **{player.current_track.title}**",
            color=config.BOT_COLOR
        )
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # ⏹️ STOP COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="stop",
        description="Stop playback and clear the queue"
    )
    async def stop(self, ctx: commands.Context):
        """Stop playback and clear the queue"""
        player = self.get_player(ctx)
        
        if not player.is_playing and not player.is_paused:
            embed = discord.Embed(
                title="❌ Nothing Playing",
                description="There's nothing playing right now!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        player.stop()
        
        embed = discord.Embed(
            title="⏹️ Stopped",
            description="Playback stopped and queue cleared.",
            color=config.BOT_COLOR
        )
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # 🔊 VOLUME COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="volume",
        aliases=["vol", "v"],
        description="Set the volume (0-500)"
    )
    @app_commands.describe(level="Volume level (0-500)")
    async def volume(self, ctx: commands.Context, level: int = None):
        """
        Set or view the volume
        
        Usage:
            !volume - Show current volume
            !volume 50 - Set volume to 50%
        """
        player = self.get_player(ctx)
        
        if level is None:
            current = int(player.volume * 100)
            
            # Create volume bar
            bar_length = 10
            filled = int(bar_length * (current / 150))
            bar = "█" * filled + "░" * (bar_length - filled)
            
            embed = discord.Embed(
                title="🔊 Current Volume",
                description=f"`{bar}` **{current}%**",
                color=config.BOT_COLOR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        if level < 0 or level > 500:
            embed = discord.Embed(
                title="❌ Invalid Volume",
                description="Volume must be between 0 and 500!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        player.set_volume(level)
        
        # Volume icon based on level
        if level == 0:
            icon = "🔇"
        elif level < 50:
            icon = "🔉"
        else:
            icon = "🔊"
        
        embed = discord.Embed(
            title=f"{icon} Volume Set",
            description=f"Volume set to **{level}%**",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=10)
        await player.update_now_playing()
    
    # ═══════════════════════════════════════════════════════════
    # 🎵 NOW PLAYING COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="nowplaying",
        aliases=["np", "current", "playing"],
        description="Show the currently playing track"
    )
    async def nowplaying(self, ctx: commands.Context):
        """Show the currently playing track"""
        player = self.get_player(ctx)
        
        if not player.current_track:
            embed = discord.Embed(
                title="❌ Nothing Playing",
                description="There's nothing playing right now! Use `!play` to start.",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        # Send new now playing message
        await player._send_now_playing()
    
    # ═══════════════════════════════════════════════════════════
    # 🔁 LOOP COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="loop",
        aliases=["repeat", "l"],
        description="Toggle loop mode"
    )
    @app_commands.describe(mode="Loop mode: off, track, or queue")
    async def loop(self, ctx: commands.Context, mode: str = None):
        """
        Toggle or set loop mode
        
        Usage:
            !loop - Toggle between modes
            !loop track - Loop current track
            !loop queue - Loop entire queue
            !loop off - Disable loop
        """
        player = self.get_player(ctx)
        
        if mode:
            mode = mode.lower()
            if mode in ["off", "disable", "none"]:
                player.loop_mode = LoopMode.OFF
            elif mode in ["track", "song", "one", "single"]:
                player.loop_mode = LoopMode.TRACK
            elif mode in ["queue", "all", "playlist"]:
                player.loop_mode = LoopMode.QUEUE
            else:
                embed = discord.Embed(
                    title="❌ Invalid Mode",
                    description="Valid modes: `off`, `track`, `queue`",
                    color=config.BOT_COLOR_ERROR
                )
                await ctx.send(embed=embed, delete_after=5)
                return
        else:
            player.toggle_loop()
        
        mode_info = {
            LoopMode.OFF: ("❌ Loop Disabled", "Loop mode is now off"),
            LoopMode.TRACK: ("🔂 Loop Track", "Now looping the current track"),
            LoopMode.QUEUE: ("🔁 Loop Queue", "Now looping the entire queue"),
        }
        
        title, desc = mode_info[player.loop_mode]
        
        embed = discord.Embed(
            title=title,
            description=desc,
            color=config.BOT_COLOR
        )
        await ctx.send(embed=embed, delete_after=10)
        await player.update_now_playing()
    
    # ═══════════════════════════════════════════════════════════
    # 🔀 PLAY NOW COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="playnow",
        aliases=["pn", "playtop"],
        description="Play a song immediately, skipping the queue"
    )
    @app_commands.describe(query="Song name or URL to play immediately")
    async def playnow(self, ctx: commands.Context, *, query: str):
        """Play a song immediately, skipping the current track"""
        if not await self.ensure_voice(ctx):
            return
        
        player = self.get_player(ctx)
        
        # Search for track
        tracks = await TrackExtractor.search(query, requester=ctx.author, limit=1)
        
        if not tracks:
            embed = discord.Embed(
                title="❌ No Results",
                description=f"No results found for: **{query}**",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        track = tracks[0]
        
        # Add current track back to front of queue if playing
        if player.current_track:
            player.queue.add_to_front(player.current_track)
        
        # Play immediately
        await player.play(track)
        
        embed = discord.Embed(
            title="⚡ Playing Now",
            description=f"**[{track.title}]({track.url})**",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # 📻 JOIN/LEAVE COMMANDS
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="join",
        aliases=["connect", "j"],
        description="Join your voice channel"
    )
    async def join(self, ctx: commands.Context):
        """Join your voice channel"""
        if not ctx.author.voice:
            embed = discord.Embed(
                title="❌ Not Connected",
                description="You need to be in a voice channel!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        player = self.get_player(ctx)
        channel = ctx.author.voice.channel
        
        success = await player.connect(channel)
        
        if success:
            embed = discord.Embed(
                title="🔊 Connected",
                description=f"Joined **{channel.name}**",
                color=config.BOT_COLOR_SUCCESS
            )
        else:
            embed = discord.Embed(
                title="❌ Failed",
                description="Could not connect to the voice channel.",
                color=config.BOT_COLOR_ERROR
            )
        
        await ctx.send(embed=embed, delete_after=10)
    
    @commands.hybrid_command(
        name="leave",
        aliases=["disconnect", "dc", "bye"],
        description="Leave the voice channel"
    )
    async def leave(self, ctx: commands.Context):
        """Leave the voice channel"""
        player = self.get_player(ctx)
        
        if not player.is_connected:
            embed = discord.Embed(
                title="❌ Not Connected",
                description="I'm not connected to a voice channel!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        await player.disconnect()
        
        embed = discord.Embed(
            title="👋 Disconnected",
            description="Left the voice channel. See you next time!",
            color=config.BOT_COLOR
        )
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # 🎲 AUTOPLAY COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="seek",
        description="Seek to a specific position in the track"
    )
    @app_commands.describe(position="Position in format mm:ss or seconds")
    async def seek(self, ctx: commands.Context, position: str):
        """
        Seek to a position in the current track
        
        Usage:
            !seek 1:30 - Seek to 1 minute 30 seconds
            !seek 90 - Seek to 90 seconds
        """
        player = self.get_player(ctx)
        
        if not player.current_track:
            embed = discord.Embed(
                title="❌ Nothing Playing",
                description="There's nothing playing to seek!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
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
            embed = discord.Embed(
                title="❌ Invalid Format",
                description="Use format: `mm:ss` or seconds (e.g., `1:30` or `90`)",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        # Note: Seek functionality requires re-streaming which is complex
        # This is a placeholder response
        embed = discord.Embed(
            title="⚠️ Seek Not Available",
            description="Seeking is not supported for this audio source.",
            color=config.BOT_COLOR_WARNING
        )
        await ctx.send(embed=embed, delete_after=5)


# ═══════════════════════════════════════════════════════════════
# 🔧 COG SETUP
# ═══════════════════════════════════════════════════════════════

async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
    logger.info("✅ Music cog loaded")
