from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
from models.rag import RAGRequest, RAGResponse, SearchResult
from models.auth import UserResponse
from services.rag import RAGService
from services.auth import AuthService

router = APIRouter()
rag_service = RAGService()
auth_service = AuthService()

@router.post("", response_model=RAGResponse)
async def query_docs(
    request: RAGRequest,
    # Temporarily commenting out authentication for testing
    # current_user: UserResponse = Depends(auth_service.get_current_user)
):
    """Query indexed documents"""
    try:
        return await rag_service.query(request)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/similar", response_model=List[SearchResult])
async def get_similar_questions(
    question: str,
    k: int = 5,
    # Temporarily commenting out authentication for testing
    # current_user: UserResponse = Depends(auth_service.get_current_user)
):
    """Get similar questions from indexed documents"""
    try:
        return await rag_service.similar_questions(question, k)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.get("/stats")
async def get_index_stats(
    # Temporarily commenting out authentication for testing
    # current_user: UserResponse = Depends(auth_service.get_current_user)
) -> Dict[str, Any]:
    """Get statistics about the vector store"""
    return rag_service.get_stats() 