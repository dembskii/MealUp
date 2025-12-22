# import asyncio
# import logging
# from datetime import datetime
# from src.db.main import get_session
# from src.services.post_service import PostService

# logger = logging.getLogger(__name__)


# async def update_trending_coefficients_task():
#     """Background task to update trending coefficients every hour"""
#     while True:
#         try:
#             logger.info("Starting trending coefficients update...")
#             async for session in get_session():
#                 updated = await PostService.recalculate_all_trending_coefficients(session)
#                 logger.info(f"Updated {updated} posts at {datetime.now()}")
#                 break  # Exit after first session
#         except Exception as e:
#             logger.error(f"Error in trending update task: {str(e)}")
        
#         # Wait 1 hour before next update
#         await asyncio.sleep(3600)


# def start_background_tasks():
#     """Start all background tasks"""
#     asyncio.create_task(update_trending_coefficients_task())