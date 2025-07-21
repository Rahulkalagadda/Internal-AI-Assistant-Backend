# Internal Docs Q&A Backend

A FastAPI backend for the Internal Docs Q&A system that integrates with Google Docs and Notion to provide a natural language interface to your team's documentation.

## Features

- 🔐 Google OAuth 2.0 authentication
- 📝 Notion integration (manual token)
- 📄 Document ingestion from:
  - Google Docs
  - Notion pages and databases
- 🔍 RAG-powered document search using:
  - ChromaDB (vector store)
  - HuggingFace Embeddings (all-MiniLM-L6-v2)
  - LangChain (orchestration)
- 🤖 Slack integration for queries

## Setup

1. Clone the repository and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

2. Create a `.env` file with the following variables:
```env
# Application
SECRET_KEY=your-secret-key-here
CORS_ORIGINS=http://localhost:3000,http://localhost:5173

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# OpenAI (for RAG)
OPENAI_API_KEY=your-openai-api-key

# Slack (optional)
SLACK_SIGNING_SECRET=your-slack-signing-secret
```

3. Run the development server:
```bash
uvicorn main:app --reload
```

## API Endpoints

### Authentication
- `POST /auth/login/google` - Initiate Google OAuth flow
- `GET /auth/google/callback` - Handle Google OAuth callback
- `POST /auth/notion` - Set Notion integration token
- `GET /auth/me` - Get current user info

### Document Management
- `POST /docs/index/notion` - Index Notion documents
- `POST /docs/index/google` - Index Google Docs documents

### Querying
- `POST /query` - Query indexed documents
- `GET /query/similar` - Get similar questions

### Slack Integration
- `POST /slack/query` - Handle Slack slash command queries

## Deployment

### Railway

1. Create a new project on Railway
2. Connect your GitHub repository
3. Add the required environment variables
4. Deploy!

### Render

1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Set the following:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add the environment variables
5. Deploy!

## Development

### Project Structure
```
backend/
├── core/
│   └── config.py         # Configuration settings
├── models/
│   └── auth.py          # Pydantic models
├── routers/
│   ├── auth.py          # Authentication routes
│   ├── docs.py          # Document management routes
│   ├── query.py         # Query routes
│   └── slack.py         # Slack integration routes
├── services/
│   ├── auth.py          # Authentication service
│   ├── document.py      # Document processing service
│   └── rag.py           # RAG service
├── main.py              # FastAPI application
└── requirements.txt     # Python dependencies
```

### Adding New Features

1. Create new models in `models/`
2. Add new services in `services/`
3. Create new routes in `routers/`
4. Update configuration in `core/config.py`
5. Add dependencies to `requirements.txt`

## Security Notes

- Store tokens securely in production (use a proper database)
- Use environment variables for sensitive data
- Keep the OpenAI API key secure
- Implement rate limiting for production use
- Add proper error handling and logging
- Use HTTPS in production

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request 