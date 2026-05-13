from fastapi import APIRouter, HTTPException, Depends
from core.dependencies import get_current_active_user
from schema.chat_schema import ChatRequest, ChatResponse
from services.agent_service import AgentService
from model.user_model import User

router = APIRouter(prefix="/chat", tags=["Chat"])
agent_service = AgentService()


@router.post("/", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_active_user)
):
    """Send a message to the AI agent — requires valid token."""
    try:
        # ── Step 1: ensure conversation exists before replying ──
        conversation_id = agent_service.start_conversation(
            user_id=current_user.user_id  # ← pass existing ID if provided
        )

        # ── Step 2: send message to agent ──────────────────────
        reply = await agent_service.reply(
            user_id=current_user.user_id,
            conversation_id=conversation_id,
            user_message=body.message
        )

        return ChatResponse(
            user_id=current_user.user_id,
            user_name=current_user.name,
            conversation_id=conversation_id,
            response=reply
        )

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))