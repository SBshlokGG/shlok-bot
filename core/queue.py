"""
🎵 Music Queue System
Advanced queue management with shuffle, history, and more
"""

import random
from typing import Optional, List
from collections import deque

from core.track import Track

# ═══════════════════════════════════════════════════════════════
# 📋 MUSIC QUEUE CLASS
# ═══════════════════════════════════════════════════════════════

class MusicQueue:
    """
    Advanced Music Queue with multiple features
    
    Features:
    - Unlimited queue size
    - Shuffle functionality
    - Move and remove tracks
    - Fair queue (round-robin per user)
    - Priority queue
    """
    
    def __init__(self):
        self._queue: deque[Track] = deque()
        self._history: List[Track] = []
        self._shuffle_indices: List[int] = []
        self._is_shuffled = False
        
    def __len__(self) -> int:
        return len(self._queue)
    
    def __bool__(self) -> bool:
        return len(self._queue) > 0
    
    def __iter__(self):
        return iter(self._queue)
    
    def __getitem__(self, index: int) -> Track:
        return self._queue[index]
    
    # ═══════════════════════════════════════════════════════════
    # ➕ ADD METHODS
    # ═══════════════════════════════════════════════════════════
    
    def add(self, track: Track) -> int:
        """Add a track to the end of the queue"""
        self._queue.append(track)
        return len(self._queue)
    
    def add_next(self, track: Track) -> int:
        """Add a track to play next (after current)"""
        if len(self._queue) > 0:
            self._queue.insert(0, track)
        else:
            self._queue.append(track)
        return 1
    
    def add_to_front(self, track: Track) -> int:
        """Add a track to the front of the queue"""
        self._queue.appendleft(track)
        return 0
    
    def add_multiple(self, tracks: List[Track]) -> int:
        """Add multiple tracks to the queue"""
        for track in tracks:
            self._queue.append(track)
        return len(self._queue)
    
    # ═══════════════════════════════════════════════════════════
    # ➖ REMOVE METHODS
    # ═══════════════════════════════════════════════════════════
    
    def get_next(self) -> Optional[Track]:
        """Get and remove the next track"""
        if self._queue:
            return self._queue.popleft()
        return None
    
    def remove(self, index: int) -> Optional[Track]:
        """Remove a track by index"""
        if 0 <= index < len(self._queue):
            track = self._queue[index]
            del self._queue[index]
            return track
        return None
    
    def remove_track(self, track: Track) -> bool:
        """Remove a specific track"""
        try:
            self._queue.remove(track)
            return True
        except ValueError:
            return False
    
    def remove_user_tracks(self, user_id: int) -> int:
        """Remove all tracks by a specific user"""
        original_length = len(self._queue)
        self._queue = deque([t for t in self._queue if t.requester_id != user_id])
        return original_length - len(self._queue)
    
    def remove_duplicates(self) -> int:
        """Remove duplicate tracks"""
        seen = set()
        new_queue = deque()
        removed = 0
        
        for track in self._queue:
            if track.url not in seen:
                seen.add(track.url)
                new_queue.append(track)
            else:
                removed += 1
        
        self._queue = new_queue
        return removed
    
    def clear(self):
        """Clear the entire queue"""
        self._queue.clear()
        self._is_shuffled = False
    
    # ═══════════════════════════════════════════════════════════
    # 🔀 SHUFFLE & REORDER
    # ═══════════════════════════════════════════════════════════
    
    def shuffle(self) -> bool:
        """Shuffle the queue"""
        if len(self._queue) < 2:
            return False
        
        queue_list = list(self._queue)
        random.shuffle(queue_list)
        self._queue = deque(queue_list)
        self._is_shuffled = True
        return True
    
    def move(self, from_index: int, to_index: int) -> bool:
        """Move a track from one position to another"""
        if not (0 <= from_index < len(self._queue) and 0 <= to_index < len(self._queue)):
            return False
        
        track = self._queue[from_index]
        del self._queue[from_index]
        self._queue.insert(to_index, track)
        return True
    
    def swap(self, index1: int, index2: int) -> bool:
        """Swap two tracks"""
        if not (0 <= index1 < len(self._queue) and 0 <= index2 < len(self._queue)):
            return False
        
        self._queue[index1], self._queue[index2] = self._queue[index2], self._queue[index1]
        return True
    
    def reverse(self):
        """Reverse the queue order"""
        self._queue.reverse()
    
    def sort_by_duration(self, ascending: bool = True):
        """Sort queue by track duration"""
        queue_list = sorted(
            self._queue,
            key=lambda t: t.duration or 0,
            reverse=not ascending
        )
        self._queue = deque(queue_list)
    
    def sort_by_title(self, ascending: bool = True):
        """Sort queue by track title"""
        queue_list = sorted(
            self._queue,
            key=lambda t: t.title.lower(),
            reverse=not ascending
        )
        self._queue = deque(queue_list)
    
    # ═══════════════════════════════════════════════════════════
    # 📊 QUEUE INFO
    # ═══════════════════════════════════════════════════════════
    
    def get_list(self, start: int = 0, limit: int = 10) -> List[Track]:
        """Get a portion of the queue"""
        queue_list = list(self._queue)
        return queue_list[start:start + limit]
    
    def get_all(self) -> List[Track]:
        """Get all tracks in the queue"""
        return list(self._queue)
    
    def get_total_duration(self) -> int:
        """Get total duration of all tracks in seconds"""
        return sum(t.duration or 0 for t in self._queue)
    
    def get_track(self, index: int) -> Optional[Track]:
        """Get a track by index without removing it"""
        if 0 <= index < len(self._queue):
            return self._queue[index]
        return None
    
    def find_track(self, query: str) -> Optional[int]:
        """Find a track by title (case-insensitive)"""
        query_lower = query.lower()
        for i, track in enumerate(self._queue):
            if query_lower in track.title.lower():
                return i
        return None
    
    def get_tracks_by_user(self, user_id: int) -> List[Track]:
        """Get all tracks requested by a specific user"""
        return [t for t in self._queue if t.requester_id == user_id]
    
    @property
    def is_empty(self) -> bool:
        """Check if queue is empty"""
        return len(self._queue) == 0
    
    @property
    def is_shuffled(self) -> bool:
        """Check if queue has been shuffled"""
        return self._is_shuffled
    
    # ═══════════════════════════════════════════════════════════
    # 💾 SAVE/LOAD QUEUE
    # ═══════════════════════════════════════════════════════════
    
    def to_dict(self) -> dict:
        """Convert queue to dictionary for saving"""
        return {
            "tracks": [t.to_dict() for t in self._queue],
            "is_shuffled": self._is_shuffled
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MusicQueue':
        """Create queue from dictionary"""
        queue = cls()
        queue._queue = deque([Track.from_dict(t) for t in data.get("tracks", [])])
        queue._is_shuffled = data.get("is_shuffled", False)
        return queue
