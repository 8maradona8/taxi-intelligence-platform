from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, JSON, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base
from app.models.base import TimestampMixin
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.models.zone import Zone


class Signal(Base, TimestampMixin):
    __tablename__ = "signals"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    signal_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    source: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    zone_id: Mapped[int] = mapped_column(ForeignKey("zones.id"), nullable=False)

    impact_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    payload: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default=dict)

    zone: Mapped["Zone"] = relationship("Zone")
