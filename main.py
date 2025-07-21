from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
from core.config import settings
from routers import auth, docs, query
from typing import Dict, List
from pydantic import BaseModel

# Define some test models
class TestQuery(BaseModel):
    question: str
    context: str = ""

class TestResponse(BaseModel):
    answer: str
    source: str = "test"

app = FastAPI(title="Internal Docs Q&A API")

# Add SessionMiddleware for OAuth
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY, same_site='lax', https_only=False)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(docs.router, prefix="/docs", tags=["docs"])
app.include_router(query.router, prefix="/query", tags=["query"])

@app.get("/")
async def root():
    return {"message": "Internal Docs Q&A API is running"}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.VERSION,
        "environment": "development"
    }

@app.post("/test/query", response_model=TestResponse)
async def test_query(query: TestQuery):
    """Test endpoint for question answering"""
    if not query.question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")
    
    return TestResponse(
        answer=f"This is a test answer for: {query.question}",
        source="test-database"
    )

@app.get("/test/sources")
async def test_sources() -> List[Dict]:
    """Test endpoint for listing available document sources"""
    return [
        {"id": "1", "name": "Company Handbook", "type": "notion"},
        {"id": "2", "name": "HR Policies", "type": "google-docs"},
        {"id": "3", "name": "Product Documentation", "type": "notion"}
    ] 