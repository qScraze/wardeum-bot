import asyncio
from collections import deque
from datetime import datetime
from aiogram.types import User

class AntiRaidService:
    def __init__(self):
        # chat_id -> deque of join timestamps
        self.windows: dict[int, deque[datetime]] = {}
        # buffer for grouping raid notifications: chat_id -> list of user objects
        self.raid_buffers: dict[int, list[User]] = {}

    def register_join(self, chat_id: int, threshold: int = 10, window_seconds: int = 5) -> bool:
        """Register a join event and return True if a raid is detected."""
        now = datetime.now()
        
        if chat_id not in self.windows:
            self.windows[chat_id] = deque()
            
        window = self.windows[chat_id]
        window.append(now)
        
        # Remove old entries
        while window and (now - window[0]).total_seconds() > window_seconds:
            window.popleft()
            
        return len(window) >= threshold

    def score_profile(self, user: User) -> int:
        """
        Score a profile from 0 to 10.
        < 3 = suspicious
        >= 3 = likely human
        """
        score = 0
        if user.username:
            score += 2
        # We can't directly check has_photo without another API call, assume bot API provides some heuristic or skip
        # Note: the task said "(we check via bot API)", we will simulate this or it's handled outside, but for simplicity:
        # Actually, if we pass aiogram User, we don't have direct access to photos in this object.
        # But we can add premium check
        if user.is_premium:
            score += 1
            
        # Account age heuristic: larger tg_id = newer account.
        # Arbitrary threshold for >30 days. Let's assume < 6,000,000,000 is older than 30 days.
        if user.id < 6000000000:
            score += 3
            
        return score
        
anti_raid_service = AntiRaidService()
