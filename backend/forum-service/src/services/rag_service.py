import logging
from typing import List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import cast
from pgvector.sqlalchemy import Vector

from src.models.post import Post
from src.services.embedding_service import generate_embedding, client
from src.core.config import settings

logger = logging.getLogger(__name__)


async def vector_search(session: AsyncSession, query: str, top_k: int = 5) -> List[Post]:
    """Search posts by semantic similarity using pgvector cosine distance (<=>)."""
    query_embedding = await generate_embedding(query)
    if not query_embedding:
        logger.warning("Could not generate embedding for query: %s", query)
        return []

    query_vec = cast(query_embedding, Vector(1536))

    stmt = (
        select(Post)
        .where(Post.embedding.isnot(None))
        .order_by(Post.embedding.op("<=>")(query_vec))
        .limit(top_k)
    )
    result = await session.exec(stmt)
    return list(result.all())


async def ask(session: AsyncSession, question: str) -> dict:
    """RAG pipeline: retrieve relevant posts → build prompt → call LLM → return answer + sources."""
    sources = await vector_search(session, question)

    if not sources:
        return {
            "answer": "No relevant posts found to answer your question.",
            "sources": []
        }

    context = "\n\n".join(
        f"[{i + 1}] Title: {post.title}\n{post.content}"
        for i, post in enumerate(sources)
    )

    prompt = (
        "You are a helpful assistant for a fitness and meal planning community forum.\n"
        "Answer the following question using only the forum posts provided below.\n"
        "Reference post numbers (e.g. [1], [2]) when citing information.\n\n"
        f"Forum posts:\n{context}\n\n"
        f"Question: {question}\n\nAnswer:"
    )

    response = await client.chat.completions.create(
        model=settings.RETRIEVE_LLM,
        messages=[{"role": "user", "content": prompt}]
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "sources": [
            {"id": str(post.id), "title": post.title}
            for post in sources
        ]
    }