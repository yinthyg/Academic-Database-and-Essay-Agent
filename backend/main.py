from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import os  # 添加 os 模块用于路径处理

from fastapi import (
    Depends,
    FastAPI,
    File,
    HTTPException,
    UploadFile,
    status,
    Request,
    Query,
    Header,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import StreamingResponse, FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from . import auth, models, schemas
from .config import settings
from .agent import ResearchAgent
from .conversation_service import (
    add_message,
    create_conversation,
    get_conversation_or_404,
    list_conversations,
    list_messages,
)
from .database import Base, engine, get_db
from .document_processing import detect_mime_type, extract_text_from_file
from .rag import (
    cleanup_history,
    delete_document_from_index,
    index_document,
    rag_compare,
    rag_query,
    paper_context_chat,
    paper_compare_chat,
)
from .student_papers import (
    create_student_paper,
    load_student_paper_content,
    save_student_paper_content,
)
from .mentor_agent import mentor_chat
from .response_validator import validate_answer

app = FastAPI(title=settings.PROJECT_NAME)

research_agent = ResearchAgent()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        db = Session(bind=conn)
        # Create default admin if not exists
        admin = (
            db.query(models.User)
            .filter(models.User.username == settings.DEFAULT_ADMIN_USERNAME)
            .first()
        )
        if not admin:
            admin = models.User(
                username=settings.DEFAULT_ADMIN_USERNAME,
                hashed_password=auth.get_password_hash(
                    settings.DEFAULT_ADMIN_PASSWORD
                ),
                is_admin=True,
            )
            db.add(admin)
            db.commit()


@app.post(f"{settings.API_V1_PREFIX}/auth/token", response_model=schemas.Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    user = auth.authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = auth.create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get(f"{settings.API_V1_PREFIX}/auth/me", response_model=schemas.UserRead)
async def read_users_me(
    current_user: models.User = Depends(auth.get_current_active_user),
):
    return current_user


# -------------------- Conversations & Messages --------------------


@app.get(
    f"{settings.API_V1_PREFIX}/conversations",
    response_model=List[schemas.ConversationRead],
)
async def list_user_conversations(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """
    返回当前用户的对话列表。
    一个对话对应一个科研主题。
    """
    convos = list_conversations(db, current_user)
    return convos


@app.post(
    f"{settings.API_V1_PREFIX}/conversations",
    response_model=schemas.ConversationRead,
)
async def create_user_conversation(
    payload: schemas.ConversationCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    convo = create_conversation(db, current_user, payload)
    return convo


@app.get(
    f"{settings.API_V1_PREFIX}/conversations/{{conversation_id}}/messages",
    response_model=List[schemas.MessageRead],
)
async def list_conversation_messages(
    conversation_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    convo = get_conversation_or_404(db, current_user, conversation_id)
    msgs = list_messages(db, convo, limit=limit)
    return msgs


@app.post(
    f"{settings.API_V1_PREFIX}/conversations/{{conversation_id}}/messages",
    response_model=schemas.MessageRead,
)
async def add_conversation_message(
    conversation_id: int,
    payload: schemas.MessageCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """
    目前仅保存消息，后续会在这里接入 Research Agent 与流式回复。
    """
    convo = get_conversation_or_404(db, current_user, conversation_id)
    msg = add_message(db, convo, payload)
    return msg


# -------------------- Streaming Chat API --------------------


@app.post(f"{settings.API_V1_PREFIX}/chat/stream")
async def chat_stream(
    request: Request,
    conversation_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """
    SSE 风格的流式对话接口：
    - 前端传入 conversation_id 和最新 user 消息（应先通过 /conversations/{id}/messages 保存）
    - 后端根据该会话的全部消息调用 ResearchAgent，逐步返回内容
    """
    convo = get_conversation_or_404(db, current_user, conversation_id)
    history_messages = list_messages(db, convo, limit=200)

    async def event_generator():
        collected: list[str] = []
        async for chunk in research_agent.chat_stream(
            convo,
            history_messages,
            db=db,
            user=current_user,
        ):
            if await request.is_disconnected():
                break
            text = chunk.get("content", "")
            collected.append(text)
            yield f"data: {text}\n\n"

        full_answer = "".join(collected)
        is_valid, error = validate_answer(full_answer)
        if not is_valid:
            # 简单策略：追加一条说明，后续可改为重试 LLM
            warning = (
                "\n\n[系统校验] 检测到回答中包含科研性描述，但缺少合法引用标注 "
                "(paper_id:<number>)，请补充引用或在回答中说明："
                "\"insufficient evidence in literature database\"。"
            )
            full_answer_with_note = full_answer + warning
        else:
            full_answer_with_note = full_answer

        # 将最终回答保存为一条 assistant 消息
        add_message(
            db,
            convo,
            schemas.MessageCreate(
                role="assistant",
                content=full_answer_with_note,
                sources=None,
            ),
        )

        # 发送一个结束事件，方便前端关闭流
        yield "data: [END]\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
    )


# -------------------- Admin: Users & Groups --------------------


@app.get(
    f"{settings.API_V1_PREFIX}/admin/users",
    response_model=List[schemas.UserRead],
)
async def list_users(
    db: Session = Depends(get_db),
    _: models.User = Depends(auth.get_current_admin),
):
    return db.query(models.User).all()


@app.post(
    f"{settings.API_V1_PREFIX}/admin/users",
    response_model=schemas.UserRead,
)
async def create_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(auth.get_current_admin),
):
    existing = (
        db.query(models.User)
        .filter(models.User.username == user_in.username)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="用户名已存在")
    user = models.User(
        username=user_in.username,
        hashed_password=auth.get_password_hash(user_in.password),
        is_admin=user_in.is_admin,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@app.post(
    f"{settings.API_V1_PREFIX}/admin/users/{{user_id}}/reset_password",
    response_model=schemas.UserRead,
)
async def reset_user_password(
    user_id: int,
    new_password: str,
    db: Session = Depends(get_db),
    _: models.User = Depends(auth.get_current_admin),
):
    user = db.query(models.User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.hashed_password = auth.get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user


@app.get(
    f"{settings.API_V1_PREFIX}/admin/groups",
    response_model=List[schemas.GroupRead],
)
async def list_groups(
    db: Session = Depends(get_db),
    _: models.User = Depends(auth.get_current_active_user),
):
    return db.query(models.Group).all()


@app.post(
    f"{settings.API_V1_PREFIX}/admin/groups",
    response_model=schemas.GroupRead,
)
async def create_group(
    group_in: schemas.GroupCreate,
    db: Session = Depends(get_db),
    _: models.User = Depends(auth.get_current_admin),
):
    existing = (
        db.query(models.Group)
        .filter(models.Group.name == group_in.name)
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="群组名称已存在")
    group = models.Group(name=group_in.name, description=group_in.description)
    db.add(group)
    db.commit()
    db.refresh(group)
    return group


@app.post(
    f"{settings.API_V1_PREFIX}/admin/groups/{{group_id}}/add_user/{{user_id}}",
)
async def add_user_to_group(
    group_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    _: models.User = Depends(auth.get_current_admin),
):
    group = db.query(models.Group).get(group_id)
    user = db.query(models.User).get(user_id)
    if not group or not user:
        raise HTTPException(status_code=404, detail="用户或群组不存在")
    existing = (
        db.query(models.UserGroup)
        .filter(
            models.UserGroup.user_id == user_id,
            models.UserGroup.group_id == group_id,
        )
        .first()
    )
    if existing:
        return {"detail": "already in group"}
    ug = models.UserGroup(user_id=user_id, group_id=group_id)
    db.add(ug)
    db.commit()
    return {"detail": "ok"}


# -------------------- Documents --------------------

def _get_current_user_from_header_or_query(
    db: Session,
    authorization: Optional[str],
    access_token: Optional[str],
) -> models.User:
    """
    For file preview embedding (iframe/object) we allow passing token via query.
    Prefer Authorization header; fall back to access_token query param.
    """
    token: Optional[str] = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
    if not token and access_token:
        token = access_token
    if not token:
        raise HTTPException(status_code=401, detail="Missing token")
    return auth.get_user_from_token(db, token)


def _ensure_doc_visible(doc: models.Document, current_user: models.User) -> None:
    if current_user.is_admin:
        return
    if doc.uploader_id == current_user.id:
        return
    if not doc.is_private:
        return
    raise HTTPException(status_code=403, detail="无权访问该文献")


def _doc_to_paper(db: Session, doc: models.Document) -> Optional[models.Paper]:
    return db.query(models.Paper).filter(models.Paper.document_id == doc.id).first()



@app.get(
    f"{settings.API_V1_PREFIX}/documents",
    response_model=List[schemas.DocumentRead],
)
async def list_documents(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    q = db.query(models.Document)
    if not current_user.is_admin:
        # private docs of user OR shared docs
        q = q.filter(
            (models.Document.uploader_id == current_user.id)
            | (models.Document.is_private == False)  # noqa: E712
        )
    return q.order_by(models.Document.created_at.desc()).all()


@app.get(
    f"{settings.API_V1_PREFIX}/documents/{{doc_id}}",
    response_model=schemas.DocumentRead,
)
async def get_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    doc = db.query(models.Document).get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文献不存在")
    _ensure_doc_visible(doc, current_user)
    return doc


@app.get(f"{settings.API_V1_PREFIX}/documents/{{doc_id}}/file")
async def get_document_file(
    doc_id: int,
    access_token: Optional[str] = Query(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db),
):
    current_user = _get_current_user_from_header_or_query(db, authorization, access_token)
    doc = db.query(models.Document).get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文献不存在")
    _ensure_doc_visible(doc, current_user)
    path = Path(doc.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    media_type = doc.mime_type or detect_mime_type(path)
    # Important: do NOT force download. Use inline Content-Disposition for preview.
    # If `filename=` is passed to FileResponse, Starlette will set Content-Disposition to attachment.
    return FileResponse(
        path=str(path),
        media_type=media_type,
        headers={
            "Content-Disposition": f'inline; filename="{doc.original_name}"',
        },
    )


@app.get(f"{settings.API_V1_PREFIX}/documents/{{doc_id}}/text")
async def get_document_text(
    doc_id: int,
    limit_chars: int = 200000,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    doc = db.query(models.Document).get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文献不存在")
    _ensure_doc_visible(doc, current_user)
    path = Path(doc.path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="文件不存在")
    text = extract_text_from_file(path)
    if limit_chars and len(text) > limit_chars:
        text = text[:limit_chars]
    return {"document_id": doc.id, "text": text}


@app.get(
    f"{settings.API_V1_PREFIX}/documents/{{doc_id}}/chunks",
    response_model=schemas.DocumentChunksResponse,
)
async def get_document_chunks(
    doc_id: int,
    q: Optional[str] = None,
    limit: int = 500,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    doc = db.query(models.Document).get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文献不存在")
    _ensure_doc_visible(doc, current_user)

    paper = _doc_to_paper(db, doc)
    if not paper:
        return schemas.DocumentChunksResponse(document_id=doc.id, total=0, chunks=[])

    chunks_path = settings.PAPERS_DIR / str(paper.id) / "chunks.json"
    if not chunks_path.exists():
        return schemas.DocumentChunksResponse(document_id=doc.id, total=0, chunks=[])

    import json as _json

    try:
        payload = _json.loads(chunks_path.read_text(encoding="utf-8"))
        chunks = payload.get("chunks") or []
    except Exception:
        chunks = []

    items: List[schemas.DocumentChunk] = []
    needle = (q or "").strip().lower()
    for idx, text in enumerate(chunks):
        if needle and needle not in str(text).lower():
            continue
        items.append(schemas.DocumentChunk(chunk_index=idx, text=str(text)))
        if limit and len(items) >= limit:
            break

    return schemas.DocumentChunksResponse(document_id=doc.id, total=len(chunks), chunks=items)


@app.get(
    f"{settings.API_V1_PREFIX}/documents/{{doc_id}}/analysis",
    response_model=schemas.DocumentAnalysisResponse,
)
async def get_document_analysis(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    doc = db.query(models.Document).get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文献不存在")
    _ensure_doc_visible(doc, current_user)

    paper = _doc_to_paper(db, doc)
    if not paper:
        return schemas.DocumentAnalysisResponse(
            document_id=doc.id, status="pending", analysis=None, detail="paper not created yet"
        )

    profile_path = settings.PAPERS_DIR / str(paper.id) / "paper_profile.json"
    if not profile_path.exists():
        return schemas.DocumentAnalysisResponse(
            document_id=doc.id, status="pending", analysis=None, detail="profile not generated yet"
        )

    import json as _json

    try:
        raw = _json.loads(profile_path.read_text(encoding="utf-8"))
    except Exception as e:
        return schemas.DocumentAnalysisResponse(
            document_id=doc.id, status="error", analysis=None, detail=f"无法解析 profile: {e}"
        )

    bib = raw.get("bibliography") or {}
    metadata = schemas.PaperBibliography(
        authors=str(bib.get("authors") or ""),
        year=str(bib.get("year") or ""),
        title=str(bib.get("title") or ""),
        venue=str(bib.get("venue") or ""),
        volume=str(bib.get("volume") or ""),
        issue=str(bib.get("issue") or ""),
        pages=str(bib.get("pages") or ""),
        doi=str(bib.get("doi") or ""),
    )

    analysis = schemas.DocumentStructuredAnalysis(
        metadata=metadata,
        core_problem=str(raw.get("scientific_problem") or ""),
        core_hypothesis=str(raw.get("research_hypothesis") or ""),
        research_design=str(raw.get("research_design") or ""),
        data_source=str(raw.get("data_source") or ""),
        methods_and_tech=str(raw.get("methods") or ""),
        analysis_workflow=str(raw.get("analysis_workflow") or ""),
        data_analysis=str(raw.get("evaluation_methods") or ""),
        core_findings=str(raw.get("core_findings") or ""),
        experimental_results=str(raw.get("experimental_results") or ""),
        supporting_results=str(raw.get("supporting_results") or ""),
        final_conclusion=str(raw.get("authors_conclusion") or ""),
        field_contribution=str(raw.get("research_contribution") or ""),
        relevance_to_my_research=str(raw.get("review_relevance") or ""),
        highlights_analysis=str(raw.get("review_highlights") or ""),
        figures_tables_index=raw.get("figures_tables") or [],
        personal_evaluation=str(raw.get("critical_evaluation") or ""),
        questions_log=str(raw.get("open_questions") or ""),
        inspiration_thoughts=str(raw.get("research_inspiration") or ""),
        representative_references=raw.get("representative_references") or [],
    )
    return schemas.DocumentAnalysisResponse(document_id=doc.id, status="ready", analysis=analysis, detail=None)


@app.post(
    f"{settings.API_V1_PREFIX}/documents/upload",
    response_model=schemas.DocumentRead,
)
async def upload_document(
    file: UploadFile = File(...),
    is_private: bool = True,
    group_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    # 修复：从临时路径中提取真实文件名
    # Gradio 上传的文件是临时文件，file.filename 可能是完整路径
    original_filename = file.filename
    # 如果是临时文件路径，只取最后的文件名
    if '\\' in original_filename or '/' in original_filename:
        original_filename = os.path.basename(original_filename)
    
    print(f"原始文件名: {file.filename}")
    print(f"处理后的文件名: {original_filename}")
    
    suffix = Path(original_filename).suffix.lower()
    if suffix not in {".pdf", ".txt", ".docx", ".xlsx"}:
        raise HTTPException(
            status_code=400,
            detail="仅支持 PDF, TXT, DOCX, XLSX 格式",
        )

    # Check overwrite by original_name & uploader
    existing = (
        db.query(models.Document)
        .filter(
            models.Document.original_name == original_filename,
            models.Document.uploader_id == current_user.id,
        )
        .first()
    )

    # 确保上传目录存在
    upload_dir = settings.UPLOAD_DIR / str(current_user.id)
    print(f"上传目录: {upload_dir}")
    
    # 强制创建目录（包括父目录）
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # 验证目录是否真的创建成功
    if not upload_dir.exists():
        raise HTTPException(status_code=500, detail=f"无法创建上传目录: {upload_dir}")
    
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
    # 清理文件名中的特殊字符（可选）
    safe_filename = original_filename.replace(" ", "_").replace("(", "").replace(")", "")
    safe_name = f"{timestamp}_{safe_filename}"
    dest_path = upload_dir / safe_name
    print(f"目标路径: {dest_path}")

    # 读取文件内容
    content = await file.read()
    
    # 写入文件
    try:
        dest_path.write_bytes(content)
        print(f"文件写入成功: {dest_path}")
        print(f"文件大小: {len(content)} 字节")
    except Exception as e:
        print(f"文件写入失败: {e}")
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    mime_type = detect_mime_type(dest_path)

    if existing:
        # Overwrite: delete vector index and update
        delete_document_from_index(existing.id)
        existing.filename = safe_name
        existing.path = str(dest_path)
        existing.size_bytes = len(content)
        existing.group_id = group_id
        existing.is_private = is_private
        existing.mime_type = mime_type
        existing.created_at = datetime.utcnow()
        db.commit()
        db.refresh(existing)
        index_document(db, existing)
        return existing

    doc = models.Document(
        filename=safe_name,
        original_name=original_filename,  # 使用处理后的文件名
        size_bytes=len(content),
        uploader_id=current_user.id,
        group_id=group_id,
        is_private=is_private,
        mime_type=mime_type,
        path=str(dest_path),
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    index_document(db, doc)
    return doc


@app.post(
    f"{settings.API_V1_PREFIX}/documents/upload/batch",
    response_model=schemas.BatchUploadResponse,
)
async def upload_documents_batch(
    files: List[UploadFile] = File(...),
    is_private: bool = True,
    group_id: Optional[int] = None,
    rollback_on_error: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """
    Batch upload documents.
    Strategy: process sequentially to reduce memory/CPU pressure (indexing is heavy).
    If rollback_on_error is True, will delete all successfully uploaded docs when any failure happens.
    """
    uploaded_docs: List[models.Document] = []
    items: List[schemas.BatchUploadItem] = []

    # Ensure upload directory exists
    upload_dir = settings.UPLOAD_DIR / str(current_user.id)
    upload_dir.mkdir(parents=True, exist_ok=True)

    for f in files:
        original_filename = f.filename
        if "\\" in original_filename or "/" in original_filename:
            original_filename = os.path.basename(original_filename)
        try:
            suffix = Path(original_filename).suffix.lower()
            if suffix not in {".pdf", ".txt", ".docx", ".xlsx"}:
                raise HTTPException(status_code=400, detail="仅支持 PDF, TXT, DOCX, XLSX 格式")

            content = await f.read()
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")
            safe_filename = original_filename.replace(" ", "_").replace("(", "").replace(")", "")
            safe_name = f"{timestamp}_{safe_filename}"
            dest_path = upload_dir / safe_name
            dest_path.write_bytes(content)
            mime_type = detect_mime_type(dest_path)

            existing = (
                db.query(models.Document)
                .filter(
                    models.Document.original_name == original_filename,
                    models.Document.uploader_id == current_user.id,
                )
                .first()
            )

            if existing:
                delete_document_from_index(existing.id)
                existing.filename = safe_name
                existing.path = str(dest_path)
                existing.size_bytes = len(content)
                existing.group_id = group_id
                existing.is_private = is_private
                existing.mime_type = mime_type
                existing.created_at = datetime.utcnow()
                db.commit()
                db.refresh(existing)
                index_document(db, existing)
                uploaded_docs.append(existing)
                items.append(
                    schemas.BatchUploadItem(
                        filename=original_filename,
                        ok=True,
                        document=schemas.DocumentRead.model_validate(existing),
                        error=None,
                    )
                )
                continue

            doc = models.Document(
                filename=safe_name,
                original_name=original_filename,
                size_bytes=len(content),
                uploader_id=current_user.id,
                group_id=group_id,
                is_private=is_private,
                mime_type=mime_type,
                path=str(dest_path),
            )
            db.add(doc)
            db.commit()
            db.refresh(doc)

            index_document(db, doc)
            uploaded_docs.append(doc)
            items.append(
                schemas.BatchUploadItem(
                    filename=original_filename,
                    ok=True,
                    document=schemas.DocumentRead.model_validate(doc),
                    error=None,
                )
            )
        except Exception as e:
            err_msg = e.detail if isinstance(e, HTTPException) else str(e)
            items.append(
                schemas.BatchUploadItem(
                    filename=original_filename,
                    ok=False,
                    document=None,
                    error=err_msg,
                )
            )
            if rollback_on_error:
                # Rollback: delete already uploaded docs and their indexes
                for d in uploaded_docs:
                    try:
                        delete_document_from_index(d.id)
                    except Exception:
                        pass
                    try:
                        Path(d.path).unlink(missing_ok=True)
                    except Exception:
                        pass
                    try:
                        db.delete(d)
                        db.commit()
                    except Exception:
                        db.rollback()
                break

    success = sum(1 for it in items if it.ok)
    failed = sum(1 for it in items if not it.ok)
    return schemas.BatchUploadResponse(
        total=len(items),
        success=success,
        failed=failed,
        items=items,
    )


@app.delete(f"{settings.API_V1_PREFIX}/documents/{{doc_id}}")
async def delete_document(
    doc_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    doc = db.query(models.Document).get(doc_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文献不存在")
    if not current_user.is_admin and doc.uploader_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权删除该文献")

    delete_document_from_index(doc.id)

    try:
        Path(doc.path).unlink(missing_ok=True)
    except Exception:
        pass

    db.delete(doc)
    db.commit()
    return {"detail": "deleted"}


# -------------------- RAG --------------------


@app.post(
    f"{settings.API_V1_PREFIX}/rag/query",
    response_model=schemas.RAGQueryResponse,
)
async def rag_query_endpoint(
    payload: schemas.RAGQueryRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    result = rag_query(
        db,
        current_user,
        question=payload.question,
        scope=payload.scope,
        group_ids=payload.group_ids,
    )
    return schemas.RAGQueryResponse(**result)


@app.post(
    f"{settings.API_V1_PREFIX}/rag/compare",
    response_model=schemas.RAGQueryResponse,
)
async def rag_compare_endpoint(
    payload: schemas.RAGCompareRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    result = rag_compare(
        db,
        current_user,
        question=payload.question,
        document_ids=payload.document_ids,
    )
    return schemas.RAGQueryResponse(**result)


# -------------------- Paper Workspace --------------------


@app.get(
    f"{settings.API_V1_PREFIX}/papers",
    response_model=List[schemas.PaperRead],
)
async def list_papers(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    """返回当前用户可见的论文工作区列表（基于文献权限）"""
    q = db.query(models.Paper).join(models.Document, models.Paper.document_id == models.Document.id)
    if not current_user.is_admin:
        q = q.filter(
            (models.Document.uploader_id == current_user.id)
            | (models.Document.is_private == False)  # noqa: E712
        )
    return q.order_by(models.Paper.created_at.desc()).all()


@app.get(f"{settings.API_V1_PREFIX}/papers/{{paper_id}}/profile")
async def get_paper_profile(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    paper = db.query(models.Paper).get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    doc = db.query(models.Document).get(paper.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文献不存在")
    if (not current_user.is_admin) and (doc.uploader_id != current_user.id and doc.is_private):
        raise HTTPException(status_code=403, detail="无权访问该论文")
    if not paper.profile_path:
        return {}
    try:
        import json as _json

        with open(paper.profile_path, "r", encoding="utf-8") as f:
            return _json.load(f)
    except Exception:
        raise HTTPException(status_code=500, detail="无法读取论文 Profile")


@app.get(f"{settings.API_V1_PREFIX}/papers/{{paper_id}}/notes")
async def get_paper_notes(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    paper = db.query(models.Paper).get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    doc = db.query(models.Document).get(paper.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文献不存在")
    if (not current_user.is_admin) and (doc.uploader_id != current_user.id and doc.is_private):
        raise HTTPException(status_code=403, detail="无权访问该论文")

    from .config import settings as _settings
    from pathlib import Path

    notes_path = Path(_settings.PAPERS_DIR) / str(paper.id) / "paper_notes.md"
    if not notes_path.exists():
        return {"content": ""}
    return {"content": notes_path.read_text(encoding="utf-8")}


@app.post(f"{settings.API_V1_PREFIX}/papers/{{paper_id}}/notes")
async def update_paper_notes(
    paper_id: int,
    content: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    paper = db.query(models.Paper).get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")
    doc = db.query(models.Document).get(paper.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文献不存在")
    if (not current_user.is_admin) and (doc.uploader_id != current_user.id and doc.is_private):
        raise HTTPException(status_code=403, detail="无权编辑该论文笔记")

    from .config import settings as _settings
    from pathlib import Path

    paper_dir = Path(_settings.PAPERS_DIR) / str(paper.id)
    paper_dir.mkdir(parents=True, exist_ok=True)
    notes_path = paper_dir / "paper_notes.md"
    notes_path.write_text(content or "", encoding="utf-8")
    return {"detail": "ok"}


@app.post(
    f"{settings.API_V1_PREFIX}/papers/chat",
    response_model=schemas.RAGQueryResponse,
)
async def paper_chat_endpoint(
    payload: schemas.PaperChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    result = paper_context_chat(
        db,
        current_user,
        paper_id=payload.paper_id,
        question=payload.question,
    )
    return schemas.RAGQueryResponse(**result)


@app.post(
    f"{settings.API_V1_PREFIX}/papers/compare",
    response_model=schemas.RAGQueryResponse,
)
async def paper_compare_endpoint(
    payload: schemas.PaperCompareRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    result = paper_compare_chat(
        db,
        current_user,
        paper_ids=payload.paper_ids,
        question=payload.question,
    )
    return schemas.RAGQueryResponse(**result)


# -------------------- History --------------------


@app.get(
    f"{settings.API_V1_PREFIX}/history",
    response_model=List[schemas.ChatHistoryRead],
)
async def list_history(
    q: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    query = db.query(models.ChatHistory).filter(
        models.ChatHistory.user_id == current_user.id
    )
    if q:
        like = f"%{q}%"
        query = query.filter(
            models.ChatHistory.question.like(like)
            | models.ChatHistory.answer.like(like)
        )
    query = query.order_by(models.ChatHistory.created_at.desc())
    return query.all()


@app.post(f"{settings.API_V1_PREFIX}/admin/history/cleanup")
async def cleanup_history_endpoint(
    db: Session = Depends(get_db),
    _: models.User = Depends(auth.get_current_admin),
):
    deleted = cleanup_history(db)
    return {"deleted": deleted}


# -------------------- Student Writing Workspace --------------------


@app.get(
    f"{settings.API_V1_PREFIX}/student_papers",
    response_model=List[schemas.StudentPaperRead],
)
async def list_student_papers(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    q = db.query(models.StudentPaper)
    if not current_user.is_admin:
        q = q.filter(models.StudentPaper.user_id == current_user.id)
    return q.order_by(models.StudentPaper.created_at.desc()).all()


@app.post(
    f"{settings.API_V1_PREFIX}/student_papers/create",
    response_model=schemas.StudentPaperRead,
)
async def create_student_paper_endpoint(
    payload: schemas.StudentPaperCreateRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    paper = create_student_paper(db, current_user, title=payload.title)
    return paper


@app.get(
    f"{settings.API_V1_PREFIX}/student_papers/{{paper_id}}",
    response_model=schemas.StudentPaperDetail,
)
async def get_student_paper(
    paper_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    paper = db.query(models.StudentPaper).get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="学生论文不存在")
    if (not current_user.is_admin) and paper.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问该学生论文")
    content = load_student_paper_content(paper)
    return schemas.StudentPaperDetail(
        id=paper.id,
        user_id=paper.user_id,
        title=paper.title,
        created_at=paper.created_at,
        content=content,
    )


@app.post(
    f"{settings.API_V1_PREFIX}/student_papers/{{paper_id}}/save",
)
async def save_student_paper(
    paper_id: int,
    payload: schemas.StudentPaperSaveRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    paper = db.query(models.StudentPaper).get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="学生论文不存在")
    if (not current_user.is_admin) and paper.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权编辑该学生论文")
    save_student_paper_content(paper, payload.content)
    return {"detail": "ok"}


@app.post(
    f"{settings.API_V1_PREFIX}/student_papers/{{paper_id}}/mentor_chat",
    response_model=schemas.MentorChatResponse,
)
async def mentor_chat_endpoint(
    paper_id: int,
    payload: schemas.MentorChatRequest,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_active_user),
):
    result = mentor_chat(
        db,
        current_user,
        student_paper_id=paper_id,
        question=payload.question,
    )
    return schemas.MentorChatResponse(**result)


# -------------------- Dashboard --------------------


@app.get(
    f"{settings.API_V1_PREFIX}/admin/dashboard",
    response_model=schemas.DashboardStats,
)
async def dashboard_stats(
    db: Session = Depends(get_db),
    _: models.User = Depends(auth.get_current_admin),
):
    total_documents = db.query(func.count(models.Document.id)).scalar() or 0
    total_storage_bytes = (
        db.query(func.coalesce(func.sum(models.Document.size_bytes), 0)).scalar()
        or 0
    )
    total_users = db.query(func.count(models.User.id)).scalar() or 0
    total_groups = db.query(func.count(models.Group.id)).scalar() or 0
    cutoff = datetime.utcnow() - timedelta(days=settings.HISTORY_RETENTION_DAYS)
    recent_questions = (
        db.query(func.count(models.ChatHistory.id))
        .filter(models.ChatHistory.created_at >= cutoff)
        .scalar()
        or 0
    )

    recent_documents = (
        db.query(models.Document)
        .order_by(models.Document.created_at.desc())
        .limit(10)
        .all()
    )

    # We don't track total_indexed_chunks separately; approximate by document count * 1
    return schemas.DashboardStats(
        total_documents=total_documents,
        total_storage_bytes=total_storage_bytes,
        total_indexed_chunks=total_documents,
        total_users=total_users,
        total_groups=total_groups,
        recent_questions=recent_questions,
        recent_documents=recent_documents,
    )


@app.get("/")
async def root():
    return {
        "message": "Local Literature RAG Agent backend is running.",
        "api_prefix": settings.API_V1_PREFIX,
    }


# -------------------- 直接运行时的服务器启动 --------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=9000)