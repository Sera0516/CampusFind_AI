
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey
)
from sqlalchemy.sql import func

from app.db.base import Base


class Claim(Base):
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True, index=True)

    # Found item being claimed
    item_id = Column(
        Integer,
        ForeignKey("items.id"),
        nullable=False,
        index=True
    )

    # User requesting ownership
    claimant_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    # Claim explanation
    message = Column(Text, nullable=False)

    # pending, approved or rejected
    status = Column(
        String(20),
        nullable=False,
        default="pending",
        index=True
    )

    # Owner's optional response
    owner_response = Column(Text, nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
