from typing import List, Dict, Any, Optional
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.llms import HuggingFaceEndpoint
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from models.rag import RAGRequest, RAGResponse, SearchResult, IndexConfig
from models.docs import DocumentMetadata, SourceType
from core.config import settings
from fastapi import HTTPException, status
import os
import json
from transformers import pipeline

class RAGService:
    def __init__(self):
        if not settings.HUGGINGFACE_API_TOKEN:
            print("Warning: HUGGINGFACE_API_TOKEN not set. Running model locally.")
        self.config = IndexConfig()
        self.embeddings = HuggingFaceEmbeddings(
            model_name=self.config.embedding_model
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.config.chunking.chunk_size,
            chunk_overlap=self.config.chunking.chunk_overlap,
            length_function=len if self.config.chunking.length_function == "char" else None,
        )
        if os.path.exists("chroma_index"):
            self.vector_store = Chroma(persist_directory="chroma_index", embedding_function=self.embeddings)
        else:
            self.vector_store = Chroma.from_texts(
                ["initialization"], 
                self.embeddings,
            )
        # Use local pipeline for text2text-generation
        self.llm = pipeline(
            "text2text-generation",
            model="google/flan-t5-small"
        )
        self.qa_template = """You are an AI assistant helping with internal company documentation.\nUse the following pieces of context to answer the question at the end.\nIf you don't know the answer, just say that you don't know. Don't try to make up an answer.\nAlways include relevant source information in your answer.\n\nContext: {context}\n\nQuestion: {question}\n\nAnswer: Let me help you with that based on the available documentation."""
        self.qa_prompt = PromptTemplate(
            template=self.qa_template,
            input_variables=["context", "question"]
        )
        retriever = self.vector_store.as_retriever(search_kwargs={"k": 3})
        self.retriever = retriever

    async def query(self, request: RAGRequest) -> RAGResponse:
        try:
            # Retrieve context
            docs = self.vector_store.similarity_search(request.question, k=3)
            # Fallback: If no docs or only initialization/default text, return a helpful message
            if not docs or all(doc.page_content.strip().lower() in ["initialization", "initialization text", ""] for doc in docs):
                return RAGResponse(
                    answer=(
                        "Hmm, I couldn't find anything in your documents that answers that. "
                        "Could you tell me a bit more, or maybe ask in a different way? "
                        "For example, you can ask: 'What is our vacation policy?' or 'How do I submit an expense report?'. "
                        "If you want, I can help you add more documents too! 😊"
                    ),
                    sources=[],
                    context_used=request.context,
                    metadata={
                        "model": "google/flan-t5-small",
                        "num_sources_used": 0,
                        "note": "No relevant context found."
                    }
                )
            context = "\n".join([doc.page_content for doc in docs])
            prompt = self.qa_prompt.format(context=context, question=request.question)
            answer = self.llm(prompt, max_new_tokens=256)[0]["generated_text"]
            sources = []
            for doc in docs:
                metadata = doc.metadata or {}
                # Provide default values if missing
                source_type = metadata.get("source_type", "unknown")
                source_id = metadata.get("source_id", "init")
                title = metadata.get("title", "Initialization Document")
                sources.append(SearchResult(
                    text=doc.page_content,
                    metadata=DocumentMetadata(
                        source_type=source_type,
                        source_id=source_id,
                        title=title
                    ),
                    score=getattr(doc, "score", 1.0)
                ))
            return RAGResponse(
                answer=answer,
                sources=sources,
                context_used=request.context,
                metadata={
                    "model": "google/flan-t5-small",
                    "num_sources_used": len(sources)
                }
            )
        except Exception as e:
            print("RAGService error:", repr(e))
            return RAGResponse(
                answer="I apologize, but I encountered an error while processing your question. Please try again.",
                sources=[],
                metadata={"error": str(e)}
            )
    
    async def similar_questions(self, question: str, k: int = 5) -> List[SearchResult]:
        """Find similar questions from the vector store"""
        try:
            results = self.vector_store.similarity_search_with_score(
                question,
                k=k
            )
            
            similar_results = []
            for doc, score in results:
                metadata = DocumentMetadata(**doc.metadata)
                similar_results.append(SearchResult(
                    text=doc.page_content,
                    metadata=metadata,
                    score=float(score)
                ))
            
            return similar_results
            
        except Exception:
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        return {
            "total_documents": len(self.vector_store.docstore._dict),
            "embedding_model": self.config.embedding_model,
            "chunking_config": self.config.chunking.dict(),
            "similarity_metric": self.config.similarity_metric
        } 