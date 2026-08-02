import asyncio
import time
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message

class ThrottleMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: float = 1.0):
        self.rate_limit = rate_limit
        self.users: Dict[int, float] = {}
        self.lock = asyncio.Lock()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any]
    ) -> Any:
        user_id = event.from_user.id
        now = time.time()
        
        async with self.lock:
            last_time = self.users.get(user_id, 0.0)
            if now - last_time < self.rate_limit:
                return # Block
            self.users[user_id] = now
            
        return await handler(event, data)
