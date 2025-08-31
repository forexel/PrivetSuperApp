import uuid
from sqlalchemy import select, or_
from sqlalchemy.orm import selectinload

from app.models.faq import FAQCategory, FAQArticle
from app.services.base import BaseService

class FAQService(BaseService):
    async def get_categories(self) -> list[FAQCategory]:
        result = await self.db.scalars(select(FAQCategory))
        return list(result)

    async def get_articles_by_category(self, category_slug: str) -> list[FAQArticle]:
        result = await self.db.scalars(
            select(FAQArticle)
            .join(FAQCategory)
            .where(FAQCategory.slug == category_slug)
        )
        return list(result)

    async def get_article(self, article_id: uuid.UUID) -> FAQArticle | None:
        return await self.db.get(FAQArticle, article_id)

    async def search_articles(self, query: str) -> list[FAQArticle]:
        result = await self.db.scalars(
            select(FAQArticle).where(
                or_(
                    FAQArticle.title.ilike(f"%{query}%"),
                    FAQArticle.content.ilike(f"%{query}%"),
                    FAQArticle.keywords.contains([query])
                )
            )
        )
        return list(result)
