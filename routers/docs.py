from fastapi import APIRouter, Depends, HTTPException, status
from typing import Optional, List
from pydantic import BaseModel
from services.document import DocumentService
from services.auth import AuthService
from models.auth import UserResponse

router = APIRouter()
doc_service = DocumentService()
auth_service = AuthService()

class IndexResponse(BaseModel):
    message: str
    document_ids: List[str]

class NotionIndexRequest(BaseModel):
    database_id: Optional[str] = None

class ConfluenceIndexRequest(BaseModel):
    base_url: str
    username: str
    api_token: str
    space_key: Optional[str] = None

class GoogleIndexRequest(BaseModel):
    google_token: str
    document_id: str

@router.post("/index/notion", response_model=IndexResponse)
async def index_notion_docs(
    request: NotionIndexRequest,
    current_user: UserResponse = Depends(auth_service.get_current_user)
):
    """Index Notion documents for the authenticated user"""
    try:
        # Get Notion token
        token = auth_service.get_notion_token(current_user.id)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Notion token not found. Please connect Notion first."
            )
        # Process Notion pages
        doc_ids = await doc_service.process_notion_pages(
            token=token,
            database_id=request.database_id
        )
        return IndexResponse(
            message="Successfully indexed Notion documents",
            document_ids=doc_ids
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/index/google", response_model=IndexResponse)
async def index_google_docs(
    request: GoogleIndexRequest
):
    """Index a specific Google Doc by token and document ID (for prototyping/testing)"""
    try:
        credentials_dict = {
            "token": request.google_token,
            "refresh_token": "",  # Add your real refresh token if available
            "token_uri": "https://oauth2.googleapis.com/token",
            "client_id": "YOUR_GOOGLE_CLIENT_ID",  # Replace with your real client_id
            "client_secret": "YOUR_GOOGLE_CLIENT_SECRET",  # Replace with your real client_secret
            "scopes": ["https://www.googleapis.com/auth/documents.readonly"]
        }
        doc_ids = await doc_service.process_google_doc(credentials_dict, request.document_id)
        return IndexResponse(
            message="Successfully indexed Google Doc",
            document_ids=doc_ids
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

@router.post("/index/confluence", response_model=IndexResponse)
async def index_confluence_docs(
    request: ConfluenceIndexRequest,
    current_user: UserResponse = Depends(auth_service.get_current_user)
):
    """Index Confluence documents for the authenticated user"""
    try:
        doc_ids = await doc_service.process_confluence_docs(
            base_url=request.base_url,
            username=request.username,
            api_token=request.api_token,
            space_key=request.space_key
        )
        return IndexResponse(
            message="Successfully indexed Confluence documents",
            document_ids=doc_ids
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        ) 