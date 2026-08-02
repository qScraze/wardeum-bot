import random
import string
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bot.database.models import Referral, User

async def generate_referral_code() -> str:
    """Generate 8 char alphanumeric unique code."""
    return "".join(random.choices(string.ascii_letters + string.digits, k=8))

async def process_referral(inviter_code: str, new_user_tg_id: int, session: AsyncSession) -> bool:
    # Find inviter
    stmt = select(User).where(User.referral_code == inviter_code)
    result = await session.execute(stmt)
    inviter = result.scalar_one_or_none()
    
    if not inviter:
        return False
        
    # Find new user
    stmt = select(User).where(User.tg_id == new_user_tg_id)
    result = await session.execute(stmt)
    invitee = result.scalar_one_or_none()
    
    if not invitee or invitee.referred_by is not None:
        return False
        
    # Prevent self-referral
    if inviter.id == invitee.id:
        return False

    invitee.referred_by = inviter.id
    
    # Create referral record
    ref = Referral(inviter_id=inviter.id, invitee_id=invitee.id, bonus_days=5)
    session.add(ref)
    
    # Add bonus days to inviter
    inviter.extra_days += 5
    
    await session.commit()
    return True

async def add_bonus_days(user_id: int, days: int, session: AsyncSession) -> None:
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()
    
    if user:
        user.extra_days += days
        await session.commit()
