"""
SQLAlchemy 2.0 async ORM models for Wardeum.
Shared with the bot — same .env / same DB file.
"""
from __future__ import annotations

import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class PlanEnum(str, enum.Enum):
    none = "none"
    lite = "lite"
    pro = "pro"
    corporate = "corporate"


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------

class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# User
# ---------------------------------------------------------------------------

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    referral_code: Mapped[Optional[str]] = mapped_column(String(16), unique=True, nullable=True, index=True)
    referred_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    subscription_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    plan: Mapped[PlanEnum] = mapped_column(
        Enum(PlanEnum, name="planenum"), nullable=False, default=PlanEnum.none
    )
    extra_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    chats: Mapped[list["Chat"]] = relationship("Chat", back_populates="owner", lazy="selectin")
    referrals_given: Mapped[list["Referral"]] = relationship(
        "Referral", foreign_keys="Referral.inviter_id", back_populates="inviter", lazy="selectin"
    )
    referral_received: Mapped[Optional["Referral"]] = relationship(
        "Referral", foreign_keys="Referral.invitee_id", back_populates="invitee", lazy="selectin"
    )
    payments: Mapped[list["PaymentHistory"]] = relationship(
        "PaymentHistory", back_populates="user", lazy="selectin"
    )


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

class Chat(Base):
    __tablename__ = "chats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    owner_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(256), nullable=False, default="")
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="chats")
    settings: Mapped[Optional["ChatSettings"]] = relationship(
        "ChatSettings", back_populates="chat", uselist=False, lazy="selectin"
    )


# ---------------------------------------------------------------------------
# ChatSettings
# ---------------------------------------------------------------------------

class ChatSettings(Base):
    __tablename__ = "chat_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("chats.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    ai_censor_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    captcha_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    antiraid_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    clean_chat_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    link_filter_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    stop_words_filter_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # JSON-encoded list of stop words stored as TEXT
    stop_words: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    antiraid_threshold: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    antiraid_window: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    captcha_timeout: Mapped[int] = mapped_column(Integer, nullable=False, default=300)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationship
    chat: Mapped["Chat"] = relationship("Chat", back_populates="settings")


# ---------------------------------------------------------------------------
# CaptchaSession
# ---------------------------------------------------------------------------

class CaptchaSession(Base):
    __tablename__ = "captcha_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    chat_tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(6), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


# ---------------------------------------------------------------------------
# Blacklist
# ---------------------------------------------------------------------------

class Blacklist(Base):
    __tablename__ = "blacklist"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    reason: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    banned_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    chat_tg_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True, index=True)
    is_global: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


# ---------------------------------------------------------------------------
# Referral
# ---------------------------------------------------------------------------

class Referral(Base):
    __tablename__ = "referrals"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    inviter_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    invitee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    bonus_days: Mapped[int] = mapped_column(Integer, nullable=False, default=7)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationships
    inviter: Mapped["User"] = relationship(
        "User", foreign_keys=[inviter_id], back_populates="referrals_given"
    )
    invitee: Mapped["User"] = relationship(
        "User", foreign_keys=[invitee_id], back_populates="referral_received"
    )


# ---------------------------------------------------------------------------
# PromoCode
# ---------------------------------------------------------------------------

class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    discount_pct: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    free_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # -1 = unlimited
    uses_left: Mapped[int] = mapped_column(Integer, nullable=False, default=-1)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )


# ---------------------------------------------------------------------------
# ActivationKey
# ---------------------------------------------------------------------------

class ActivationKey(Base):
    __tablename__ = "activation_keys"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    # Format: XXXX-XXXX-XXXXX-XXXXX
    key: Mapped[str] = mapped_column(String(24), unique=True, nullable=False, index=True)
    plan: Mapped[PlanEnum] = mapped_column(
        Enum(PlanEnum, name="planenum"), nullable=False
    )
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    used_by: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationship
    user: Mapped[Optional["User"]] = relationship("User", foreign_keys=[used_by])


# ---------------------------------------------------------------------------
# PaymentHistory
# ---------------------------------------------------------------------------

class PaymentHistory(Base):
    __tablename__ = "payment_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    plan: Mapped[PlanEnum] = mapped_column(
        Enum(PlanEnum, name="planenum"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="pending")
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="")
    provider_payment_id: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="payments")


# ---------------------------------------------------------------------------
# ForceSub  (singleton row with id=1)
# ---------------------------------------------------------------------------

class ForceSub(Base):
    __tablename__ = "force_sub"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)  # always 1
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    channel_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
