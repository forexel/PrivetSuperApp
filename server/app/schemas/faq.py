from datetime import datetime
import uuid
from pydantic import BaseModel

class FAQCategoryResponse(BaseModel):
    id: uuid.UUID
    slug: str
    title: str

    class Config:
        from_attributes = True

class FAQArticleBase(BaseModel):
    title: str
    content: str
    keywords: list[str]

class FAQArticleResponse(FAQArticleBase):
    id: uuid.UUID
    category_id: uuid.UUID
    created_at: datetime

    class Config:
        from_attributes = True

class SupportRequestCreate(BaseModel):
    subject: str
    message: str
    file_url: str | None = None
