from fastapi import APIRouter, Request, HTTPException
from app.schemas.request_response import ChatRequest, ChatResponse

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: Request, body: ChatRequest):
    chatbot_service = request.app.state.chatbot_service
    
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")
        
    try:
        response = chatbot_service.process_message(body.message)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing message: {str(e)}")
