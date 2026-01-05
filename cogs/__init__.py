"""
Cogs module initialization
"""

from cogs.music import Music
from cogs.queue import Queue
from cogs.effects import Effects
from cogs.utility import Utility
from cogs.events import Events

__all__ = [
    'Music',
    'Queue',
    'Effects',
    'Utility',
    'Events',
]
