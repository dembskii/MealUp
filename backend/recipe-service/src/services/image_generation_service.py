import random
import logging
from datetime import datetime
import httpx
from src.db.mongodb import get_database
from src.core.config import settings

logger = logging.getLogger(__name__)



LIGHTING = [
    "soft natural window light",
    "warm golden hour sunlight",
    "bright studio lighting",
    "moody candlelight ambiance",
    "diffused overcast daylight",
    "dramatic side lighting with deep shadows",
    "cool blue-toned morning light",
    "warm overhead pendant light",
]

BACKGROUND = [
    "rustic wooden table",
    "white marble countertop",
    "dark slate surface",
    "linen tablecloth with subtle texture",
    "old farmhouse kitchen",
    "modern minimalist kitchen",
    "outdoor garden picnic setting",
    "mediterranean tiled surface",
]

STYLE = [
    "professional food photography",
    "editorial magazine style",
    "cozy home-cooking aesthetic",
    "fine-dining plating",
    "rustic farmhouse style",
    "vibrant street-food look",
    "Michelin-star presentation",
    "casual Instagram flat-lay",
]

MOOD = [
    "inviting and appetizing",
    "elegant and sophisticated",
    "warm and comforting",
    "fresh and vibrant",
    "rich and indulgent",
    "light and healthy",
    "festive and celebratory",
    "simple and wholesome",
]


OPENROUTER_URL = settings.OPENROUTER_URL
MODEL = settings.MODEL


def _build_prompt(recipe_name: str) -> str:
    """Build a randomized image-generation prompt for the given recipe."""
    lighting = random.choice(LIGHTING)
    background = random.choice(BACKGROUND)
    style = random.choice(STYLE)
    mood = random.choice(MOOD)

    return (
            f"""
                A stunning food photography shot of {recipe_name}, 
                {style},
                {lighting},
                {background},
                {mood},
                the dish fills most of the frame with beautiful detail,
                ultra-realistic, photorealistic,
                shot with a Canon EF 85mm f/1.8 lens,
                shallow depth of field with soft blurred background,
                warm inviting colors, natural home cooking feel,
                appetizing and delicious looking,
                no text, no titles, no watermarks
            """
    )


async def generate_recipe_image(recipe_id: str, recipe_name: str) -> None:
    """
    Generate an AI image for a recipe via OpenRouter and persist the
    base64 data-URL in MongoDB.
    This function is designed to be fired as a background task
    (asyncio.create_task) so it never blocks the HTTP response.
    """
    logger.info(f"Starting image generation for recipe {recipe_id} ({recipe_name})")

    api_key = settings.OPEN_ROUTER_API_KEY
    if not api_key:
        logger.warning("OPEN_ROUTER_API_KEY is not set — skipping image generation")
        return

    prompt = _build_prompt(recipe_name)
    logger.debug(f"Image prompt: {prompt}")

    payload = {
        "model": MODEL,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt,
                    }
                ],
            }
        ],
        "modalities": ["image"],
        "image": {
            "size": "512x512",
        },
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout = 120.0) as client:
            response = await client.post(
                OPENROUTER_URL,
                json = payload,
                headers = headers,
            )
            response.raise_for_status()
            result = response.json()

        base64_data_url: str = (
            result["choices"][0]["message"]["images"][0]["image_url"]["url"]
        )

        if not base64_data_url:
            logger.error(f"Empty image URL in OpenRouter response for recipe {recipe_id}")
            return

        #Saving in database
        db = get_database()
        collection = db[settings.RECIPES_COLLECTION]
        await collection.update_one(
            {"_id": recipe_id},
            {
                "$set": {
                    "image": base64_data_url,
                    "_updated_at": datetime.utcnow(),
                }
            },
        )
        logger.info(f"Image saved for recipe {recipe_id} ({len(base64_data_url)} chars)")

    except httpx.HTTPStatusError as e:
        logger.error(
            f"OpenRouter HTTP error for recipe {recipe_id}: "
            f"{e.response.status_code} — {e.response.text}"
        )
    except KeyError as e:
        logger.error(
            f"Unexpected OpenRouter response structure for recipe {recipe_id}: "
            f"missing key {e}. Full response: {result}"
        )
    except Exception as e:
        logger.error(
            f"Image generation failed for recipe {recipe_id}: {type(e).__name__}: {e}",
            exc_info=True,
        )