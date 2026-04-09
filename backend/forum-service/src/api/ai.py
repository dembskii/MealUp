from fastapi import APIRouter, HTTPException, Depends, status
from sqlmodel.ext.asyncio.session import AsyncSession
from typing import Dict
from common.auth_guard import require_auth
from src.db.main import get_session

from src.services.rag_service import ask
from src.validators.rag import AskRequest, AskResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()



@router.post("/ai/ask", response_model=AskResponse, status_code=status.HTTP_200_OK)
async def rag_query(
    request: AskRequest,
    session: AsyncSession = Depends(get_session),
    token_payload: Dict = Depends(require_auth)
):
    """Ask RAG system for forum data"""

    try:      
        if not request.question.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question cannot be empty"
            )
           
        logger.info(f"User {token_payload.get('sub')} asked: {request.question}")

        result = await ask(session, request.question, request.top_k)

        if not result.get("sources"):
            logger.warning(f"No sources found for question: {request.question}")
        
        return result

    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid input: {str(e)}"
        )
    
    except ConnectionError as e:
        logger.error(f"API connection error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable"
        )

    except HTTPException:
        raise
    
    except Exception as e:
        logger.error(f"Unexpected error in rag_query: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )    


