from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import cast
from core.dependencies import get_current_active_user, get_current_user
from dependency_injector.wiring import inject, Provide  # ← only this
from schema.chat_schema import ChatRequest, ChatResponse
from services.agent_service import AgentService
from model.user_model import User
from core.container import Container

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/", response_model=ChatResponse)
@inject
async def chat_root(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service])
):
    """Send a message to the AI agent — requires valid token."""
    print(f"[Chat Route] Received message from user {current_user.user_id}: {body.message}")
    try:
        # ── Step 1: ensure conversation exists before replying ──
        conversation_id = await agent_service.start_conversation(
            user_id=current_user.user_id ,
            conversation_id=body.conversation_id
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

@router.post("/message", response_model=ChatResponse)
@inject
async def chat(
    body: ChatRequest,
    current_user: User = Depends(get_current_user),
    agent_service: AgentService = Depends(Provide[Container.agent_service])
):
    """Send a message to the AI agent — requires valid token."""
    print(f"[Chat Route] Received message from user {current_user.user_id}: {body.message}")
    try:
        print(f"[Chat Route] Received message from user {current_user.user_id}: {body.message}")
        # ── Step 1: ensure conversation exists before replying ──
        conversation_id = await agent_service.start_conversation(
            user_id=current_user.user_id ,
            conversation_id=body.conversation_id
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