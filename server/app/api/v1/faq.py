from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_db
from app.schemas.faq import FAQCategoryResponse, FAQArticleResponse
from app.services.faq import FAQService

router = APIRouter(prefix="/faq", tags=["faq"])

@router.get("/categories", response_model=list[FAQCategoryResponse])
async def get_categories(
    db: Annotated[AsyncSession, Depends(get_db)]
):
    service = FAQService(db)
    return await service.get_categories()

@router.get("/categories/{slug}/articles", response_model=list[FAQArticleResponse])
async def get_articles_by_category(
    slug: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    service = FAQService(db)
    return await service.get_articles_by_category(slug)

@router.get("/articles/{article_id}", response_model=FAQArticleResponse)
async def get_article(
    article_id: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    service = FAQService(db)
    article = await service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    return article

@router.get("/search", response_model=list[FAQArticleResponse])
async def search_articles(
    q: str,
    db: Annotated[AsyncSession, Depends(get_db)]
):
    service = FAQService(db)
    return await service.search_articles(q)
