import json
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session

from . import models
from .config import settings
from .rag import (
    build_permission_filter,
    collection,
    embedding_model,
    call_llm,
)
from .student_papers import load_student_paper_content


def _collect_rag_context(
    db: Session,
    user: models.User,
    combined_query: str,
    top_k: int = 8,
) -> Tuple[str, List[Dict[str, Any]]]:
    """基于学生论文+问题组合，做一次 RAG 检索，返回文本上下文和源信息。"""
    # 使用用户“全部可见文献”的权限范围
    where_filter = build_permission_filter(user, scope="all", group_ids=None)

    query_embedding = embedding_model.embed_query(combined_query)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter or None,
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    parts: List[str] = []
    sources: List[Dict[str, Any]] = []
    for doc_text, meta in zip(documents, metadatas):
        label = f"[{meta.get('original_name')} - 块 {meta.get('chunk_index')}] {doc_text}"
        parts.append(label)
        sources.append(
            {
                "document_id": meta.get("document_id"),
                "original_name": meta.get("original_name"),
                "chunk_index": meta.get("chunk_index"),
            }
        )

    ctx = "\n\n".join(parts) if parts else "（未检索到相关文献片段）"
    return ctx, sources


def _collect_paper_profiles(db: Session, user: models.User, limit: int = 5) -> str:
    """选取当前用户可访问的若干篇论文 profile，作为结构化文献背景。"""
    # 先选出可访问的 Document id
    docs = (
        db.query(models.Document)
        .order_by(models.Document.created_at.desc())
        .limit(50)
        .all()
    )
    allowed_doc_ids: List[int] = []
    for d in docs:
        if user.is_admin or d.uploader_id == user.id or (not d.is_private):
            allowed_doc_ids.append(d.id)
    if not allowed_doc_ids:
        return ""

    papers = (
        db.query(models.Paper)
        .filter(models.Paper.document_id.in_(allowed_doc_ids))
        .order_by(models.Paper.created_at.desc())
        .limit(limit)
        .all()
    )

    profiles_snippets: List[str] = []
    for p in papers:
        if not p.profile_path:
            continue
        try:
            with open(p.profile_path, "r", encoding="utf-8") as f:
                profile = json.load(f)
            bib = profile.get("bibliography", {}) or {}
            title = bib.get("title") or p.title or ""
            methods = profile.get("methods", "") or ""
            sci_problem = profile.get("scientific_problem", "") or ""
            core = profile.get("core_findings", "") or ""
            snippet = (
                f"Title: {title}\n"
                f"Scientific problem: {sci_problem}\n"
                f"Methods: {methods}\n"
                f"Core findings: {core}\n"
            )
            profiles_snippets.append(snippet.strip())
        except Exception:
            continue

    return "\n\n---\n\n".join(profiles_snippets[:limit])


def mentor_chat(
    db: Session,
    user: models.User,
    student_paper_id: int,
    question: str,
) -> Dict[str, Any]:
    """导师 Agent：综合学生论文 + RAG 文献 + 论文 profiles 给出写作建议与引用推荐。"""
    sp = db.query(models.StudentPaper).get(student_paper_id)
    if not sp:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="学生论文不存在")
    if (not user.is_admin) and sp.user_id != user.id:
        from fastapi import HTTPException

        raise HTTPException(status_code=403, detail="无权访问该学生论文")

    paper_content = load_student_paper_content(sp)
    combined_query = (paper_content[:2000] + "\n\n" + question) if paper_content else question

    rag_ctx, sources = _collect_rag_context(db, user, combined_query, top_k=settings.TOP_K)
    profiles_text = _collect_paper_profiles(db, user, limit=5)

    system_prompt = (
        "You are an academic research advisor.\n"
        "A student is writing a research paper. "
        "You should: (1) evaluate the research idea, (2) find similar research papers, "
        "(3) suggest citations, (4) suggest improvements, (5) suggest methods or experiments.\n"
        "Please answer in Chinese, structured with numbered bullet points."
    )

    user_prompt = (
        "Student paper (Markdown):\n"
        "------------------------\n"
        f"{paper_content[:4000] if paper_content else '(empty)'}\n\n"
        "Student question:\n"
        "-----------------\n"
        f"{question}\n\n"
        "Relevant literature chunks (RAG):\n"
        "---------------------------------\n"
        f"{rag_ctx}\n\n"
        "Structured literature profiles:\n"
        "------------------------------\n"
        f"{profiles_text or '(no structured profiles)'}\n\n"
        "Output in the following sections:\n"
        "1. Research evaluation\n"
        "2. Related work suggestions\n"
        "3. Citation suggestions (list concrete paper-style references)\n"
        "4. Improvement suggestions\n"
        "5. Method / experiment suggestions\n"
    )

    answer = call_llm(system_prompt, user_prompt)

    # 简单从回答中提取 "Citation suggestions" 段落中的项目行（启发式）
    citations: List[str] = []
    lower = answer.lower()
    marker = "citation suggestions"
    idx = lower.find(marker)
    if idx != -1:
        block = answer[idx:].split("\n", maxsplit=20)
        for line in block[1:]:
            stripped = line.strip(" -*•\t")
            if not stripped:
                continue
            # 遇到下一节标题时停止
            if stripped[:2].isdigit() or stripped.lower().startswith("research evaluation"):
                break
            citations.append(stripped)

    return {"answer": answer, "sources": sources, "citations": citations}

