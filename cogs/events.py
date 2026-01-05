"""
🔔 Events Cog
Handles Discord events including reaction controls
"""

import asyncio
import logging
from typing import Optional

import discord
from discord.ext import commands

import config
from core import LoopMode

logger = logging.getLogger('ShlokMusic.Events')

# ═══════════════════════════════════════════════════════════════
# 🔔 EVENTS COG
# ═══════════════════════════════════════════════════════════════

class Events(commands.Cog, name="Events"):
    """🔔 Event handlers and reaction controls"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.cooldowns = {}  # User cooldowns for reactions
    
    def get_player(self, guild_id: int):
        """Get or create music player for the guild"""
        return self.bot.get_player(guild_id)
    
    # ═══════════════════════════════════════════════════════════
    # 🎮 REACTION CONTROLS
    # ═══════════════════════════════════════════════════════════
    
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        """Handle reaction-based controls on now playing messages"""
        # Ignore bot reactions
        if payload.user_id == self.bot.user.id:
            return
        
        # Check if this guild has a player
        if payload.guild_id not in self.bot.music_players:
            return
        
        player = self.get_player(payload.guild_id)
        
        # Check if this is the now playing message
        if not player.now_playing_message or player.now_playing_message.id != payload.message_id:
            return
        
        # Get the emoji and action
        emoji = str(payload.emoji)
        if emoji not in config.REACTION_CONTROLS:
            return
        
        action = config.REACTION_CONTROLS[emoji]
        
        # Get the user and channel
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        
        member = guild.get_member(payload.user_id)
        if not member:
            return
        
        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return
        
        # Check cooldown (prevent spam)
        cooldown_key = f"{payload.user_id}:{action}"
        if cooldown_key in self.cooldowns:
            return
        
        self.cooldowns[cooldown_key] = True
        asyncio.get_event_loop().call_later(1.0, lambda: self.cooldowns.pop(cooldown_key, None))
        
        # Check if user is in voice channel
        if not member.voice or (player.voice_client and member.voice.channel != player.voice_client.channel):
            try:
                await channel.send(
                    f"❌ {member.mention} You need to be in the same voice channel!",
                    delete_after=5
                )
            except:
                pass
            return
        
        # Remove the user's reaction
        try:
            message = await channel.fetch_message(payload.message_id)
            await message.remove_reaction(payload.emoji, member)
        except:
            pass
        
        # Execute the action
        await self._handle_reaction_action(action, player, member, channel)
    
    async def _handle_reaction_action(self, action: str, player, member: discord.Member, channel: discord.TextChannel):
        """Handle a reaction control action"""
        try:
            response = None
            
            if action == "pause_resume":
                if player.is_paused:
                    player.resume()
                    response = ("▶️ Resumed", f"Resumed by {member.display_name}")
                else:
                    player.pause()
                    response = ("⏸️ Paused", f"Paused by {member.display_name}")
                await player.update_now_playing()
            
            elif action == "skip":
                if player.current_track:
                    title = player.current_track.title
                    await player.skip()
                    response = ("⏭️ Skipped", f"**{title}** skipped by {member.display_name}")
            
            elif action == "stop":
                player.stop()
                response = ("⏹️ Stopped", f"Playback stopped by {member.display_name}")
            
            elif action == "shuffle":
                if player.queue.shuffle():
                    response = ("🔀 Shuffled", f"Queue shuffled by {member.display_name}")
                else:
                    response = ("❌ Error", "Not enough tracks to shuffle")
            
            elif action == "loop_queue":
                mode = player.set_loop_queue()
                mode_str = "enabled" if mode == LoopMode.QUEUE else "disabled"
                response = ("🔁 Loop Queue", f"Queue loop {mode_str} by {member.display_name}")
                await player.update_now_playing()
            
            elif action == "loop_track":
                mode = player.set_loop_track()
                mode_str = "enabled" if mode == LoopMode.TRACK else "disabled"
                response = ("🔂 Loop Track", f"Track loop {mode_str} by {member.display_name}")
                await player.update_now_playing()
            
            elif action == "volume_down":
                current = int(player.volume * 100)
                new_vol = max(0, current - 10)
                player.set_volume(new_vol)
                response = ("🔉 Volume Down", f"Volume: **{new_vol}%**")
                await player.update_now_playing()
            
            elif action == "volume_up":
                current = int(player.volume * 100)
                new_vol = min(150, current + 10)
                player.set_volume(new_vol)
                response = ("🔊 Volume Up", f"Volume: **{new_vol}%**")
                await player.update_now_playing()
            
            elif action == "favorite":
                if player.current_track:
                    added = player.add_favorite(member.id, player.current_track)
                    if added:
                        response = ("❤️ Favorited", f"Added to {member.display_name}'s favorites")
                    else:
                        response = ("💔 Already Favorited", "This track is already in your favorites")
            
            elif action == "show_queue":
                # Send queue info
                if len(player.queue) == 0:
                    response = ("📋 Queue Empty", "No tracks in queue")
                else:
                    queue_preview = ""
                    for i, track in enumerate(player.queue.get_list(0, 5), 1):
                        queue_preview += f"**{i}.** {track.title[:40]}...\n" if len(track.title) > 40 else f"**{i}.** {track.title}\n"
                    
                    if len(player.queue) > 5:
                        queue_preview += f"\n*...and {len(player.queue) - 5} more tracks*"
                    
                    embed = discord.Embed(
                        title="📋 Queue Preview",
                        description=queue_preview,
                        color=config.BOT_COLOR
                    )
                    embed.set_footer(text=f"Use !queue for full list • Total: {len(player.queue)} tracks")
                    await channel.send(embed=embed, delete_after=15)
                    return
            
            elif action == "lyrics":
                if player.current_track:
                    embed = discord.Embed(
                        title="🎤 Lyrics",
                        description=f"Use `!lyrics` to view lyrics for **{player.current_track.title}**",
                        color=config.BOT_COLOR_INFO
                    )
                    await channel.send(embed=embed, delete_after=10)
                    return
            
            elif action == "previous":
                success = await player.previous()
                if success:
                    response = ("⏮️ Previous", f"Playing previous track")
                else:
                    response = ("❌ No History", "No previous track in history")
            
            # Send response
            if response:
                embed = discord.Embed(
                    title=response[0],
                    description=response[1],
                    color=config.BOT_COLOR
                )
                await channel.send(embed=embed, delete_after=5)
                
        except Exception as e:
            logger.error(f"Error handling reaction action {action}: {e}")
    
    # ═══════════════════════════════════════════════════════════
    # 📝 COMMAND ERROR HANDLER
    # ═══════════════════════════════════════════════════════════
    
    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Handle command errors"""
        # Ignore if command has its own error handler
        if hasattr(ctx.command, 'on_error'):
            return
        
        # Ignore if cog has its own error handler
        if ctx.cog and ctx.cog._get_overridden_method(ctx.cog.cog_command_error) is not None:
            return
        
        # Get the original error
        error = getattr(error, 'original', error)
        
        # Handle specific errors
        if isinstance(error, commands.CommandNotFound):
            return  # Silently ignore
        
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = discord.Embed(
                title="❌ Missing Argument",
                description=f"Missing required argument: `{error.param.name}`\n"
                           f"Use `!help {ctx.command}` for more info.",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
        
        elif isinstance(error, commands.BadArgument):
            embed = discord.Embed(
                title="❌ Invalid Argument",
                description=f"Invalid argument provided.\n"
                           f"Use `!help {ctx.command}` for more info.",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
        
        elif isinstance(error, commands.MissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description=f"You need these permissions: `{perms}`",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
        
        elif isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(error.missing_permissions)
            embed = discord.Embed(
                title="❌ Bot Missing Permissions",
                description=f"I need these permissions: `{perms}`",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
        
        elif isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="⏱️ Cooldown",
                description=f"Please wait **{error.retry_after:.1f}** seconds before using this command again.",
                color=config.BOT_COLOR_WARNING
            )
            await ctx.send(embed=embed, delete_after=5)
        
        elif isinstance(error, commands.NoPrivateMessage):
            embed = discord.Embed(
                title="❌ Server Only",
                description="This command can only be used in a server!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
        
        else:
            # Log unexpected errors
            logger.error(f"Unexpected error in {ctx.command}: {error}", exc_info=error)
            
            embed = discord.Embed(
                title="❌ Error",
                description="An unexpected error occurred. Please try again later.",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # 📊 GUILD EVENTS
    # ═══════════════════════════════════════════════════════════
    
    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        """Called when the bot joins a new guild"""
        logger.info(f"📥 Joined guild: {guild.name} (ID: {guild.id})")
        
        # Try to send a welcome message
        try:
            # Find a suitable channel
            channel = None
            for ch in guild.text_channels:
                if ch.permissions_for(guild.me).send_messages:
                    channel = ch
                    break
            
            if channel:
                embed = discord.Embed(
                    title="🎵 Thanks for adding Shlok Music!",
                    description=(
                        "I'm a high-quality music bot with tons of features!\n\n"
                        "**Quick Start:**\n"
                        "• `!play <song>` - Play a song\n"
                        "• `!queue` - View the queue\n"
                        "• `!help` - See all commands\n\n"
                        "**Features:**\n"
                        "• 🎵 High-quality audio streaming\n"
                        "• 🎮 Reaction-based controls\n"
                        "• 🎛️ Audio effects (bass boost, nightcore, etc.)\n"
                        "• 📋 Advanced queue management\n"
                        "• 🔄 24/7 music playback\n"
                        "• 🎤 Lyrics support\n"
                    ),
                    color=config.BOT_COLOR
                )
                embed.set_footer(text="Use !help for a full list of commands")
                
                await channel.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")
    
    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """Called when the bot leaves a guild"""
        logger.info(f"📤 Left guild: {guild.name} (ID: {guild.id})")
        
        # Cleanup player
        if guild.id in self.bot.music_players:
            try:
                player = self.bot.music_players[guild.id]
                await player.disconnect()
            except:
                pass
            del self.bot.music_players[guild.id]
    
    # ═══════════════════════════════════════════════════════════
    # 🎤 MESSAGE EVENTS
    # ═══════════════════════════════════════════════════════════
    
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handle special message events"""
        # Ignore bots
        if message.author.bot:
            return
        
        # Respond to mentions
        if self.bot.user in message.mentions and len(message.content.split()) == 1:
            embed = discord.Embed(
                title="🎵 Shlok Music",
                description=f"Hey {message.author.mention}! My prefix is `{config.BOT_PREFIX}`\n"
                           f"Use `{config.BOT_PREFIX}help` to see all commands!",
                color=config.BOT_COLOR
            )
            await message.channel.send(embed=embed, delete_after=15)


# ═══════════════════════════════════════════════════════════════
# 🔧 COG SETUP
# ═══════════════════════════════════════════════════════════════

async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))
    logger.info("✅ Events cog loaded")
