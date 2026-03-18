from datetime import datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Float,
)
from sqlalchemy.orm import relationship

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    documents = relationship("Document", back_populates="uploader")
    groups = relationship("UserGroup", back_populates="user")
    chats = relationship("ChatHistory", back_populates="user")
    conversations = relationship("Conversation", back_populates="user")


class Group(Base):
    __tablename__ = "groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("UserGroup", back_populates="group")
    documents = relationship("Document", back_populates="group")


class UserGroup(Base):
    __tablename__ = "user_groups"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"))

    user = relationship("User", back_populates="groups")
    group = relationship("Group", back_populates="members")


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    size_bytes = Column(Integer, nullable=False)
    uploader_id = Column(Integer, ForeignKey("users.id"))
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)
    is_private = Column(Boolean, default=True)
    mime_type = Column(String(100), nullable=True)
    path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    uploader = relationship("User", back_populates="documents")
    group = relationship("Group", back_populates="documents")


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    sources = Column(Text, nullable=True)  # JSON string of sources metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="chats")


class Paper(Base):
    __tablename__ = "papers"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), unique=True)

    title = Column(String(255), nullable=True)
    authors = Column(String(255), nullable=True)
    year = Column(Integer, nullable=True)
    journal = Column(String(255), nullable=True)
    doi = Column(String(255), nullable=True)

    file_path = Column(String(500), nullable=True)
    profile_path = Column(String(500), nullable=True)

    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)


class StudentPaper(Base):
    __tablename__ = "student_papers"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(255), nullable=False)
    content_path = Column(String(500), nullable=False)

    created_at = Column(DateTime, default=datetime.utcnow)


class Conversation(Base):
    """
    One conversation = one research topic.
    """

    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Optional title, can be auto-filled from first user message
    title = Column(String(255), nullable=True)

    # Scope controls: literature collection and optional student paper
    collection_id = Column(Integer, nullable=True)
    student_paper_id = Column(Integer, ForeignKey("student_papers.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="conversations")
    student_paper = relationship("StudentPaper")
    messages = relationship(
        "Message",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="Message.created_at",
    )


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(
        Integer, ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )

    # user | assistant | system | tool
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)

    # JSON string of sources metadata (paper_id/module, etc.)
    sources = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    conversation = relationship("Conversation", back_populates="messages")