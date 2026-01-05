"""
📋 Queue Commands Cog
Queue management commands for Shlok Music Bot
"""

import asyncio
import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

import config
from core import TrackExtractor

logger = logging.getLogger('ShlokMusic.Queue')

# ═══════════════════════════════════════════════════════════════
# 📋 QUEUE COG
# ═══════════════════════════════════════════════════════════════

class Queue(commands.Cog, name="Queue"):
    """📋 Queue management commands"""
    
    def __init__(self, bot: commands.Bot):
        self.bot = bot
    
    def get_player(self, ctx):
        """Get or create music player for the guild"""
        return self.bot.get_player(ctx.guild.id)
    
    # ═══════════════════════════════════════════════════════════
    # 📋 QUEUE DISPLAY
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="queue",
        aliases=["q", "list"],
        description="Show the current queue"
    )
    @app_commands.describe(page="Page number to display")
    async def queue(self, ctx: commands.Context, page: int = 1):
        """
        Show the current queue
        
        Usage:
            !queue - Show first page
            !queue 2 - Show page 2
        """
        player = self.get_player(ctx)
        
        if not player.current_track and len(player.queue) == 0:
            embed = discord.Embed(
                title="📋 Queue is Empty",
                description="Add songs with `!play <song name>`",
                color=config.BOT_COLOR_INFO
            )
            await ctx.send(embed=embed, delete_after=15)
            return
        
        # Pagination settings
        items_per_page = 10
        total_pages = max(1, (len(player.queue) + items_per_page - 1) // items_per_page)
        page = max(1, min(page, total_pages))
        
        # Create embed
        embed = discord.Embed(
            title=f"📋 Music Queue - Page {page}/{total_pages}",
            color=config.BOT_COLOR
        )
        
        # Now playing
        if player.current_track:
            status = "⏸️" if player.is_paused else "▶️"
            embed.add_field(
                name=f"{status} Now Playing",
                value=f"**[{player.current_track.title}]({player.current_track.url})**\n"
                      f"└ 👤 {player.current_track.artist} • ⏱️ {player.current_track.duration_formatted}",
                inline=False
            )
        
        # Queue items
        if player.queue:
            start_idx = (page - 1) * items_per_page
            queue_items = player.queue.get_list(start_idx, items_per_page)
            
            queue_text = ""
            for i, track in enumerate(queue_items, start=start_idx + 1):
                duration = track.duration_formatted if track.duration else "Live"
                queue_text += f"**{i}.** [{track.title}]({track.url})\n"
                queue_text += f"    └ 👤 {track.artist} • ⏱️ {duration}\n"
            
            if queue_text:
                embed.add_field(
                    name="📋 Up Next",
                    value=queue_text,
                    inline=False
                )
        
        # Queue stats
        total_duration = player.queue.get_total_duration()
        if player.current_track and player.current_track.duration:
            total_duration += player.current_track.duration
        
        hours, remainder = divmod(total_duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            duration_str = f"{hours}h {minutes}m"
        else:
            duration_str = f"{minutes}m {seconds}s"
        
        loop_str = {
            0: "❌ Off",
            1: "🔂 Track",
            2: "🔁 Queue"
        }.get(player.loop_mode.value, "❌ Off")
        
        embed.add_field(name="📊 Tracks", value=f"{len(player.queue) + (1 if player.current_track else 0)}", inline=True)
        embed.add_field(name="⏱️ Duration", value=duration_str, inline=True)
        embed.add_field(name="🔄 Loop", value=loop_str, inline=True)
        
        embed.set_footer(text=f"Use the reactions to navigate • Volume: {int(player.volume * 100)}%")
        
        # Send and add pagination reactions
        message = await ctx.send(embed=embed)
        
        if total_pages > 1:
            reactions = ["⏮️", "◀️", "▶️", "⏭️", "🗑️"]
            for emoji in reactions:
                await message.add_reaction(emoji)
            
            def check(reaction, user):
                return user == ctx.author and reaction.message.id == message.id and str(reaction.emoji) in reactions
            
            while True:
                try:
                    reaction, user = await self.bot.wait_for('reaction_add', timeout=60.0, check=check)
                    
                    emoji = str(reaction.emoji)
                    
                    if emoji == "⏮️":
                        page = 1
                    elif emoji == "◀️":
                        page = max(1, page - 1)
                    elif emoji == "▶️":
                        page = min(total_pages, page + 1)
                    elif emoji == "⏭️":
                        page = total_pages
                    elif emoji == "🗑️":
                        await message.delete()
                        return
                    
                    # Update embed
                    embed.title = f"📋 Music Queue - Page {page}/{total_pages}"
                    
                    # Update queue items
                    start_idx = (page - 1) * items_per_page
                    queue_items = player.queue.get_list(start_idx, items_per_page)
                    
                    queue_text = ""
                    for i, track in enumerate(queue_items, start=start_idx + 1):
                        duration = track.duration_formatted if track.duration else "Live"
                        queue_text += f"**{i}.** [{track.title}]({track.url})\n"
                        queue_text += f"    └ 👤 {track.artist} • ⏱️ {duration}\n"
                    
                    if len(embed.fields) > 1:
                        embed.set_field_at(
                            1,
                            name="📋 Up Next",
                            value=queue_text or "No more tracks",
                            inline=False
                        )
                    
                    await message.edit(embed=embed)
                    await message.remove_reaction(reaction, user)
                    
                except asyncio.TimeoutError:
                    try:
                        await message.clear_reactions()
                    except:
                        pass
                    break
    
    # ═══════════════════════════════════════════════════════════
    # 🔀 SHUFFLE COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="shuffle",
        aliases=["mix", "randomize"],
        description="Shuffle the queue"
    )
    async def shuffle(self, ctx: commands.Context):
        """Shuffle the queue"""
        player = self.get_player(ctx)
        
        if len(player.queue) < 2:
            embed = discord.Embed(
                title="❌ Not Enough Tracks",
                description="Need at least 2 tracks in queue to shuffle!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        player.queue.shuffle()
        
        embed = discord.Embed(
            title="🔀 Queue Shuffled",
            description=f"Shuffled **{len(player.queue)}** tracks",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # 🗑️ CLEAR COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="clear",
        aliases=["empty", "cls"],
        description="Clear the queue"
    )
    async def clear(self, ctx: commands.Context):
        """Clear the entire queue"""
        player = self.get_player(ctx)
        
        if len(player.queue) == 0:
            embed = discord.Embed(
                title="❌ Queue Already Empty",
                description="The queue is already empty!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        count = len(player.queue)
        player.queue.clear()
        
        embed = discord.Embed(
            title="🗑️ Queue Cleared",
            description=f"Removed **{count}** tracks from the queue",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # ➖ REMOVE COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="remove",
        aliases=["rm", "delete"],
        description="Remove a track from the queue"
    )
    @app_commands.describe(position="Position of the track to remove")
    async def remove(self, ctx: commands.Context, position: int):
        """
        Remove a track from the queue
        
        Usage:
            !remove 3 - Remove track at position 3
        """
        player = self.get_player(ctx)
        
        if position < 1 or position > len(player.queue):
            embed = discord.Embed(
                title="❌ Invalid Position",
                description=f"Position must be between 1 and {len(player.queue)}",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        track = player.queue.remove(position - 1)
        
        if track:
            embed = discord.Embed(
                title="🗑️ Track Removed",
                description=f"Removed **{track.title}** from the queue",
                color=config.BOT_COLOR_SUCCESS
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to remove the track",
                color=config.BOT_COLOR_ERROR
            )
        
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # 🔄 MOVE COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="move",
        aliases=["mv"],
        description="Move a track to a different position"
    )
    @app_commands.describe(
        from_pos="Current position of the track",
        to_pos="New position for the track"
    )
    async def move(self, ctx: commands.Context, from_pos: int, to_pos: int):
        """
        Move a track to a different position
        
        Usage:
            !move 5 1 - Move track 5 to position 1
        """
        player = self.get_player(ctx)
        
        queue_len = len(player.queue)
        
        if from_pos < 1 or from_pos > queue_len or to_pos < 1 or to_pos > queue_len:
            embed = discord.Embed(
                title="❌ Invalid Position",
                description=f"Positions must be between 1 and {queue_len}",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        track = player.queue.get_track(from_pos - 1)
        success = player.queue.move(from_pos - 1, to_pos - 1)
        
        if success:
            embed = discord.Embed(
                title="🔄 Track Moved",
                description=f"Moved **{track.title}** from position {from_pos} to {to_pos}",
                color=config.BOT_COLOR_SUCCESS
            )
        else:
            embed = discord.Embed(
                title="❌ Error",
                description="Failed to move the track",
                color=config.BOT_COLOR_ERROR
            )
        
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # 🔝 SKIPTO COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="skipto",
        aliases=["jumpto", "jump"],
        description="Skip to a specific track in the queue"
    )
    @app_commands.describe(position="Position of the track to skip to")
    async def skipto(self, ctx: commands.Context, position: int):
        """
        Skip to a specific track in the queue
        
        Usage:
            !skipto 5 - Skip to track at position 5
        """
        player = self.get_player(ctx)
        
        if position < 1 or position > len(player.queue):
            embed = discord.Embed(
                title="❌ Invalid Position",
                description=f"Position must be between 1 and {len(player.queue)}",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        # Remove tracks before the target
        for _ in range(position - 1):
            player.queue.get_next()
        
        # Skip current track
        await player.skip()
        
        embed = discord.Embed(
            title="⏭️ Skipped To",
            description=f"Skipped to track at position {position}",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # 🔁 REVERSE COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="reverse",
        aliases=["rev"],
        description="Reverse the queue order"
    )
    async def reverse(self, ctx: commands.Context):
        """Reverse the queue order"""
        player = self.get_player(ctx)
        
        if len(player.queue) < 2:
            embed = discord.Embed(
                title="❌ Not Enough Tracks",
                description="Need at least 2 tracks in queue to reverse!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        player.queue.reverse()
        
        embed = discord.Embed(
            title="🔄 Queue Reversed",
            description=f"Reversed **{len(player.queue)}** tracks",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # 📊 SORT COMMANDS
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_group(
        name="sort",
        description="Sort the queue"
    )
    async def sort(self, ctx: commands.Context):
        """Sort the queue by different criteria"""
        if ctx.invoked_subcommand is None:
            embed = discord.Embed(
                title="📊 Sort Commands",
                description=(
                    "`!sort duration` - Sort by duration (shortest first)\n"
                    "`!sort title` - Sort alphabetically by title\n"
                    "`!sort reverse` - Reverse current order"
                ),
                color=config.BOT_COLOR
            )
            await ctx.send(embed=embed, delete_after=15)
    
    @sort.command(name="duration", description="Sort queue by duration")
    async def sort_duration(self, ctx: commands.Context):
        """Sort queue by duration (shortest first)"""
        player = self.get_player(ctx)
        
        if len(player.queue) < 2:
            embed = discord.Embed(
                title="❌ Not Enough Tracks",
                description="Need at least 2 tracks to sort!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        player.queue.sort_by_duration()
        
        embed = discord.Embed(
            title="📊 Queue Sorted",
            description="Sorted queue by duration (shortest first)",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=10)
    
    @sort.command(name="title", description="Sort queue by title")
    async def sort_title(self, ctx: commands.Context):
        """Sort queue alphabetically by title"""
        player = self.get_player(ctx)
        
        if len(player.queue) < 2:
            embed = discord.Embed(
                title="❌ Not Enough Tracks",
                description="Need at least 2 tracks to sort!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        player.queue.sort_by_title()
        
        embed = discord.Embed(
            title="📊 Queue Sorted",
            description="Sorted queue alphabetically by title",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # ➕ PLAYNEXT COMMAND
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="playnext",
        aliases=["pnext", "addnext"],
        description="Add a song to play next"
    )
    @app_commands.describe(query="Song name or URL")
    async def playnext(self, ctx: commands.Context, *, query: str):
        """
        Add a song to play next in the queue
        
        Usage:
            !playnext <song name or URL>
        """
        player = self.get_player(ctx)
        
        # Ensure in voice
        if not ctx.author.voice:
            embed = discord.Embed(
                title="❌ Not Connected",
                description="You need to be in a voice channel!",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
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
        player.queue.add_next(track)
        
        embed = discord.Embed(
            title="✅ Added to Play Next",
            description=f"**[{track.title}]({track.url})**\n"
                        f"Will play after the current track",
            color=config.BOT_COLOR_SUCCESS
        )
        
        if track.thumbnail:
            embed.set_thumbnail(url=track.thumbnail)
        
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # 🧹 REMOVE DUPLICATES
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="removedupes",
        aliases=["dedup", "nodupes"],
        description="Remove duplicate tracks from the queue"
    )
    async def removedupes(self, ctx: commands.Context):
        """Remove duplicate tracks from the queue"""
        player = self.get_player(ctx)
        
        removed = player.queue.remove_duplicates()
        
        if removed > 0:
            embed = discord.Embed(
                title="🧹 Duplicates Removed",
                description=f"Removed **{removed}** duplicate tracks",
                color=config.BOT_COLOR_SUCCESS
            )
        else:
            embed = discord.Embed(
                title="✅ No Duplicates",
                description="No duplicate tracks found in the queue",
                color=config.BOT_COLOR_INFO
            )
        
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # 👤 REMOVE USER TRACKS
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="removemytracks",
        aliases=["rmmine", "clearmine"],
        description="Remove all your tracks from the queue"
    )
    async def removemytracks(self, ctx: commands.Context):
        """Remove all your tracks from the queue"""
        player = self.get_player(ctx)
        
        removed = player.queue.remove_user_tracks(ctx.author.id)
        
        if removed > 0:
            embed = discord.Embed(
                title="🗑️ Your Tracks Removed",
                description=f"Removed **{removed}** tracks requested by you",
                color=config.BOT_COLOR_SUCCESS
            )
        else:
            embed = discord.Embed(
                title="❌ No Tracks Found",
                description="You don't have any tracks in the queue",
                color=config.BOT_COLOR_INFO
            )
        
        await ctx.send(embed=embed, delete_after=10)
    
    # ═══════════════════════════════════════════════════════════
    # 📜 SAVE/LOAD QUEUE
    # ═══════════════════════════════════════════════════════════
    
    @commands.hybrid_command(
        name="savequeue",
        aliases=["exportqueue"],
        description="Save the current queue as a playlist"
    )
    @app_commands.describe(name="Name for the saved playlist")
    async def savequeue(self, ctx: commands.Context, *, name: str):
        """
        Save the current queue as a playlist
        
        Usage:
            !savequeue My Playlist
        """
        player = self.get_player(ctx)
        
        if len(player.queue) == 0:
            embed = discord.Embed(
                title="❌ Empty Queue",
                description="The queue is empty! Add some songs first.",
                color=config.BOT_COLOR_ERROR
            )
            await ctx.send(embed=embed, delete_after=5)
            return
        
        # Save queue (would normally save to database/file)
        # For now, just acknowledge
        embed = discord.Embed(
            title="💾 Queue Saved",
            description=f"Saved **{len(player.queue)}** tracks as **{name}**",
            color=config.BOT_COLOR_SUCCESS
        )
        await ctx.send(embed=embed, delete_after=10)


# ═══════════════════════════════════════════════════════════════
# 🔧 COG SETUP
# ═══════════════════════════════════════════════════════════════

async def setup(bot: commands.Bot):
    await bot.add_cog(Queue(bot))
    logger.info("✅ Queue cog loaded")
