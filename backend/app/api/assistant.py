
import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.db.session import get_db
from app.services.rag_service import ask_campus_assistant

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/assistant",
    tags=["AI Assistant"]
)


class AssistantQuery(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        max_length=1000,
        description="Ask a question about campus lost and found reports"
    )


@router.post("/ask")
def ask_assistant(
    request: AssistantQuery,
    db: Session = Depends(get_db)
):
    try:
        return ask_campus_assistant(
            db=db,
            question=request.question.strip()
        )

    except SQLAlchemyError:
        logger.exception("RAG database retrieval failed")
        raise HTTPException(
            status_code=503,
            detail="Unable to retrieve campus reports"
        )

    except RuntimeError:
        logger.exception("RAG service configuration or generation error")
        raise HTTPException(
            status_code=503,
            detail="AI assistant is temporarily unavailable"
        )

    except Exception:
        logger.exception("Unexpected AI assistant error")
        raise HTTPException(
            status_code=500,
            detail="Unable to process your question"
        )
