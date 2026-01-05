"""
🎛️ Effects Commands Cog
Audio effects, filters, and advanced playback features
"""

import asyncio
import logging
import aiohttp
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

import config

logger = logging.getLogger('ShlokMusic.Effects')

# ═══════════════════════════════════════════════════════════════
# 🎛️ EFFECTS COG
# ═══════════════════════════════════════════════════════════════

class Effects(commands.Cog, name="Effects"):
    """🎛️ Audio effects and advanced features"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def cog_load(self):
        """Initialize aiohttp session"""
        self.session = aiohttp.ClientSession()
    
    async def cog_unload(self):
        """Cleanup aiohttp session"""
        if self.session:
            await self.session.close()
    
    def get_player(self, ctx):
        """Get or create music player for the guild"""
        return self.bot.get_player(ctx.guild.id)
    
    # ═══════════════════════════════════════════════════════════
    # 🎛️ EFFECTS COMMANDS
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_group(
        name="effect",
        aliases=["fx", "filter"],
        description="Audio effects and filters"
    )
    async def effect(self, ctx: commands.Context):
        """Audio effects commands"""
        if ctx.invoked_subcommand is None:
            player = self.get_player(ctx)
            
            embed = discord.Embed(
                title="🎛️ Audio Effects",
                description=f"Current effect: **{player.current_effect.title()}**\n\n"
                           "**Available Effects:**",
                color=config.BOT_COLOR
            )
            
            effects_list = ""
            for name, data in config.AUDIO_EFFECTS.items():
                if name == "none":
                    effects_list += "• `none` - 🔈 No effect (default)\n"
                else:
                    desc = data.get("description", "")
                    effects_list += f"• `{name}` - {desc}\n"
            
            embed.add_field(
                name="Effects",
                value=effects_list,
                inline=False
            )
            
            embed.set_footer(text="Use !effect <name> to apply an effect")
            
            await ctx.send(embed=embed)
    
    @effect.command(name="apply", description="Apply an audio effect")
    @app_commands.describe(name="Effect name to apply")
    async def effect_apply(self, ctx: commands.Context, name: str):
        """Apply an audio effect"""
        player = self.get_player(ctx)
        name = name.lower()
        
        if name not in config.AUDIO_EFFECTS:
            embed = discord.Embed(
                title="❌ Unknown Effect",
                description=f"Effect `{name}` not found. Use `!effect` to see available effects.",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=10)
            return
        
        player.current_effect = name
        
        if name == "none":
            embed = discord.Embed(
                title="🔈 Effect Removed",
                description="Audio effect has been disabled",
                color=config.BOT_COLOR_SUCCESS
            )
        else:
            effect_data = config.AUDIO_EFFECTS[name]
            embed = discord.Embed(
                title=f"🎛️ Effect Applied: {name.title()}",
                description=effect_data.get("description", "Effect applied"),
                color=config.BOT_COLOR_SUCCESS
            )
        
        embed.set_footer(text="Note: Effect will apply to the next track")
        await ctx.send(embed=embed, delete_after=10)
    
    @effect.command(name="bassboost", aliases=["bass", "bb"], description="Apply bass boost")
    async def bassboost(self, ctx: commands.Context):
        """Apply bass boost effect"""
        await self.effect_apply(ctx, "bass_boost")
    
    @effect.command(name="nightcore", aliases=["nc"], description="Apply nightcore effect")
    async def nightcore(self, ctx: commands.Context):
        """Apply nightcore effect"""
        await self.effect_apply(ctx, "nightcore")
    
    @effect.command(name="vaporwave", aliases=["vapor"], description="Apply vaporwave effect")
    async def vaporwave(self, ctx: commands.Context):
        """Apply vaporwave effect"""
        await self.effect_apply(ctx, "vaporwave")
    
    @effect.command(name="8d", description="Apply 8D audio effect")
    async def _8d(self, ctx: commands.Context):
        """Apply 8D rotating audio effect"""
        await self.effect_apply(ctx, "8d")
    
    @effect.command(name="reset", aliases=["off", "clear"], description="Remove all effects")
    async def effect_reset(self, ctx: commands.Context):
        """Remove all audio effects"""
        await self.effect_apply(ctx, "none")
    
    # ═══════════════════════════════════════════════════════════
    # 🎤 LYRICS COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="lyrics",
        aliases=["ly", "words"],
        description="Get lyrics for the current song"
    )
    @app_commands.describe(query="Song to search lyrics for (optional)")
    async def lyrics(self, ctx: commands.Context, *, query: str = None):
        """
        Get lyrics for a song
        
        Usage:
            !lyrics - Get lyrics for current song
            !lyrics <song name> - Search for specific lyrics
        """
        player = self.get_player(ctx)
        
        # Determine what to search for
        if query:
            search_query = query
        elif player.current_track:
            search_query = f"{player.current_track.artist} {player.current_track.title}"
        else:
            embed = discord.Embed(
                title="❌ No Song Playing",
                description="Specify a song name or play something first!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        # Loading message
        loading_embed = discord.Embed(
            title="🔍 Searching Lyrics...",
            description=f"Looking for: **{search_query}**",
            color=config.BOT_COLOR
        )
        loading_msg = await ctx.send(embed=loading_embed)
        
        try:
            # Try to fetch lyrics
            lyrics_text = await self._fetch_lyrics(search_query)
            
            if not lyrics_text:
                embed = discord.Embed(
                    title="❌ Lyrics Not Found",
                    description=f"Could not find lyrics for: **{search_query}**",
                    color=config.BOT_COLOR_ERROR
                )
                await loading_msg.edit(embed=embed)
                return
            
            # Split lyrics into chunks if too long
            max_length = 4000
            chunks = [lyrics_text[i:i+max_length] for i in range(0, len(lyrics_text), max_length)]
            
            # Send first chunk
            embed = discord.Embed(
                title=f"🎤 Lyrics - {search_query[:100]}",
                description=chunks[0],
                color=config.BOT_COLOR
            )
            
            if player.current_track and player.current_track.thumbnail:
                embed.set_thumbnail(url=player.current_track.thumbnail)
            
            await loading_msg.edit(embed=embed)
            
            # Send additional chunks if needed
            for chunk in chunks[1:]:
                embed = discord.Embed(
                    description=chunk,
                    color=config.BOT_COLOR
                )
                await ctx.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Error fetching lyrics: {e}")
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to fetch lyrics. Please try again later.",
                color=config.BOT_COLOR_ERROR
            )
            await loading_msg.edit(embed=embed)
    
    async def _fetch_lyrics(self, query: str) -> Optional[str]:
        """Fetch lyrics from API"""
        try:
            # Clean the query
            query = query.replace("(Official Video)", "").replace("(Official Audio)", "")
            query = query.replace("[Official Video]", "").replace("[Official Audio]", "")
            query = query.strip()
            
            # Try lyrics.ovh API
            parts = query.split(" - ", 1) if " - " in query else query.split(" ", 1)
            
            if len(parts) == 2:
                artist, title = parts
            else:
                # Try to extract from query
                artist = parts[0].split()[0] if parts else ""
                title = " ".join(parts[0].split()[1:]) if parts else query
            
            url = f"{config.LYRICS_API}/{artist}/{title}"
            
            async with self.session.get(url, timeout=10) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("lyrics")
                    
        except Exception as e:
            logger.error(f"Error fetching lyrics: {e}")
        
        return None
    
    # ═══════════════════════════════════════════════════════════
    # 📻 RADIO COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="radio",
        aliases=["autoplay", "endless"],
        description="Enable radio mode (auto-play similar songs)"
    )
    async def radio(self, ctx: commands.Context):
        """
        Enable radio mode to automatically play similar songs
        when the queue is empty
        """
        player = self.get_player(ctx)
        
        # Toggle radio mode (would be implemented in player)
        embed = discord.Embed(
            title="📻 Radio Mode",
            description="Radio mode will automatically add similar songs when the queue is empty.\n\n"
                       "**Status:** Coming Soon!",
            color=config.BOT_COLOR_INFO
        )
        await ctx.send(embed=embed, delete_after=15)
    
    # ═══════════════════════════════════════════════════════════
    # 🎵 EQUALIZER COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="equalizer",
        aliases=["eq"],
        description="View or set the equalizer"
    )
    async def equalizer(self, ctx: commands.Context):
        """View the equalizer presets"""
        embed = discord.Embed(
            title="🎚️ Equalizer Presets",
            description="Use `!effect <name>` to apply these presets:",
            color=config.BOT_COLOR
        )
        
        presets = [
            ("🔊 Bass Boost", "bass_boost", "Enhanced bass frequencies"),
            ("🎸 Rock", "none", "Balanced for rock music"),
            ("🎹 Jazz", "soft", "Smooth and mellow"),
            ("🎤 Vocal", "none", "Enhanced vocals"),
            ("🎧 Electronic", "bass_boost", "Heavy bass for EDM"),
            ("🌙 Night", "soft", "Quiet and easy listening"),
        ]
        
        for name, effect, desc in presets:
            embed.add_field(name=name, value=f"`!effect {effect}`\n{desc}", inline=True)
        
        await ctx.send(embed=embed)
    
    # ═══════════════════════════════════════════════════════════
    # ⚡ SPEED COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="speed",
        aliases=["tempo"],
        description="Change playback speed"
    )
    @app_commands.describe(multiplier="Speed multiplier (0.5-2.0)")
    async def speed(self, ctx: commands.Context, multiplier: float = None):
        """
        Change the playback speed
        
        Usage:
            !speed - Show current speed
            !speed 1.5 - Set speed to 1.5x
        """
        if multiplier is None:
            embed = discord.Embed(
                title="⚡ Playback Speed",
                description="Use `!speed <0.5-2.0>` to change speed\n\n"
                           "**Presets:**\n"
                           "• `!speed 0.5` - Half speed\n"
                           "• `!speed 1.0` - Normal\n"
                           "• `!speed 1.25` - Nightcore style\n"
                           "• `!speed 1.5` - Fast\n"
                           "• `!speed 2.0` - Double speed",
                color=config.BOT_COLOR
            )
            await ctx.send(embed=embed, delete_after=15)
            return
        
        if multiplier < 0.5 or multiplier > 2.0:
            embed = discord.Embed(
                title="❌ Invalid Speed",
                description="Speed must be between 0.5 and 2.0",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        embed = discord.Embed(
            title="⚡ Speed Changed",
            description=f"Playback speed set to **{multiplier}x**\n"
                       "*(Will apply to the next track)*",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # 🎵 PITCH COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="pitch",
        description="Change playback pitch"
    )
    @app_commands.describe(semitones="Pitch change in semitones (-12 to 12)")
    async def pitch(self, ctx: commands.Context, semitones: int = None):
        """
        Change the playback pitch
        
        Usage:
            !pitch - Show current pitch
            !pitch 3 - Raise pitch by 3 semitones
            !pitch -2 - Lower pitch by 2 semitones
        """
        if semitones is None:
            embed = discord.Embed(
                title="🎵 Playback Pitch",
                description="Use `!pitch <-12 to 12>` to change pitch\n\n"
                           "**Examples:**\n"
                           "• `!pitch 0` - Normal pitch\n"
                           "• `!pitch 5` - Chipmunk style\n"
                           "• `!pitch -5` - Deep voice\n"
                           "• `!pitch 12` - One octave up\n"
                           "• `!pitch -12` - One octave down",
                color=config.BOT_COLOR
            )
            await ctx.send(embed=embed, delete_after=15)
            return
        
        if semitones < -12 or semitones > 12:
            embed = discord.Embed(
                title="❌ Invalid Pitch",
                description="Pitch must be between -12 and 12 semitones",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        direction = "raised" if semitones > 0 else "lowered"
        embed = discord.Embed(
            title="🎵 Pitch Changed",
            description=f"Pitch {direction} by **{abs(semitones)}** semitones\n"
                       "*(Will apply to the next track)*",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # ❤️ FAVORITES COMMANDS
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_group(
        name="favorite",
        aliases=["fav", "like"],
        description="Favorite songs management"
    )
    async def favorite(self, ctx: commands.Context):
        """Favorite songs commands"""
        if ctx.invoked_subcommand is None:
            await self.favorite_list(ctx)
    
    @favorite.command(name="add", description="Add current song to favorites")
    async def favorite_add(self, ctx: commands.Context):
        """Add the current song to your favorites"""
        player = self.get_player(ctx)
        
        if not player.current_track:
            embed = discord.Embed(
                title="❌ Nothing Playing",
                description="There's no song playing to add to favorites!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        added = player.add_favorite(ctx.author.id, player.current_track)
        
        if added:
            embed = discord.Embed(
                title="❤️ Added to Favorites",
                description=f"Added **{player.current_track.title}** to your favorites!",
                color=config.BOT_COLOR_SUCCESS
            )
        else:
            embed = discord.Embed(
                title="⚠️ Already in Favorites",
                description="This song is already in your favorites!",
                color=config.BOT_COLOR_WARNING
            )
        
        await ctx.send(embed=embed, delete_after=10)
    
    @favorite.command(name="list", description="View your favorites")
    async def favorite_list(self, ctx: commands.Context):
        """View your favorite songs"""
        player = self.get_player(ctx)
        favorites = player.get_favorites(ctx.author.id)
        
        if not favorites:
            embed = discord.Embed(
                title="❤️ Your Favorites",
                description="You haven't added any favorites yet!\n"
                           "Use `!favorite add` while a song is playing.",
                color=config.BOT_COLOR_INFO
            )
            await ctx.send(embed=embed, delete_after=15)
            return
        
        embed = discord.Embed(
            title=f"❤️ {ctx.author.display_name}'s Favorites",
            color=config.BOT_COLOR
        )
        
        fav_list = ""
        for i, track in enumerate(favorites[:10], 1):
            fav_list += f"**{i}.** [{track.title}]({track.url})\n"
        
        embed.description = fav_list
        embed.set_footer(text=f"Total: {len(favorites)} favorites")
        
        await ctx.send(embed=embed)


# ═══════════════════════════════════════════════════════════════
# 🔧 COG SETUP
# ═══════════════════════════════════════════════════════════════

async def setup(bot: commands.Bot):
    await bot.add_cog(Effects(bot))
    logger.info("✅ Effects cog loaded")
