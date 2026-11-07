from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector

from app.db.base import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    item_type = Column(String(20), nullable=False)  # lost or found
    category = Column(String(50), nullable=False)
    location = Column(String(150), nullable=False)
    event_date = Column(DateTime, nullable=False)
    image_url = Column(String(500), nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # 384-dimensional semantic embedding for AI matching
    embedding = Column(Vector(384), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )