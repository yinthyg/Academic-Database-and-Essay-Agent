from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    username: Optional[str] = None


class UserBase(BaseModel):
    username: str


class UserCreate(UserBase):
    password: str
    is_admin: bool = False


class UserRead(UserBase):
    id: int
    is_admin: bool
    created_at: datetime

    class Config:
        from_attributes = True


class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None


class GroupCreate(GroupBase):
    pass


class GroupRead(GroupBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DocumentRead(BaseModel):
    id: int
    filename: str
    original_name: str
    size_bytes: int
    uploader_id: int
    group_id: Optional[int]
    is_private: bool
    mime_type: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ============ Document Detail ============


class DocumentChunk(BaseModel):
    chunk_index: int
    text: str


class DocumentChunksResponse(BaseModel):
    document_id: int
    total: int
    chunks: List[DocumentChunk]


class PaperBibliography(BaseModel):
    authors: str = ""
    year: str = ""
    title: str = ""
    venue: str = ""
    volume: str = ""
    issue: str = ""
    pages: str = ""
    doi: str = ""


class DocumentStructuredAnalysis(BaseModel):
    # 1) 元数据（9项）
    metadata: PaperBibliography
    # 2-20) 其余 19 项结构化输出
    core_problem: str = ""
    core_hypothesis: str = ""
    research_design: str = ""
    data_source: str = ""
    methods_and_tech: str = ""
    analysis_workflow: str = ""
    data_analysis: str = ""
    core_findings: str = ""
    experimental_results: str = ""
    supporting_results: str = ""
    final_conclusion: str = ""
    field_contribution: str = ""
    relevance_to_my_research: str = ""
    highlights_analysis: str = ""
    figures_tables_index: list = []
    personal_evaluation: str = ""
    questions_log: str = ""
    inspiration_thoughts: str = ""
    representative_references: list = []


class DocumentAnalysisResponse(BaseModel):
    document_id: int
    status: str  # "pending" | "ready" | "error"
    analysis: Optional[DocumentStructuredAnalysis] = None
    detail: Optional[str] = None


# ============ Batch Upload ============


class BatchUploadItem(BaseModel):
    filename: str
    ok: bool
    document: Optional[DocumentRead] = None
    error: Optional[str] = None


class BatchUploadResponse(BaseModel):
    total: int
    success: int
    failed: int
    items: List[BatchUploadItem]


class ChatHistoryRead(BaseModel):
    id: int
    question: str
    answer: str
    sources: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class RAGQueryRequest(BaseModel):
    question: str
    scope: str  # "private" | "groups" | "all"
    group_ids: Optional[List[int]] = None


class RAGQueryResponse(BaseModel):
    answer: str
    sources: list


class RAGCompareRequest(BaseModel):
    question: str
    document_ids: List[int]


class DashboardStats(BaseModel):
    total_documents: int
    total_storage_bytes: int
    total_indexed_chunks: int
    total_users: int
    total_groups: int
    recent_questions: int
    recent_documents: List[DocumentRead]


class PaperRead(BaseModel):
    id: int
    document_id: int
    title: Optional[str]
    authors: Optional[str]
    year: Optional[int]
    journal: Optional[str]
    doi: Optional[str]
    file_path: Optional[str]
    profile_path: Optional[str]
    owner_id: Optional[int]
    group_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class PaperChatRequest(BaseModel):
    paper_id: int
    question: str


class PaperCompareRequest(BaseModel):
    paper_ids: List[int]
    question: str


class StudentPaperRead(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime

    class Config:
        from_attributes = True


class StudentPaperDetail(StudentPaperRead):
    content: str


class StudentPaperCreateRequest(BaseModel):
    title: str


class StudentPaperSaveRequest(BaseModel):
    content: str


class MentorChatRequest(BaseModel):
    question: str


class MentorChatResponse(BaseModel):
    answer: str
    citations: List[str]
    sources: list


class ConversationBase(BaseModel):
    title: Optional[str] = None
    collection_id: Optional[int] = None
    student_paper_id: Optional[int] = None


class ConversationCreate(ConversationBase):
    pass


class ConversationRead(ConversationBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    role: str  # "user" | "assistant" | "system" | "tool"
    content: str
    sources: Optional[str] = None


class MessageCreate(MessageBase):
    pass


class MessageRead(MessageBase):
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True