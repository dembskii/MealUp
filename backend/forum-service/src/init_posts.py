import asyncio
import logging
import uuid
import random
from typing import List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from src.db.main import engine
from src.models.post import Post
from src.services.embedding_service import generate_embedding, build_post_text

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOPICS = [
    "Weight Loss", "Muscle Gain", "Supplements", "Tips & Tricks", 
    "Strength Training", "Vegan Diet", "Keto Diet", "Marathon Prep", 
    "Recovery", "Intermittent Fasting", "Calisthenics", "Home Workouts", 
    "Yoga and Flexibility", "Powerlifting", "Cardio Training", "Meal Prep"
]

ADJECTIVES = [
    "Best", "Proven", "Simple", "My", "Critical", "Quick", 
    "Ultimate", "Effective", "Brutal", "Daily", "Intense", 
    "Healthy", "Tasty", "Beginner", "Advanced", "Essential"
]

NOUNS = [
    "workout routine", "summer diet", "beginner tip", "opinion on creatine", 
    "dinner recipe", "stretching guide", "meal prep strategy", 
    "protein powder review", "leg day workout", "morning mobility flow", 
    "pre-workout snack", "recovery protocol", "hydration plan", "mindset shifts"
]

def generate_mock_posts(count: int = 100) -> List[Post]:
    """
    Generates a specified number of mock posts with random titles, content, and tags.
    """
    posts = []
    mock_author_id = uuid.uuid4()
    
    for i in range(count):
        topic = random.choice(TOPICS)
        adj = random.choice(ADJECTIVES)
        noun = random.choice(NOUNS)
        
        title = f"{adj} {noun.title()} - {topic} #{i+1}"
        content = (
            f"Have you ever wondered about the {noun}? "
            f"In today's post, I want to discuss a topic related to {topic}. "
            "Please share your thoughts in the comments. Let's start a discussion!"
        )
        
        tags = [topic.lower().replace(" ", "-"), noun.split()[0].lower(), "discussion"]
        
        post = Post(
            author_id=mock_author_id,
            title=title,
            content=content,
            tags=tags,
            total_likes=random.randint(0, 50),
            views_count=random.randint(10, 200)
        )
        posts.append(post)
    return posts

async def seed_posts(session: AsyncSession, mock_posts: List[Post]) -> None:
    """
    Generates an embedding for each document using the RAG service and saves it to the database.
    Generation is partially batched to avoid overwhelming the API.
    """
    logger.info(f"Starting to save {len(mock_posts)} posts with RAG embeddings...")
    
    saved_count = 0
    for post in mock_posts:
        post_text = build_post_text(post)
        
        embedding = await generate_embedding(post_text)
        if embedding:
            post.embedding = embedding
        else:
            logger.warning(f"Failed to generate embedding for post: {post.title}")
            
        session.add(post)
        saved_count += 1
        
        if saved_count % 10 == 0:
            logger.info(f"Generated embeddings and prepared {saved_count}/{len(mock_posts)} posts...")
            await session.commit()
    
    await session.commit()
    logger.info("Successfully finished initializing posts database!")


async def init_posts() -> None:
    """
    Main orchestration function to check database state and initialize dummy data.
    """
    logger.info("Checking state of the 'posts' table in forum-service...")
    
    async with AsyncSession(engine) as session:
        result = await session.exec(select(Post).limit(1))
        existing_post = result.first()
        
        if existing_post:
            logger.info("Posts are already initialized. Skipping embedding generation and database seeding.")
            return

        mock_posts = generate_mock_posts(count=100)
        await seed_posts(session, mock_posts)

if __name__ == "__main__":
    asyncio.run(init_posts())