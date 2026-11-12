
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import current_user
from ..database import get_db
from ..models import ChatConversation, ChatMessage, User
from ..services.health_data_crypto import (
    encrypt_health_text,
    decrypt_health_text
)
from ..services.health_chatbot import generate_health_reply


router = APIRouter(
    prefix="/api/chat",
    tags=["AI Health Chatbot"]
)


class ConversationCreate(BaseModel):
    title: Optional[str] = Field(default=None, max_length=160)
    language: str = Field(default="English", min_length=2, max_length=30)


class ChatMessageRequest(BaseModel):
    message: str = Field(min_length=1, max_length=3000)


def get_owned_conversation(
    db: Session,
    conversation_id: int,
    user_id: int
):
    conversation = (
        db.query(ChatConversation)
        .filter(
            ChatConversation.id == conversation_id,
            ChatConversation.user_id == user_id
        )
        .first()
    )

    if not conversation:
        raise HTTPException(
            status_code=404,
            detail="Conversation not found."
        )

    return conversation


@router.post("/conversations", status_code=201)
def create_conversation(
    payload: ConversationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    conversation = ChatConversation(
        user_id=user.id,
        title=(payload.title or "New conversation").strip()[:160],
        language=payload.language.strip(),
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return {
        "id": conversation.id,
        "title": conversation.title,
        "language": conversation.language,
        "created_at": conversation.created_at
    }


@router.get("/conversations")
def list_conversations(
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    conversations = (
        db.query(ChatConversation)
        .filter(ChatConversation.user_id == user.id)
        .order_by(ChatConversation.updated_at.desc())
        .limit(100)
        .all()
    )

    return [
        {
            "id": item.id,
            "title": item.title,
            "language": item.language,
            "created_at": item.created_at,
            "updated_at": item.updated_at
        }
        for item in conversations
    ]


@router.get("/conversations/{conversation_id}")
def get_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    conversation = get_owned_conversation(
        db,
        conversation_id,
        user.id
    )

    records = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation.id)
        .order_by(ChatMessage.created_at.asc(), ChatMessage.id.asc())
        .limit(200)
        .all()
    )

    return {
        "id": conversation.id,
        "title": conversation.title,
        "language": conversation.language,
        "created_at": conversation.created_at,
        "messages": [
            {
                "id": item.id,
                "role": item.role,
                "content": decrypt_health_text(item.encrypted_content),
                "created_at": item.created_at
            }
            for item in records
        ]
    }


@router.post("/conversations/{conversation_id}/messages", status_code=201)
async def send_chat_message(
    conversation_id: int,
    payload: ChatMessageRequest,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    conversation = get_owned_conversation(
        db,
        conversation_id,
        user.id
    )

    user_text = payload.message.strip()

    if not user_text:
        raise HTTPException(
            status_code=422,
            detail="Message cannot be empty."
        )

    previous_records = (
        db.query(ChatMessage)
        .filter(ChatMessage.conversation_id == conversation.id)
        .order_by(ChatMessage.created_at.desc(), ChatMessage.id.desc())
        .limit(12)
        .all()
    )

    previous_records.reverse()

    context = []

    for item in previous_records:
        context.append({
            "role": item.role,
            "content": decrypt_health_text(item.encrypted_content)
        })

    context.append({
        "role": "user",
        "content": user_text
    })

    try:
        reply = await generate_health_reply(
            messages=context,
            language=conversation.language
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=502,
            detail=str(exc)
        ) from exc

    now_time = datetime.now(timezone.utc)

    user_message = ChatMessage(
        conversation_id=conversation.id,
        role="user",
        encrypted_content=encrypt_health_text(user_text),
        created_at=now_time
    )

    assistant_message = ChatMessage(
        conversation_id=conversation.id,
        role="assistant",
        encrypted_content=encrypt_health_text(reply),
        created_at=now_time
    )

    if conversation.title == "New conversation":
        conversation.title = user_text[:60]

    conversation.updated_at = now_time

    try:
        db.add(user_message)
        db.add(assistant_message)
        db.commit()
        db.refresh(user_message)
        db.refresh(assistant_message)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail="Could not save chat messages."
        ) from exc

    return {
        "conversation_id": conversation.id,
        "user_message": {
            "id": user_message.id,
            "role": "user",
            "content": user_text,
            "created_at": user_message.created_at
        },
        "assistant_message": {
            "id": assistant_message.id,
            "role": "assistant",
            "content": reply,
            "created_at": assistant_message.created_at
        },
        "disclaimer": (
            "MediBridge AI provides general health information only. "
            "It does not provide medical diagnosis or replace a doctor."
        )
    }


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(current_user)
):
    conversation = get_owned_conversation(
        db,
        conversation_id,
        user.id
    )

    db.query(ChatMessage).filter(
        ChatMessage.conversation_id == conversation.id
    ).delete(synchronize_session=False)

    db.delete(conversation)
    db.commit()

    return None
