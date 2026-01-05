"""
🔧 Utility Commands Cog
Help, stats, and utility commands for Shlok Music Bot
"""

import logging
import platform
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

import config

logger = logging.getLogger('ShlokMusic.Utility')

class Utility(commands.Cog, name="Utility"):
    """🔧 Help, stats, and utility commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    @commands.hybrid_command(name="help", aliases=["h", "commands"], description="Show all commands")
    @app_commands.describe(command="Specific command to get help for")
    async def help(self, ctx: commands.Context, command: str = None):
        """Show help for all commands"""
        
        if command:
            cmd = self.bot.get_command(command)
            if not cmd:
                return await ctx.send(f"❌ Command `{command}` not found!", delete_after=10)
            
            embed = discord.Embed(
                title=f"📖 Help: {cmd.name}",
                description=cmd.help or cmd.description or "No description",
                color=config.BOT_COLOR
            )
            
            usage = f"!{cmd.name}"
            if cmd.signature:
                usage += f" {cmd.signature}"
            embed.add_field(name="Usage", value=f"`{usage}`", inline=False)
            
            if cmd.aliases:
                embed.add_field(name="Aliases", value=", ".join([f"`{a}`" for a in cmd.aliases]), inline=False)
            
            return await ctx.send(embed=embed)
        
        embed = discord.Embed(
            title="🎵 Shlok Music Bot - Commands",
            description=f"**Prefixes:** `$` or `/` (also works with `!`, `s!`, or @mention)\n"
                       f"Use `$help <command>` for detailed info",
            color=config.BOT_COLOR
        )
        
        # Music Commands
        embed.add_field(
            name="🎵 Music",
            value="`play` `pause` `resume` `skip` `stop` `previous` `seek` `nowplaying`",
            inline=False
        )
        
        # Queue Commands
        embed.add_field(
            name="📋 Queue",
            value="`queue` `shuffle` `loop` `clear` `search`",
            inline=False
        )
        
        # Voice Commands
        embed.add_field(
            name="🔊 Voice",
            value="`join` `leave` `volume`",
            inline=False
        )
        
        # Effects Commands
        embed.add_field(
            name="🎛️ Effects",
            value="`bassboost` `nightcore` `vaporwave` `resetfilter`",
            inline=False
        )
        
        # Utility Commands
        embed.add_field(
            name="🔧 Utility",
            value="`help` `ping` `stats` `invite`",
            inline=False
        )
        
        # Reaction controls
        embed.add_field(
            name="🎮 Reaction Controls",
            value="React to the Now Playing message:\n"
                  "⏮️ Previous • ⏯️ Pause/Resume • ⏭️ Skip • ⏹️ Stop\n"
                  "🔀 Shuffle • 🔁 Loop Queue • 🔂 Loop Track\n"
                  "🔉 Vol- • 🔊 Vol+",
            inline=False
        )
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="🎵 High-Quality Music Streaming • 24/7 Online")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="ping", description="Check bot latency")
    async def ping(self, ctx: commands.Context):
        """Check the bot's latency"""
        latency = round(self.bot.latency * 1000)
        
        if latency < 100:
            emoji = "🟢"
            status = "Excellent"
        elif latency < 200:
            emoji = "🟡"
            status = "Good"
        else:
            emoji = "🔴"
            status = "High"
        
        embed = discord.Embed(
            title="🏓 Pong!",
            description=f"{emoji} **{latency}ms** ({status})",
            color=config.BOT_COLOR
        )
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="stats", aliases=["info", "about"], description="Show bot statistics")
    async def stats(self, ctx: commands.Context):
        """Show bot statistics"""
        
        # Calculate uptime
        if self.bot.start_time:
            uptime = datetime.now() - self.bot.start_time
            hours, remainder = divmod(int(uptime.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            uptime_str = f"{hours}h {minutes}m {seconds}s"
        else:
            uptime_str = "Unknown"
        
        embed = discord.Embed(
            title="📊 Shlok Music Bot - Statistics",
            color=config.BOT_COLOR
        )
        
        embed.add_field(name="📡 Servers", value=f"{len(self.bot.guilds)}", inline=True)
        embed.add_field(name="👥 Users", value=f"{sum(g.member_count for g in self.bot.guilds):,}", inline=True)
        embed.add_field(name="🏓 Latency", value=f"{round(self.bot.latency * 1000)}ms", inline=True)
        embed.add_field(name="⏱️ Uptime", value=uptime_str, inline=True)
        embed.add_field(name="🎧 Voice", value=f"{len(self.bot.voice_clients)} active", inline=True)
        embed.add_field(name="🐍 Python", value=platform.python_version(), inline=True)
        embed.add_field(name="📚 discord.py", value=discord.__version__, inline=True)
        embed.add_field(name="💻 Platform", value=platform.system(), inline=True)
        embed.add_field(name="🎵 Audio", value="Wavelink/Lavalink", inline=True)
        
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        embed.set_footer(text="🎵 24/7 High-Quality Music Streaming")
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="invite", description="Get bot invite link")
    async def invite(self, ctx: commands.Context):
        """Get the bot's invite link"""
        
        invite_url = f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=3214336&scope=bot%20applications.commands"
        
        embed = discord.Embed(
            title="🔗 Invite Shlok Music Bot",
            description=f"[**Click here to invite me!**]({invite_url})\n\n"
                       f"Thanks for choosing Shlok Music! 🎵",
            color=config.BOT_COLOR
        )
        embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        
        await ctx.send(embed=embed)
    
    @commands.hybrid_command(name="support", description="Get support server link")
    async def support(self, ctx: commands.Context):
        """Get support information"""
        
        embed = discord.Embed(
            title="💬 Support",
            description="Need help with Shlok Music Bot?\n\n"
                       "• Use `!help` to see all commands\n"
                       "• Use `!help <command>` for specific help\n"
                       "• Make sure the bot has proper permissions\n"
                       "• Check if you're in a voice channel",
            color=config.BOT_COLOR
        )
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Utility(bot))
    logger.info("✅ Utility cog loaded")
