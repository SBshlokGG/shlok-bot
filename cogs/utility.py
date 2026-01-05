"""
🔧 Utility Commands Cog
Help, stats, settings, and other utility commands
"""

import asyncio
import logging
import platform
from datetime import datetime
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

import config

logger = logging.getLogger('ShlokMusic.Utility')

# ═══════════════════════════════════════════════════════════════
# 🔧 UTILITY COG
# ═══════════════════════════════════════════════════════════════

class Utility(commands.Cog, name="Utility"):
    """🔧 Help, stats, and utility commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    # ═══════════════════════════════════════════════════════════
    # ❓ HELP COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="help",
        aliases=["h", "commands", "cmds"],
        description="Show all available commands"
    )
    @app_commands.describe(command="Specific command to get help for")
    async def help(self, ctx: commands.Context, command: str = None):
        """
        Show help for all commands or a specific command
        
        Usage:
            !help - Show all commands
            !help play - Show help for play command
        """
        if command:
            # Show help for specific command
            cmd = self.bot.get_command(command)
            if not cmd:
                embed = discord.Embed(
                    title="❌ Command Not Found",
                    description=f"Command `{command}` not found. Use `!help` to see all commands.",
                    color=config.BOT_COLOR_ERROR
                )
                await ctx.send(embed=embed, delete_after=10)
                return
            
            embed = discord.Embed(
                title=f"📖 Help: {cmd.name}",
                description=cmd.help or "No description available.",
                color=config.BOT_COLOR
            )
            
            # Usage
            usage = f"!{cmd.name}"
            if cmd.signature:
                usage += f" {cmd.signature}"
            embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
            
            # Aliases
            if cmd.aliases:
                embed.add_field(
                    name="Aliases",
                    value=", ".join([f"`{a}`" for a in cmd.aliases]),
                    inline=False
                )
            
            await ctx.send(embed=embed)
            return
        
        # Show all commands
        embed = discord.Embed(
            title="🎵 Shlok Music - Commands",
            description=f"**Prefix:** `{config.BOT_PREFIX}` or mention me\n"
                       f"Use `{config.BOT_PREFIX}help <command>` for detailed info\n\n"
                       f"**Reaction Controls:** React to the Now Playing message!",
            color=config.BOT_COLOR
        )
        
        # Music commands
        music_cmds = [
            ("`play`", "Play a song"),
            ("`search`", "Search and choose"),
            ("`pause`", "Pause playback"),
            ("`resume`", "Resume playback"),
            ("`skip`", "Skip current track"),
            ("`previous`", "Previous track"),
            ("`stop`", "Stop & clear queue"),
            ("`nowplaying`", "Show current track"),
            ("`volume`", "Set volume (0-150)"),
            ("`loop`", "Toggle loop mode"),
            ("`playnow`", "Play immediately"),
            ("`seek`", "Seek in track"),
        ]
        embed.add_field(
            name="🎵 Music",
            value="\n".join([f"{c[0]} - {c[1]}" for c in music_cmds]),
            inline=True
        )
        
        # Queue commands
        queue_cmds = [
            ("`queue`", "View queue"),
            ("`shuffle`", "Shuffle queue"),
            ("`clear`", "Clear queue"),
            ("`remove`", "Remove track"),
            ("`move`", "Move track"),
            ("`skipto`", "Skip to position"),
            ("`playnext`", "Add to play next"),
            ("`reverse`", "Reverse queue"),
            ("`removedupes`", "Remove duplicates"),
            ("`sort`", "Sort queue"),
        ]
        embed.add_field(
            name="📋 Queue",
            value="\n".join([f"{c[0]} - {c[1]}" for c in queue_cmds]),
            inline=True
        )
        
        # Effects & Utility commands
        other_cmds = [
            ("`effect`", "Audio effects"),
            ("`lyrics`", "Get lyrics"),
            ("`equalizer`", "EQ presets"),
            ("`speed`", "Change speed"),
            ("`pitch`", "Change pitch"),
            ("`favorite`", "Manage favorites"),
            ("`join`", "Join voice"),
            ("`leave`", "Leave voice"),
            ("`stats`", "Bot statistics"),
            ("`ping`", "Check latency"),
            ("`invite`", "Invite link"),
        ]
        embed.add_field(
            name="🎛️ Effects & Utility",
            value="\n".join([f"{c[0]} - {c[1]}" for c in other_cmds]),
            inline=True
        )
        
        # Reaction controls info
        embed.add_field(
            name="🎮 Reaction Controls",
            value=(
                "⏮️ Previous • ⏯️ Pause/Resume • ⏭️ Skip • ⏹️ Stop\n"
                "🔀 Shuffle • 🔁 Loop Queue • 🔂 Loop Track\n"
                "🔉 Vol- • 🔊 Vol+ • ❤️ Favorite • 📋 Queue • 🎵 Lyrics"
            ),
            inline=False
        )
        
        embed.set_footer(
            text=f"Requested by {ctx.author.display_name}",
            icon_url=ctx.author.display_avatar.url
        )
        
        await ctx.send(embed=embed)
    
    # ═══════════════════════════════════════════════════════════
    # 📊 STATS COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="stats",
        aliases=["statistics", "info", "botinfo"],
        description="Show bot statistics"
    )
    async def stats(self, ctx: commands.Context):
        """Show detailed bot statistics"""
        # Calculate uptime
        if self.bot.start_time:
            uptime = datetime.now() - self.bot.start_time
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{days}d {hours}h {minutes}m {seconds}s"
        else:
            uptime_str = "Unknown"
        
        # Count voice connections
        voice_connections = sum(1 for p in self.bot.music_players.values() if p.is_connected)
        
        # Count total queue size
        total_queue = sum(len(p.queue) for p in self.bot.music_players.values())
        
        embed = discord.Embed(
            title="📊 Shlok Music Statistics",
            color=config.BOT_COLOR
        )
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        # Bot info
        embed.add_field(
            name="🤖 Bot Info",
            value=(
                f"**Name:** {self.bot.user.name}\n"
                f"**ID:** {self.bot.user.id}\n"
                f"**Uptime:** {uptime_str}"
            ),
            inline=True
        )
        
        # Server stats
        embed.add_field(
            name="📈 Server Stats",
            value=(
                f"**Servers:** {len(self.bot.guilds):,}\n"
                f"**Users:** {sum(g.member_count for g in self.bot.guilds):,}\n"
                f"**Voice Connections:** {voice_connections}"
            ),
            inline=True
        )
        
        # Music stats
        embed.add_field(
            name="🎵 Music Stats",
            value=(
                f"**Songs Played:** {self.bot.songs_played:,}\n"
                f"**Commands Used:** {self.bot.commands_used:,}\n"
                f"**Queue Size:** {total_queue:,}"
            ),
            inline=True
        )
        
        # System info
        embed.add_field(
            name="💻 System",
            value=(
                f"**Python:** {platform.python_version()}\n"
                f"**Discord.py:** {discord.__version__}\n"
                f"**OS:** {platform.system()}"
            ),
            inline=True
        )
        
        # Latency
        embed.add_field(
            name="📡 Connection",
            value=(
                f"**Latency:** {round(self.bot.latency * 1000)}ms\n"
                f"**Shards:** {self.bot.shard_count or 1}\n"
                f"**24/7 Mode:** {'✅ On' if config.MUSIC.stay_connected_24_7 else '❌ Off'}"
            ),
            inline=True
        )
        
        # Features
        embed.add_field(
            name="✨ Features",
            value=(
                "• High-quality streaming\n"
                "• Reaction controls\n"
                "• Audio effects\n"
                "• Advanced queue\n"
                "• Lyrics support\n"
                "• 24/7 playback"
            ),
            inline=True
        )
        
        embed.set_footer(text=f"Thanks for using {config.BOT_NAME}!")
        
        await ctx.send(embed=embed)
    
    # ═══════════════════════════════════════════════════════════
    # 🏓 PING COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="ping",
        aliases=["latency", "pong"],
        description="Check bot latency"
    )
    async def ping(self, ctx: commands.Context):
        """Check the bot's latency"""
        # Calculate latencies
        ws_latency = round(self.bot.latency * 1000)
        
        # Message latency
        start = datetime.now()
        msg = await ctx.send("🏓 Pinging...")
        end = datetime.now()
        msg_latency = round((end - start).total_seconds() * 1000)
        
        # Create status indicator
        if ws_latency < 100:
            status = "🟢 Excellent"
        elif ws_latency < 200:
            status = "🟡 Good"
        else:
            status = "🔴 High"
        
        embed = discord.Embed(
            title="🏓 Pong!",
            color=config.BOT_COLOR_SUCCESS if ws_latency < 200 else config.BOT_COLOR_WARNING
        )
        
        embed.add_field(
            name="📡 WebSocket",
            value=f"`{ws_latency}ms`",
            inline=True
        )
        embed.add_field(
            name="📨 Message",
            value=f"`{msg_latency}ms`",
            inline=True
        )
        embed.add_field(
            name="📊 Status",
            value=status,
            inline=True
        )
        
        await msg.edit(content=None, embed=embed)
    
    # ═══════════════════════════════════════════════════════════
    # 🔗 INVITE COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="invite",
        aliases=["inv", "addbot"],
        description="Get the bot invite link"
    )
    async def invite(self, ctx: commands.Context):
        """Get the bot's invite link"""
        # Generate invite URL with necessary permissions
        permissions = discord.Permissions(
            connect=True,
            speak=True,
            read_messages=True,
            send_messages=True,
            embed_links=True,
            add_reactions=True,
            read_message_history=True,
            use_voice_activation=True,
        )
        
        invite_url = discord.utils.oauth_url(
            self.bot.user.id,
            permissions=permissions,
            scopes=["bot", "applications.commands"]
        )
        
        embed = discord.Embed(
            title="🔗 Invite Shlok Music",
            description=(
                f"Click the button below to add me to your server!\n\n"
                f"**[Invite Bot]({invite_url})**\n\n"
                f"**Required Permissions:**\n"
                f"• Connect to Voice Channels\n"
                f"• Speak in Voice Channels\n"
                f"• Send Messages\n"
                f"• Embed Links\n"
                f"• Add Reactions"
            ),
            color=config.BOT_COLOR
        )
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        # Create button view
        view = discord.ui.View()
        view.add_item(discord.ui.Button(
            label="Invite Bot",
            url=invite_url,
            style=discord.ButtonStyle.link,
            emoji="🎵"
        ))
        
        await ctx.send(embed=embed, view=view)
    
    # ═══════════════════════════════════════════════════════════
    # 💬 SUPPORT COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="support",
        aliases=["server", "discord"],
        description="Get support server link"
    )
    async def support(self, ctx: commands.Context):
        """Get the support server link"""
        embed = discord.Embed(
            title="💬 Need Help?",
            description=(
                "**For Support:**\n"
                "• Use `!help <command>` for command help\n"
                "• Check if you have the right permissions\n"
                "• Make sure the bot has voice permissions\n\n"
                "**Common Issues:**\n"
                "• Bot not joining? Check voice permissions\n"
                "• No sound? Check volume and deafen status\n"
                "• Commands not working? Check prefix"
            ),
            color=config.BOT_COLOR
        )
        
        await ctx.send(embed=embed)
    
    # ═══════════════════════════════════════════════════════════
    # ⚙️ SETTINGS COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_group(
        name="settings",
        aliases=["config", "set"],
        description="Bot settings"
    )
    @commands.has_permissions(manage_guild=True)
    async def settings(self, ctx: commands.Context):
        """View or modify bot settings"""
        if ctx.invoked_subcommand is None:
            player = self.bot.get_player(ctx.guild.id)
            
            embed = discord.Embed(
                title="⚙️ Server Settings",
                description="Use `!settings <option> <value>` to change settings",
                color=config.BOT_COLOR
            )
            
            embed.add_field(
                name="🔊 Volume",
                value=f"`{int(player.volume * 100)}%`",
                inline=True
            )
            embed.add_field(
                name="🔄 24/7 Mode",
                value=f"{'`On`' if player.stay_connected else '`Off`'}",
                inline=True
            )
            embed.add_field(
                name="🔁 Loop Mode",
                value=f"`{player.loop_mode.name.title()}`",
                inline=True
            )
            
            embed.add_field(
                name="📝 Available Settings",
                value=(
                    "`!settings 247 on/off` - Toggle 24/7 mode\n"
                    "`!settings volume <0-150>` - Default volume\n"
                    "`!settings dj <role>` - Set DJ role"
                ),
                inline=False
            )
            
            await ctx.send(embed=embed)
    
    @settings.command(name="247", description="Toggle 24/7 mode")
    @commands.has_permissions(manage_guild=True)
    async def settings_247(self, ctx: commands.Context, mode: str):
        """Toggle 24/7 mode"""
        player = self.bot.get_player(ctx.guild.id)
        
        if mode.lower() in ["on", "enable", "true", "yes"]:
            player.stay_connected = True
            embed = discord.Embed(
                title="✅ 24/7 Mode Enabled",
                description="I'll stay in the voice channel even when no one else is there!",
                color=config.BOT_COLOR_SUCCESS
            )
        elif mode.lower() in ["off", "disable", "false", "no"]:
            player.stay_connected = False
            embed = discord.Embed(
                title="❌ 24/7 Mode Disabled",
                description="I'll disconnect when the channel is empty.",
                color=config.BOT_COLOR
            )
        else:
            embed = discord.Embed(
                title="❌ Invalid Option",
                description="Use `on` or `off`",
                color=config.BOT_COLOR_ERROR
            )
        
        await ctx.send(embed=embed, delete_after=10)
    
    @settings.command(name="volume", description="Set default volume")
    @commands.has_permissions(manage_guild=True)
    async def settings_volume(self, ctx: commands.Context, level: int):
        """Set default volume"""
        if level < 0 or level > 150:
            embed = discord.Embed(
                title="❌ Invalid Volume",
                description="Volume must be between 0 and 150!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        player = self.bot.get_player(ctx.guild.id)
        player.set_volume(level)
        
        embed = discord.Embed(
            title="🔊 Default Volume Set",
            description=f"Default volume set to **{level}%**",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # 🧹 CLEANUP COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="cleanup",
        aliases=["clean", "purge"],
        description="Clean up bot messages"
    )
    @commands.has_permissions(manage_messages=True)
    async def cleanup(self, ctx: commands.Context, amount: int = 50):
        """
        Clean up bot messages in the channel
        
        Usage:
            !cleanup - Delete last 50 bot messages
            !cleanup 100 - Delete last 100 bot messages
        """
        amount = min(amount, 100)  # Cap at 100
        
        def is_bot_message(msg):
            return msg.author == self.bot.user
        
        try:
            deleted = await ctx.channel.purge(limit=amount, check=is_bot_message)
            
            embed = discord.Embed(
                title="🧹 Cleanup Complete",
                description=f"Deleted **{len(deleted)}** bot messages.",
                color=config.BOT_COLOR_SUCCESS
            )
            await ctx.send(embed=embed, delete_after=5)
            
        except discord.Forbidden:
            embed = discord.Embed(
                title="❌ Missing Permissions",
                description="I need `Manage Messages` permission to do that!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)


# ═══════════════════════════════════════════════════════════════
# 🔧 COG SETUP
# ═══════════════════════════════════════════════════════════════

async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
    logger.info("✅ Utility cog loaded")
