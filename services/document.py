from typing import List, Optional
# from langchain_community.document_loaders import NotionDirectoryLoader  # Not supported on Windows due to 'pwd' module
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from core.config import settings
from notion_client import Client as NotionClient
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import os
import json
from langchain_community.document_loaders.confluence import ConfluenceLoader
import requests

class DocumentService:
    def __init__(self):
        self.embeddings = HuggingFaceEmbeddings(
            model_name=settings.EMBEDDING_MODEL_NAME
        )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len,
        )
        # Initialize empty Chroma index
        self.vector_store = Chroma.from_texts(
            ["initialization text"],
            self.embeddings,
            persist_directory="chroma_index"
        )
        # Remove initialization text
        if os.path.exists("chroma_index"):
            self.vector_store = Chroma(persist_directory="chroma_index", embedding_function=self.embeddings)
    
    async def process_notion_pages(self, token: str, database_id: Optional[str] = None) -> List[str]:
        """Process Notion pages and store in vector database"""
        notion = NotionClient(auth=token)
        
        # Get pages from database or user's workspace
        if database_id:
            response = notion.databases.query(database_id=database_id)
            pages = response.get('results', [])
        else:
            # Get all pages user has access to
            response = notion.search()
            pages = response.get('results', [])
        
        documents = []
        for page in pages:
            # Extract text content
            blocks = notion.blocks.children.list(block_id=page['id'])
            content = self._extract_notion_content(blocks['results'])
            
            # Create document with metadata
            doc = {
                'content': content,
                'metadata': {
                    'source': 'notion',
                    'page_id': page['id'],
                    'title': page.get('properties', {}).get('title', {}).get('title', [{}])[0].get('text', {}).get('content', 'Untitled'),
                    'url': page.get('url', '')
                }
            }
            documents.append(doc)
        
        # Split and store documents
        return await self._process_documents(documents)
    
    def fetch_google_doc_as_text(self, access_token: str, document_id: str) -> str:
        url = f"https://www.googleapis.com/drive/v3/files/{document_id}/export"
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        params = {
            "mimeType": "text/plain"
        }
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.text

    async def process_google_doc(self, credentials_dict: dict, document_id: str) -> List[str]:
        """Process a single Google Doc using Drive API and store in vector database"""
        access_token = credentials_dict["token"]
        content = self.fetch_google_doc_as_text(access_token, document_id)
        doc_info = {
            'content': content,
            'metadata': {
                'source': 'google_docs',
                'doc_id': document_id,
                'title': f"Google Doc {document_id}",
                'url': f"https://docs.google.com/document/d/{document_id}/edit"
            }
        }
        # Split and store document
        return await self._process_documents([doc_info])
    
    async def process_confluence_docs(self, base_url: str, username: str, api_token: str, space_key: str = None) -> list:
        """Process Confluence pages and store in vector database"""
        loader = ConfluenceLoader(
            url=base_url,
            username=username,
            api_token=api_token,
            space_key=space_key
        )
        docs = loader.load()
        documents = []
        for doc in docs:
            documents.append({
                'content': doc.page_content,
                'metadata': {
                    'source_type': 'confluence',
                    'page_id': doc.metadata.get('id', ''),
                    'title': doc.metadata.get('title', 'Untitled'),
                    'url': doc.metadata.get('url', '')
                }
            })
        return await self._process_documents(documents)
    
    async def _process_documents(self, documents: List[dict]) -> List[str]:
        """Split documents and store in vector database"""
        doc_ids = []
        
        for doc in documents:
            # Split text into chunks
            splits = self.text_splitter.split_text(doc['content'])
            
            # Add metadata to each chunk
            texts_with_metadata = [
                {
                    'text': split,
                    'metadata': {
                        **doc['metadata'],
                        'chunk_index': i
                    }
                }
                for i, split in enumerate(splits)
            ]
            
            # Add to vector store
            self.vector_store.add_texts(
                texts=[t['text'] for t in texts_with_metadata],
                metadatas=[t['metadata'] for t in texts_with_metadata]
            )
            
            # Save the index
            self.vector_store.persist()
            
            # Add document ID to list
            doc_ids.append(doc['metadata']['doc_id'])
        
        return doc_ids
    
    def _extract_notion_content(self, blocks: List[dict]) -> str:
        """Extract text content from Notion blocks"""
        content = []
        for block in blocks:
            block_type = block['type']
            if block_type == 'paragraph':
                text = block.get('paragraph', {}).get('text', [{}])[0].get('text', {}).get('content', '')
                content.append(text)
            elif block_type == 'heading_1':
                text = block.get('heading_1', {}).get('text', [{}])[0].get('text', {}).get('content', '')
                content.append(f"# {text}")
            elif block_type == 'heading_2':
                text = block.get('heading_2', {}).get('text', [{}])[0].get('text', {}).get('content', '')
                content.append(f"## {text}")
            elif block_type == 'heading_3':
                text = block.get('heading_3', {}).get('text', [{}])[0].get('text', {}).get('content', '')
                content.append(f"### {text}")
        return '\n\n'.join(content)
    
    def _extract_google_doc_content(self, document: dict) -> str:
        """Extract text content from Google Doc"""
        content = []
        for element in document.get('body', {}).get('content', []):
            if 'paragraph' in element:
                paragraph = element['paragraph']
                for elem in paragraph.get('elements', []):
                    if 'textRun' in elem:
                        content.append(elem['textRun'].get('content', ''))
        return '\n'.join(content) 