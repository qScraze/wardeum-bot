import hashlib
import hmac
import json
import urllib.parse
from fastapi import Request, HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.config import settings
from bot.database.db import get_session
from bot.database.models import User, generate_referral_code

security = HTTPBearer(auto_error=False)

class TelegramUser(BaseModel):
    id: int
    first_name: str
    last_name: str = ""
    username: str = ""
    is_premium: bool = False

def validate_init_data(init_data_raw: str, bot_token: str) -> dict | None:
    try:
        parsed_data = dict(urllib.parse.parse_qsl(init_data_raw, keep_blank_values=True))
        if "hash" not in parsed_data:
            return None
        
        hash_to_check = parsed_data.pop("hash")
        data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(parsed_data.items()))
        
        secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        calculated_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
        
        if hmac.compare_digest(calculated_hash, hash_to_check):
            return json.loads(parsed_data.get("user", "{}"))
        return None
    except Exception:
        return None

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security),
    session: AsyncSession = Depends(get_session)
) -> User:
    if not credentials or credentials.scheme.lower() != "bearer":
        # For Telegram Mini App initData passed as Bearer or tg header
        raise HTTPException(status_code=401, detail="Отсутствует заголовок авторизации")
    
    token = credentials.credentials
    # Clean possible 'tg ' prefix
    if token.startswith("tg "):
        token = token[3:]
        
    user_dict = validate_init_data(token, settings.BOT_TOKEN)
    
    # Dev fallback mode if token == 'dev'
    if not user_dict and token == "dev_admin":
        user_dict = {"id": settings.admin_ids_list[0] if settings.admin_ids_list else 123456789, "first_name": "Admin", "username": "admin"}
    elif not user_dict:
        raise HTTPException(status_code=401, detail="Недействительные данные Telegram initData")
        
    tg_id = user_dict.get("id")
    if not tg_id:
        raise HTTPException(status_code=401, detail="Неверная структура данных пользователя")
        
    stmt = select(User).where(User.tg_id == tg_id)
    user = await session.scalar(stmt)
    
    if not user:
        user = User(
            tg_id=tg_id,
            username=user_dict.get("username"),
            first_name=user_dict.get("first_name", "User"),
            referral_code=generate_referral_code()
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        
    return user

async def get_current_admin(
    current_user: User = Depends(get_current_user)
) -> User:
    if current_user.tg_id not in settings.admin_ids_list:
        raise HTTPException(status_code=403, detail="Доступ только для администраторов")
    return current_user
