from datetime import datetime
import uuid
from sqlalchemy import DateTime, ForeignKey, String, Text, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.base import Base

class FAQCategory(Base):
    __tablename__ = "faq_categories"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String, unique=True)
    title: Mapped[str] = mapped_column(String)
    
    articles = relationship("FAQArticle", back_populates="category")

class FAQArticle(Base):
    __tablename__ = "faq_articles"

    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=uuid.uuid4)
    category_id: Mapped[uuid.UUID] = mapped_column(UUID, ForeignKey("faq_categories.id"))
    title: Mapped[str] = mapped_column(String)
    content: Mapped[str] = mapped_column(Text)
    keywords: Mapped[list[str]] = mapped_column(ARRAY(String))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    category = relationship("FAQCategory", back_populates="articles")
