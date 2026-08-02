from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.database.db import get_session
from api.middleware.tg_auth import get_current_user
from api.config import settings
from bot.database.models import User
from api.schemas.schemas import UserResponse

router = APIRouter(tags=["auth"])


@router.get("/me", response_model=UserResponse)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """Возвращает профиль текущего пользователя."""
    return UserResponse(
        id=current_user.id,
        tg_id=current_user.tg_id,
        username=current_user.username,
        first_name=current_user.first_name or "User",
        plan=current_user.plan.value if hasattr(current_user.plan, "value") else str(current_user.plan),
        subscription_end=current_user.subscription_end,
        extra_days=current_user.extra_days,
        referral_code=current_user.referral_code,
        is_admin=current_user.tg_id in settings.admin_ids_list,
    )
