"""
🎵 Track Model
Represents a music track with all metadata
"""

import asyncio
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

import discord
import yt_dlp

import config

logger = logging.getLogger('ShlokMusic.Track')

# ═══════════════════════════════════════════════════════════════
# 🎵 TRACK DATACLASS
# ═══════════════════════════════════════════════════════════════

@dataclass
class Track:
    """
    Represents a music track
    
    Attributes:
        title: Track title
        url: Source URL
        duration: Duration in seconds
        thumbnail: Thumbnail URL
        artist: Artist/uploader name
        requester: User who requested the track
        source_type: Source type (youtube, spotify, etc.)
    """
    
    title: str
    url: str
    duration: Optional[int] = None
    thumbnail: Optional[str] = None
    artist: Optional[str] = None
    requester: Optional[discord.Member] = None
    source_type: str = "youtube"
    
    # Audio source URL (extracted later)
    _audio_url: Optional[str] = field(default=None, repr=False)
    
    # Additional metadata
    views: Optional[int] = None
    likes: Optional[int] = None
    upload_date: Optional[str] = None
    description: Optional[str] = None
    
    @property
    def requester_id(self) -> Optional[int]:
        """Get requester's user ID"""
        return self.requester.id if self.requester else None
    
    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string"""
        if not self.duration:
            return "🔴 Live"
        
        hours, remainder = divmod(self.duration, 3600)
        minutes, seconds = divmod(remainder, 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        return f"{minutes}:{seconds:02d}"
    
    async def get_source(self) -> Optional[discord.FFmpegPCMAudio]:
        """Get FFmpeg audio source for playback"""
        try:
            # Extract audio URL if not already done
            if not self._audio_url:
                await self._extract_audio_url()
            
            if not self._audio_url:
                logger.error("❌ No audio URL available")
                return None
            
            logger.info(f"🎧 Creating FFmpeg source with URL length: {len(self._audio_url)}")
            
            # FFmpeg options for streaming
            ffmpeg_options = {
                'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
                'options': '-vn'
            }
            
            source = discord.FFmpegPCMAudio(
                self._audio_url,
                **ffmpeg_options
            )
            
            logger.info(f"✅ FFmpeg source created successfully")
            return source
            
        except Exception as e:
            logger.error(f"❌ Error getting audio source: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def _extract_audio_url(self):
        """Extract the direct audio URL"""
        try:
            # Use yt-dlp to get audio URL
            ytdl_opts = {
                'format': 'bestaudio/best',
                'noplaylist': True,
                'nocheckcertificate': True,
                'ignoreerrors': False,
                'logtostderr': False,
                'quiet': True,
                'no_warnings': True,
                'default_search': 'ytsearch',
                'source_address': '0.0.0.0',
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(
                    None,
                    lambda: ytdl.extract_info(self.url, download=False)
                )
                
                if data:
                    # Get the audio URL
                    self._audio_url = data.get('url')
                    
                    if not self._audio_url:
                        # Try to get from formats - prefer audio-only formats
                        formats = data.get('formats', [])
                        audio_formats = [f for f in formats if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                        
                        if audio_formats:
                            # Get best audio format
                            best_audio = max(audio_formats, key=lambda f: f.get('abr', 0) or 0)
                            self._audio_url = best_audio.get('url')
                        elif formats:
                            # Fallback to any format with audio
                            for f in formats:
                                if f.get('acodec') != 'none' and f.get('url'):
                                    self._audio_url = f['url']
                                    break
                    
                    if self._audio_url:
                        logger.info(f"✅ Extracted audio URL for: {self.title}")
                    else:
                        logger.error(f"❌ No audio URL found in data for: {self.title}")
                    
                    # Update metadata if missing
                    if not self.duration:
                        self.duration = data.get('duration')
                    if not self.thumbnail:
                        self.thumbnail = data.get('thumbnail')
                    if not self.artist:
                        self.artist = data.get('uploader') or data.get('channel')
                else:
                    logger.error("❌ No data returned from yt-dlp")
                    
        except Exception as e:
            logger.error(f"❌ Error extracting audio URL: {e}")
            import traceback
            traceback.print_exc()
    
    def to_dict(self) -> dict:
        """Convert track to dictionary"""
        return {
            "title": self.title,
            "url": self.url,
            "duration": self.duration,
            "thumbnail": self.thumbnail,
            "artist": self.artist,
            "requester_id": self.requester_id,
            "source_type": self.source_type,
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Track':
        """Create track from dictionary"""
        return cls(
            title=data.get("title", "Unknown"),
            url=data.get("url", ""),
            duration=data.get("duration"),
            thumbnail=data.get("thumbnail"),
            artist=data.get("artist"),
            source_type=data.get("source_type", "youtube"),
        )
    
    def __eq__(self, other):
        if isinstance(other, Track):
            return self.url == other.url
        return False
    
    def __hash__(self):
        return hash(self.url)


# ═══════════════════════════════════════════════════════════════
# 🔍 TRACK SEARCH & EXTRACTION
# ═══════════════════════════════════════════════════════════════

class TrackExtractor:
    """
    Utility class for searching and extracting tracks
    """
    
    @staticmethod
    async def search(query: str, requester: discord.Member = None, limit: int = 1) -> list[Track]:
        """
        Search for tracks
        
        Args:
            query: Search query or URL
            requester: User who requested
            limit: Maximum number of results
            
        Returns:
            List of Track objects
        """
        try:
            ytdl_opts = {
                **config.YTDL_OPTIONS,
                'extract_flat': True,
                'playlistend': limit,
            }
            
            # Check if it's a URL or search query
            is_url = query.startswith(('http://', 'https://', 'www.'))
            
            if not is_url:
                query = f"ytsearch{limit}:{query}"
            
            with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(
                    None,
                    lambda: ytdl.extract_info(query, download=False)
                )
                
                if not data:
                    return []
                
                tracks = []
                
                # Handle playlist
                if 'entries' in data:
                    for entry in data['entries'][:limit]:
                        if entry:
                            track = TrackExtractor._create_track(entry, requester)
                            if track:
                                tracks.append(track)
                else:
                    track = TrackExtractor._create_track(data, requester)
                    if track:
                        tracks.append(track)
                
                return tracks
                
        except Exception as e:
            logger.error(f"❌ Error searching tracks: {e}")
            return []
    
    @staticmethod
    async def extract_playlist(url: str, requester: discord.Member = None, limit: int = 100) -> list[Track]:
        """
        Extract all tracks from a playlist
        
        Args:
            url: Playlist URL
            requester: User who requested
            limit: Maximum number of tracks
            
        Returns:
            List of Track objects
        """
        try:
            ytdl_opts = {
                **config.YTDL_OPTIONS,
                'extract_flat': True,
                'playlistend': limit,
            }
            
            with yt_dlp.YoutubeDL(ytdl_opts) as ytdl:
                loop = asyncio.get_event_loop()
                data = await loop.run_in_executor(
                    None,
                    lambda: ytdl.extract_info(url, download=False)
                )
                
                if not data or 'entries' not in data:
                    return []
                
                tracks = []
                for entry in data['entries'][:limit]:
                    if entry:
                        track = TrackExtractor._create_track(entry, requester)
                        if track:
                            tracks.append(track)
                
                return tracks
                
        except Exception as e:
            logger.error(f"❌ Error extracting playlist: {e}")
            return []
    
    @staticmethod
    def _create_track(data: dict, requester: discord.Member = None) -> Optional[Track]:
        """Create a Track object from extracted data"""
        try:
            # Get URL
            url = data.get('url') or data.get('webpage_url')
            if not url and data.get('id'):
                url = f"https://www.youtube.com/watch?v={data['id']}"
            
            if not url:
                return None
            
            return Track(
                title=data.get('title') or "Unknown Title",
                url=url,
                duration=data.get('duration'),
                thumbnail=data.get('thumbnail') or data.get('thumbnails', [{}])[0].get('url'),
                artist=data.get('uploader') or data.get('channel') or "Unknown Artist",
                requester=requester,
                source_type="youtube",
                views=data.get('view_count'),
                likes=data.get('like_count'),
                upload_date=data.get('upload_date'),
            )
            
        except Exception as e:
            logger.error(f"❌ Error creating track: {e}")
            return None
    
    @staticmethod
    async def get_recommendations(track: Track, limit: int = 5) -> list[Track]:
        """Get recommended tracks based on a track"""
        try:
            # Use YouTube's related videos
            query = f"ytsearch{limit}:{track.artist} {track.title} similar"
            return await TrackExtractor.search(query, limit=limit)
        except Exception as e:
            logger.error(f"❌ Error getting recommendations: {e}")
            return []
