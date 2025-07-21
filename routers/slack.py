from fastapi import APIRouter, HTTPException, status, Request
from typing import Dict, Any
from services.rag import RAGService
import json
import hmac
import hashlib
import time
from core.config import settings

router = APIRouter()
rag_service = RAGService()

def verify_slack_signature(request: Request) -> bool:
    """Verify that the request came from Slack"""
    slack_signing_secret = settings.SLACK_SIGNING_SECRET.encode('utf-8')
    slack_signature = request.headers.get('X-Slack-Signature', '')
    slack_timestamp = request.headers.get('X-Slack-Request-Timestamp', '')
    
    if abs(time.time() - int(slack_timestamp)) > 60 * 5:
        return False
        
    sig_basestring = f"v0:{slack_timestamp}:{request.body.decode('utf-8')}"
    my_signature = 'v0=' + hmac.new(
        slack_signing_secret,
        sig_basestring.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(my_signature, slack_signature)

@router.post("/query")
async def slack_query(request: Request) -> Dict[str, Any]:
    """Handle Slack slash command queries"""
    try:
        # Verify request is from Slack
        if not verify_slack_signature(request):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Slack signature"
            )
        
        # Parse request body
        form_data = await request.form()
        question = form_data.get('text', '')
        
        if not question:
            return {
                "response_type": "ephemeral",
                "text": "Please provide a question after the slash command."
            }
        
        # Query RAG system
        result = await rag_service.query(question)
        
        # Format response for Slack
        blocks = [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": result["answer"]
                }
            }
        ]
        
        # Add sources if available
        if result.get("sources"):
            source_text = "*Sources:*\n"
            for source in result["sources"]:
                source_text += f"• <{source['url']}|{source['title']}> ({source['source_type']})\n"
            
            blocks.append({
                "type": "context",
                "elements": [
                    {
                        "type": "mrkdwn",
                        "text": source_text
                    }
                ]
            })
        
        return {
            "response_type": "in_channel",
            "blocks": blocks
        }
        
    except Exception as e:
        return {
            "response_type": "ephemeral",
            "text": f"Error processing your request: {str(e)}"
        } 