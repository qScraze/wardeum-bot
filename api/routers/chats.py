import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from api.database.db import get_session
from api.middleware.tg_auth import get_current_user
from bot.database.models import User, Chat, ChatSettings, PlanEnum
from api.schemas.schemas import (
    ChatResponse, ChatSettingsResponse, ChatSettingsUpdate, AddChatRequest
)
from fastapi.responses import FileResponse
import aiohttp
import pathlib
import os
from api.config import settings

router = APIRouter(tags=["chats"])

PLAN_CHAT_LIMITS: dict[str, int] = {
    "none": 0,
    "lite": 2,
    "pro": 5,
    "corporate": 10,
}

PRO_PLUS_MODULES = {"ai_censor_enabled", "antiraid_enabled"}
CORPORATE_MODULES: set[str] = set()


def _plan_str(user: User) -> str:
    return user.plan.value if hasattr(user.plan, "value") else str(user.plan)


def _settings_to_response(s: ChatSettings) -> ChatSettingsResponse:
    try:
        words = json.loads(s.stop_words) if s.stop_words else []
    except Exception:
        words = []
    return ChatSettingsResponse(
        ai_censor_enabled=s.ai_censor_enabled,
        captcha_enabled=s.captcha_enabled,
        antiraid_enabled=s.antiraid_enabled,
        clean_chat_enabled=s.clean_chat_enabled,
        link_filter_enabled=s.link_filter_enabled,
        stop_words_filter_enabled=s.stop_words_filter_enabled,
        stop_words=words,
        antiraid_threshold=s.antiraid_threshold,
        antiraid_window=s.antiraid_window,
        captcha_timeout=s.captcha_timeout,
    )


def _chat_to_response(chat: Chat, settings_obj: ChatSettings | None) -> ChatResponse:
    return ChatResponse(
        id=chat.id,
        tg_id=chat.tg_id,
        title=chat.title,
        username=chat.username,
        is_active=chat.is_active,
        settings=_settings_to_response(settings_obj) if settings_obj else None,
    )


@router.get("/chats", response_model=list[ChatResponse])
async def list_chats(
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> list[ChatResponse]:
    stmt = (
        select(Chat, ChatSettings)
        .outerjoin(ChatSettings, ChatSettings.chat_id == Chat.id)
        .where(Chat.owner_id == current_user.id, Chat.is_active == True)
    )
    rows = (await session.execute(stmt)).all()
    return [_chat_to_response(chat, s) for chat, s in rows]


@router.post("/chats", response_model=ChatResponse, status_code=201)
async def add_chat(
    body: AddChatRequest,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    plan = _plan_str(current_user)
    limit = PLAN_CHAT_LIMITS.get(plan, 0)

    count_result = await session.execute(
        select(Chat).where(Chat.owner_id == current_user.id, Chat.is_active == True)
    )
    existing = len(count_result.scalars().all())

    if existing >= limit:
        raise HTTPException(
            status_code=403,
            detail=f"Ваш тариф позволяет добавить не более {limit} чатов. Перейдите на более высокий тариф.",
        )

    title = body.title
    username = body.username

    # Fetch chat and avatar from telegram
    bot_token = settings.BOT_TOKEN
    async with aiohttp.ClientSession() as http_session:
        url = f"https://api.telegram.org/bot{bot_token}/getChat?chat_id={body.tg_id}"
        async with http_session.get(url) as resp:
            data = await resp.json()
            if not data.get("ok"):
                raise HTTPException(status_code=400, detail="Бот не добавлен в этот чат или нет доступа")
            
            chat_info = data["result"]
            title = chat_info.get("title", body.title)
            username = chat_info.get("username", body.username)
            
            photo = chat_info.get("photo")
            if photo:
                file_id = photo.get("small_file_id")
                f_url = f"https://api.telegram.org/bot{bot_token}/getFile?file_id={file_id}"
                async with http_session.get(f_url) as f_resp:
                    f_data = await f_resp.json()
                    if f_data.get("ok"):
                        file_path = f_data["result"]["file_path"]
                        dl_url = f"https://api.telegram.org/file/bot{bot_token}/{file_path}"
                        async with http_session.get(dl_url) as dl_resp:
                            if dl_resp.status == 200:
                                avatars_dir = pathlib.Path("data/avatars")
                                avatars_dir.mkdir(parents=True, exist_ok=True)
                                with open(avatars_dir / f"{body.tg_id}.jpg", "wb") as f:
                                    f.write(await dl_resp.read())

    chat = Chat(
        tg_id=body.tg_id,
        owner_id=current_user.id,
        title=title,
        username=username,
        is_active=True,
    )
    session.add(chat)
    await session.flush()

    chat_settings = ChatSettings(chat_id=chat.id)
    session.add(chat_settings)
    await session.commit()
    await session.refresh(chat)
    await session.refresh(chat_settings)

    return _chat_to_response(chat, chat_settings)


@router.get("/chats/{chat_id}/avatar")
async def get_chat_avatar(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session)
):
    chat = await session.scalar(select(Chat).where(Chat.id == chat_id, Chat.owner_id == current_user.id))
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    
    avatar_path = pathlib.Path("data/avatars") / f"{chat.tg_id}.jpg"
    if avatar_path.exists():
        return FileResponse(avatar_path, media_type="image/jpeg")
    
    raise HTTPException(status_code=404, detail="Avatar not found")


@router.get("/chats/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ChatResponse:
    result = await session.execute(
        select(Chat, ChatSettings)
        .outerjoin(ChatSettings, ChatSettings.chat_id == Chat.id)
        .where(Chat.id == chat_id, Chat.owner_id == current_user.id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Чат не найден")
    return _chat_to_response(row[0], row[1])


@router.put("/chats/{chat_id}/settings", response_model=ChatSettingsResponse)
async def update_chat_settings(
    chat_id: int,
    body: ChatSettingsUpdate,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
) -> ChatSettingsResponse:
    plan = _plan_str(current_user)

    result = await session.execute(
        select(Chat, ChatSettings)
        .outerjoin(ChatSettings, ChatSettings.chat_id == Chat.id)
        .where(Chat.id == chat_id, Chat.owner_id == current_user.id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="Чат не найден")

    chat, s = row
    if not s:
        s = ChatSettings(chat_id=chat.id)
        session.add(s)

    # Enforce plan restrictions for Pro+ features
    if body.ai_censor_enabled and plan not in ("pro", "corporate"):
        raise HTTPException(status_code=403, detail="ИИ-цензор доступен только на тарифе Про и выше")
    if body.antiraid_enabled and plan not in ("pro", "corporate"):
        raise HTTPException(status_code=403, detail="Anti-Raid доступен только на тарифе Про и выше")

    update_data = body.model_dump(exclude_none=True)
    for field, value in update_data.items():
        if field == "stop_words":
            setattr(s, "stop_words", json.dumps(value, ensure_ascii=False))
        else:
            setattr(s, field, value)

    await session.commit()
    await session.refresh(s)
    return _settings_to_response(s)


@router.delete("/chats/{chat_id}", status_code=204)
async def delete_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(
        select(Chat).where(Chat.id == chat_id, Chat.owner_id == current_user.id)
    )
    chat = result.scalar_one_or_none()
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")
    chat.is_active = False
    await session.commit()
