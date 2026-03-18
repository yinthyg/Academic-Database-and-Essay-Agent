from typing import List, Optional

from sqlalchemy.orm import Session

from . import models, schemas


def list_conversations(db: Session, user: models.User) -> List[models.Conversation]:
    return (
        db.query(models.Conversation)
        .filter(models.Conversation.user_id == user.id)
        .order_by(models.Conversation.created_at.desc())
        .all()
    )


def get_conversation_or_404(
    db: Session, user: models.User, conversation_id: int
) -> models.Conversation:
    convo = db.query(models.Conversation).get(conversation_id)
    if not convo:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="会话不存在")
    if (not user.is_admin) and convo.user_id != user.id:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="无权访问该会话")
    return convo


def create_conversation(
    db: Session,
    user: models.User,
    convo_in: schemas.ConversationCreate,
) -> models.Conversation:
    convo = models.Conversation(
        user_id=user.id,
        title=convo_in.title,
        collection_id=convo_in.collection_id,
        student_paper_id=convo_in.student_paper_id,
    )
    db.add(convo)
    db.commit()
    db.refresh(convo)
    return convo


def list_messages(
    db: Session,
    conversation: models.Conversation,
    limit: int = 100,
) -> List[models.Message]:
    q = (
        db.query(models.Message)
        .filter(models.Message.conversation_id == conversation.id)
        .order_by(models.Message.created_at.asc())
    )
    if limit:
        q = q.limit(limit)
    return q.all()


def add_message(
    db: Session,
    conversation: models.Conversation,
    message_in: schemas.MessageCreate,
) -> models.Message:
    msg = models.Message(
        conversation_id=conversation.id,
        role=message_in.role,
        content=message_in.content,
        sources=message_in.sources,
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    # TODO: later hook here to call Research Agent and append assistant messages.

    return msg

