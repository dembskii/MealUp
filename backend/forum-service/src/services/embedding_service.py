import logging
from typing import Optional, List
from openai import AsyncOpenAI
from sqlmodel.ext.asyncio.session import AsyncSession
from src.core.config import settings

logger = logging.getLogger(__name__)

embedding_client = AsyncOpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL
)


def build_post_text(post) -> str:
    """Combining text into one block to embed"""
    parts = []
    
    if post.title:
        parts.append(f"Title: {post.title}")
    
    if post.content:
        parts.append(f"Content: {post.content}")
    
    if post.tags:
        tags_str = ", ".join(post.tags)
        parts.append(f"Tags: {tags_str}")
    
    return " ".join(parts)


async def generate_embedding(text: str) -> Optional[List[float]]:
    """Generating embedding for text"""
    try:
        if not text or not text.strip():
            logger.warning("Empty text passed to generate_embedding")
            return None
        
        response = await embedding_client.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text
        )
        
        embedding = response.data[0].embedding
        logger.info(f"Generated embedding of dimension {len(embedding)}")
        return embedding
        
    except Exception as e:
        logger.error(f"Error generating embedding: {str(e)}")
        return None


async def embed_post(session: AsyncSession ,post) -> Optional[List[float]]:
    """Generating embed for whole Post(title, content, tags)"""
    try:
        post_text = build_post_text(post)
        embedding = await generate_embedding(post_text)

        if embedding:
            post.embedding = embedding
            session.add(post)
            await session.commit()
            logger.info(f"Embedded and saved post {post.id}")

        return embedding
    except Exception as e:
        logger.error(f"Error embedding post {post.id}: {str(e)}")
        await session.rollback()
        return None