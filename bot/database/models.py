import secrets
import string
from datetime import datetime
import enum
from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def generate_referral_code(length: int = 8) -> str:
    """Generate a random 8-character alphanumeric referral code."""
    alphabet = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(length))



class Base(DeclarativeBase):
    pass

class PlanEnum(str, enum.Enum):
    NONE = "none"
    LITE = "lite"
    PRO = "pro"
    CORPORATE = "corporate"

class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    first_name: Mapped[str | None] = mapped_column(String, nullable=True)
    referral_code: Mapped[str] = mapped_column(String(8), unique=True, nullable=False)
    referred_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    subscription_end: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    plan: Mapped[PlanEnum] = mapped_column(String, default=PlanEnum.NONE, nullable=False)
    extra_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)


class Blacklist(Base):
    __tablename__ = "blacklists"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    username: Mapped[str | None] = mapped_column(String, nullable=True)
    first_name: Mapped[str | None] = mapped_column(String, nullable=True)
    reason: Mapped[str] = mapped_column(String, nullable=False)
    banned_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    chat_tg_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    is_global: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

class Referral(Base):
    __tablename__ = "referrals"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inviter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    invitee_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, nullable=False)
    bonus_days: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

class PromoCode(Base):
    __tablename__ = "promocodes"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    discount_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    free_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    uses_left: Mapped[int] = mapped_column(Integer, default=-1, nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

class ActivationKey(Base):
    __tablename__ = "activation_keys"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    key: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    plan: Mapped[PlanEnum] = mapped_column(String, nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    used_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    used_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

class PaymentHistory(Base):
    __tablename__ = "payment_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    plan: Mapped[PlanEnum] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    provider: Mapped[str] = mapped_column(String, nullable=False)
    provider_payment_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

class ForceSub(Base):
    __tablename__ = "force_sub"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    channel_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
