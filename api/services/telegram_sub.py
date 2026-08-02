import aiohttp
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.config import settings
from bot.database.models import ForceSub
from bot.middlewares.subscription import format_telegram_channel_id, format_channel_url

async def check_telegram_subscription(bot_token: str, channel_id: int | str, user_tg_id: int) -> bool:
    if not bot_token or bot_token == "placeholder_token":
        return True
    
    formatted_chat_id = format_telegram_channel_id(channel_id)
    url = f"https://api.telegram.org/bot{bot_token}/getChatMember"
    params = {
        "chat_id": str(formatted_chat_id),
        "user_id": str(user_tg_id)
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params, timeout=5.0) as resp:
                data = await resp.json()
                if data.get("ok"):
                    status = data.get("result", {}).get("status")
                    return status in ["creator", "administrator", "member", "restricted"]
    except Exception:
        pass
    return False


async def get_user_sub_status(session: AsyncSession, user_tg_id: int) -> tuple[bool, str | None]:
    """Returns (is_subscribed, force_sub_url)"""
    is_admin = user_tg_id in settings.admin_ids_list
    force_sub = await session.scalar(select(ForceSub).where(ForceSub.id == 1))
    
    if not force_sub or not force_sub.enabled or not force_sub.channel_id:
        return True, None
        
    url = format_channel_url(force_sub.channel_id)
    if is_admin:
        return True, url

    is_subscribed = await check_telegram_subscription(
        settings.BOT_TOKEN, force_sub.channel_id, user_tg_id
    )
    return is_subscribed, url
