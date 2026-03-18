import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from .config import settings
import chromadb
from chromadb.config import Settings as ChromaSettings
from fastapi import HTTPException
from langchain.text_splitter import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session

from . import models
from .config import settings
from .document_processing import extract_text_from_file


class EmbeddingWrapper:
    def __init__(self, model_name: str):
        self.model = SentenceTransformer(model_name)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return self.model.encode(texts, show_progress_bar=False).tolist()

    def embed_query(self, text: str) -> List[float]:
        return self.model.encode([text], show_progress_bar=False)[0].tolist()


embedding_model = EmbeddingWrapper(settings.EMBEDDING_MODEL_NAME)

chroma_client = chromadb.PersistentClient(
    path=str(settings.CHROMA_DIR),
    settings=ChromaSettings(allow_reset=True),
)

collection = chroma_client.get_or_create_collection(
    name="literature_chunks",
    metadata={"hnsw:space": "cosine"},
)

text_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.CHUNK_SIZE,
    chunk_overlap=settings.CHUNK_OVERLAP,
)


def _build_metadata(
    doc: models.Document, chunk_index: int
) -> Dict[str, Any]:
    """构建 metadata，确保没有 None 值"""
    # 处理可能为 None 的字段
    group_id_val = doc.group_id if doc.group_id is not None else -1
    
    # 处理 created_at
    created_at_val = doc.created_at.isoformat() if doc.created_at else datetime.utcnow().isoformat()
    
    return {
        "document_id": doc.id,
        "original_name": doc.original_name or "",
        "uploader_id": doc.uploader_id,
        "group_id": group_id_val,  # 使用处理后的值，确保不是 None
        "is_private": doc.is_private,
        "chunk_index": chunk_index,
        "created_at": created_at_val,
    }


def index_document(db: Session, doc: models.Document) -> int:
    """Extract text, split into chunks, embed and store in Chroma. Returns number of chunks.

    同时生成论文知识层：
    - 调用 paper_analysis.analyze_paper 生成 paper_profile.json
    - 将分块结果保存为 chunks.json
    - 在 data/papers/{paper_id}/ 下建立工作区目录
    """
    from pathlib import Path

    from .config import settings  # 局部引入避免循环
    from .paper_analysis import analyze_paper

    path = Path(doc.path)
    text = extract_text_from_file(path)
    if not text.strip():
        raise HTTPException(status_code=400, detail="无法从文档中提取文本内容")

    # 文本分块与向量化（原有逻辑）
    chunks = text_splitter.split_text(text)
    if not chunks:
        raise HTTPException(status_code=400, detail="分块结果为空")

    embeddings = embedding_model.embed_documents(chunks)
    ids = [f"doc-{doc.id}-chunk-{i}" for i in range(len(chunks))]
    metadatas = [_build_metadata(doc, i) for i in range(len(chunks))]

    collection.add(
        ids=ids,
        documents=chunks,
        metadatas=metadatas,
        embeddings=embeddings,
    )

    # ---------- 论文知识层：Paper Profile & Chunks 存储 ----------
    # 1. 获取或创建 Paper 记录
    paper = (
        db.query(models.Paper)
        .filter(models.Paper.document_id == doc.id)
        .first()
    )
    if paper is None:
        paper = models.Paper(
            document_id=doc.id,
            title=doc.original_name,
            owner_id=doc.uploader_id,
            group_id=doc.group_id,
            file_path=str(path),
        )
        db.add(paper)
        db.commit()
        db.refresh(paper)

    # 2. 构建论文工作区目录
    papers_root = settings.PAPERS_DIR
    paper_dir = papers_root / str(paper.id)
    paper_dir.mkdir(parents=True, exist_ok=True)

    # 3. 保存原始文件副本
    try:
        suffix = path.suffix.lower() or ".pdf"
        original_target = paper_dir / f"original{suffix}"
        if not original_target.exists():
            original_target.write_bytes(path.read_bytes())
    except Exception:
        # 不影响主流程，忽略复制失败
        pass

    # 4. 调用 LLM 生成 paper_profile.json
    try:
        profile = analyze_paper(text)
    except Exception:
        profile = {}

    import json as _json

    profile_path = paper_dir / "paper_profile.json"
    profile_path.write_text(
        _json.dumps(profile, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 5. 保存 chunks.json（只保存纯文本，避免重复 embedding）
    chunks_path = paper_dir / "chunks.json"
    chunks_payload = {"chunks": chunks}
    chunks_path.write_text(
        _json.dumps(chunks_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    # 6. 初始化笔记文件 paper_notes.md（如不存在）
    notes_path = paper_dir / "paper_notes.md"
    if not notes_path.exists():
        notes_path.write_text(f"# 笔记：{doc.original_name}\n\n", encoding="utf-8")

    # 7. 回写 profile_path 等辅助信息
    paper.profile_path = str(profile_path)
    paper.file_path = str(path)
    db.commit()

    return len(chunks)


def delete_document_from_index(doc_id: int) -> None:
    prefix = f"doc-{doc_id}-chunk-"
    # Chroma doesn't support prefix delete directly; fetch ids first
    results = collection.get(
        where={"document_id": doc_id},
        include=["metadatas"],
    )
    if results and results.get("ids"):
        collection.delete(ids=results["ids"])


def build_permission_filter(
    user: models.User,
    scope: str,
    group_ids: Optional[List[int]] = None,
) -> Dict[str, Any]:
    if user.is_admin or scope == "all":
        # Admins can see all; for normal users "all" means all they have access to,
        # which is enforced at DB/document level, but in vector store we filter by user/group/private
        if user.is_admin:
            return {}
        # user: private or group docs they belong to
        return {
            "$or": [
                {"uploader_id": user.id},
                {"is_private": False},
            ]
        }

    if scope == "private":
        return {"uploader_id": user.id, "is_private": True}

    if scope == "groups":
        if not group_ids:
            raise HTTPException(status_code=400, detail="请选择至少一个群组")
        return {
            "$and": [
                {"group_id": {"$in": group_ids}},
                {"is_private": False},
            ]
        }

    raise HTTPException(status_code=400, detail="未知检索范围")


def expand_query(q: str) -> List[str]:
    q = (q or "").strip()
    if not q:
        return []
    return [
        q,
        f"{q} remote sensing",
        f"{q} deep learning",
        f"{q} survey",
    ]


def classify_query(q: str) -> str:
    q = (q or "").strip()
    if not q:
        return "qa"
    if "方向" in q or "综述" in q or "路线" in q or "总结" in q:
        return "research"
    if "可行吗" in q or "可行性" in q or "feasibility" in q.lower():
        return "feasibility"
    return "qa"

RESEARCH_PROMPT = """
你是遥感领域博士导师。

你的任务不是“总结文献”，而是：

👉 帮学生建立研究认知 + 提供可做的研究方向

----------------------------------

【回答结构】

# 📡 遥感超分研究方向分析

## 🧠 领域发展判断（必须有）
用1-2句话总结：

该领域当前的阶段，例如：
- 从“通用模型” → “遥感特化设计”
- 从“CNN” → “Transformer / Diffusion”

⚠️ 这一部分必须是“你的总结”，不是复述论文


---

## 🔬 重点研究方向（最重要部分）

必须给出 4-6 个方向，每个方向必须包含：

### 1. 方向名称（加粗）

**研究机会：**
一句话说明为什么值得做（gap）

**具体切入点：**
- 点1（必须具体）
- 点2（必须具体）

⚠️ 禁止写空话（如“可以进一步研究”）

---

## 💡 选题建议（必须有）

用表格：

| 方向 | 创新性 | 难度 | 数据需求 | 推荐人群 |

最后补一句：

👉 给出明确建议（比如“新手建议从xxx入手”）

---

【风格要求】

- 必须像导师讲解，不是论文摘要
- 多用 bullet points
- 关键概念加粗
- 不要大段文字

---

【禁止】

- 不要逐篇论文解释
- 不要只做分类
- 不要写泛泛建议

"""


FEASIBILITY_PROMPT = """
你是遥感领域科研导师。

请评估一个研究想法的可行性。

必须使用 Markdown 输出：

# 📊 可行性分析

## ✅ 可行性判断
（高 / 中 / 低）

## 📌 依据
- 列出已有相关方法

## ⚠️ 潜在问题
- 2-3点

## 💡 改进建议
- 可执行建议

----------------------------------

要求：

- 使用清晰结构
- 使用 bullet points
- 避免长段落
"""


DEFAULT_QA_PROMPT = """
你是一个遥感地理教授和博士导师，帮助博士学生理解文献。
请直接给出答案，不要输出思考过程。
请用正式的学术语言，简洁的语句进行回答。
如果无法从文献中获得答案，请如实说明：insufficient evidence in literature database
"""


def split_long_paragraphs(text: str) -> str:
    """
    简单防“文字墙”：对超长行做轻量断句。
    保守策略：仅在超长行中按中文逗号拆分，尽量不破坏 Markdown 表格。
    """
    lines = (text or "").split("\n")
    new_lines: List[str] = []
    for line in lines:
        if len(line) > 120 and "，" in line and ("|" not in line):
            parts = [p.strip() for p in line.split("，") if p.strip()]
            new_lines.extend(parts)
        else:
            new_lines.append(line)
    return "\n".join(new_lines)


def format_response(text: str) -> str:
    """
    简单增强输出格式（防止模型偶尔崩格式）：
    - 保证有一级标题
    - 断开超长段落
    """
    t = (text or "").strip()
    if not t.startswith("#"):
        t = "# 📡 研究分析结果\n\n" + t
    return split_long_paragraphs(t)


def _load_profile_for_document(db: Session, document_id: int) -> Optional[Dict[str, Any]]:
    paper = (
        db.query(models.Paper)
        .filter(models.Paper.document_id == document_id)
        .first()
    )
    if not paper or not paper.profile_path:
        return None
    try:
        with open(paper.profile_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _paper_summary_from_profile(profile: Dict[str, Any], fallback_title: str = "") -> str:
    bib = profile.get("bibliography", {}) or {}
    title = bib.get("title") or fallback_title or ""
    task_type = profile.get("task_type", "") or ""
    method_type = profile.get("method_type", "") or ""
    method_summary = profile.get("method_summary", "") or profile.get("methods", "") or ""
    innovation = profile.get("method_innovation", "") or ""
    results = profile.get("results_summary", "") or profile.get("core_findings", "") or ""

    return (
        f"论文: {title}\n"
        f"任务: {task_type}\n"
        f"方法: {method_type}\n"
        f"方法核心: {method_summary}\n"
        f"创新: {innovation}\n"
        f"结论: {results}\n"
    ).strip()


def _hybrid_retrieve(
    question: str,
    where_filter: Dict[str, Any],
    top_k: int,
) -> Tuple[List[str], List[Dict[str, Any]]]:
    """
    "Hybrid" retrieval (lightweight): multi-query rewrite + vector retrieval + merge/dedup.
    Returns (documents, metadatas) aligned by rank.
    """
    queries = expand_query(question)
    if not queries:
        return [], []

    merged: Dict[str, Tuple[str, Dict[str, Any], float]] = {}
    # Higher is better (we use negative distance as score).
    for q in queries:
        qe = embedding_model.embed_query(q)
        res = collection.query(
            query_embeddings=[qe],
            n_results=top_k,
            where=where_filter or None,
            include=["documents", "metadatas", "distances"],
        )
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        dists = res.get("distances", [[]])[0] if res.get("distances") else [None] * len(docs)

        for doc_text, meta, dist in zip(docs, metas, dists):
            doc_id = meta.get("document_id")
            chunk_idx = meta.get("chunk_index")
            key = f"{doc_id}:{chunk_idx}"
            score = -(float(dist) if dist is not None else 0.0)
            prev = merged.get(key)
            if prev is None or score > prev[2]:
                merged[key] = (doc_text, meta, score)

    ranked = sorted(merged.values(), key=lambda x: x[2], reverse=True)[:top_k]
    return [r[0] for r in ranked], [r[1] for r in ranked]


def rag_query(
    db: Session,
    user: models.User,
    question: str,
    scope: str,
    group_ids: Optional[List[int]] = None,
    top_k: int = 15,
) -> Dict[str, Any]:
    # 1) Task identify
    task_type = classify_query(question)

    # 2) Retrieval (rewrite + vector + dedup)
    where_filter = build_permission_filter(user, scope, group_ids)
    documents, metadatas = _hybrid_retrieve(question, where_filter, top_k=top_k)

    # 3) Chunk -> paper aggregation
    paper_map: Dict[int, List[str]] = {}
    sources: List[Dict[str, Any]] = []
    for doc, meta in zip(documents, metadatas):
        doc_id = meta.get("document_id")
        if doc_id is not None:
            paper_map.setdefault(int(doc_id), []).append(str(doc))
        sources.append(
            {
                "document_id": meta.get("document_id"),
                "original_name": meta.get("original_name"),
                "chunk_index": meta.get("chunk_index"),
            }
        )

    # 4) Paper profile injection
    context_parts: List[str] = []
    for doc_id, chunks in paper_map.items():
        profile = _load_profile_for_document(db, doc_id)
        if profile:
            # Prefer structured knowledge over noisy chunks
            doc_name = next((m.get("original_name") for m in metadatas if m.get("document_id") == doc_id), "") or ""
            context_parts.append(_paper_summary_from_profile(profile, fallback_title=doc_name))
        else:
            # Fallback: take top-3 chunks as a weak summary
            context_parts.append("\n".join(chunks[:3]))

    context_text = "\n\n---\n\n".join(context_parts) if context_parts else "（未检索到相关内容）"

    # 5) Task-aware prompt
    if task_type == "research":
        system_prompt = RESEARCH_PROMPT.strip()
        user_prompt = f"用户问题：{question}\n\n可用的论文结构化摘要/片段如下：\n{context_text}\n\n请按要求输出。"
    elif task_type == "feasibility":
        system_prompt = FEASIBILITY_PROMPT.strip()
        user_prompt = f"研究想法：{question}\n\n可用的论文结构化摘要/片段如下：\n{context_text}\n\n请按要求输出。"
    else:
        system_prompt = DEFAULT_QA_PROMPT.strip()
        user_prompt = (
            f"用户问题：{question}\n\n"
            f"可用的论文结构化摘要/片段如下：\n{context_text}\n\n"
            "请给出结构化、清晰的回答。"
        )

    answer = call_llm(system_prompt, user_prompt)
    answer = format_response(answer)
    answer = format_response(answer)

    # Save history
    history = models.ChatHistory(
        user_id=user.id,
        question=question,
        answer=answer,
        sources=json.dumps(sources, ensure_ascii=False),
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    return {"answer": answer, "sources": sources}


def rag_compare(
    db: Session,
    user: models.User,
    question: str,
    document_ids: List[int],
    top_k: int = 15,
) -> Dict[str, Any]:
    if not document_ids:
        raise HTTPException(status_code=400, detail="请至少选择一篇文献")

    # Verify user permission at DB level
    docs = (
        db.query(models.Document)
        .filter(models.Document.id.in_(document_ids))
        .all()
    )
    allowed_ids: List[int] = []
    for d in docs:
        if user.is_admin:
            allowed_ids.append(d.id)
        elif d.uploader_id == user.id:
            allowed_ids.append(d.id)
        elif not d.is_private:
            allowed_ids.append(d.id)
    if not allowed_ids:
        raise HTTPException(status_code=403, detail="没有权限访问所选文献")

    # Task identify (compare is usually research-like)
    task_type = classify_query(question)

    where_filter = {"document_id": {"$in": allowed_ids}}
    documents, metadatas = _hybrid_retrieve(question, where_filter, top_k=top_k)

    # Aggregate by paper
    paper_map: Dict[int, List[str]] = {}
    for doc_text, meta in zip(documents, metadatas):
        doc_id = meta.get("document_id")
        if doc_id is not None:
            paper_map.setdefault(int(doc_id), []).append(str(doc_text))

    compare_context_parts: List[str] = []
    for doc_id in allowed_ids:
        doc = next((d for d in docs if d.id == doc_id), None)
        if not doc:
            continue
        profile = _load_profile_for_document(db, doc_id)
        if profile:
            compare_context_parts.append(_paper_summary_from_profile(profile, fallback_title=doc.original_name))
        else:
            compare_context_parts.append("\n".join(paper_map.get(doc_id, [])[:3]) or "（未检索到该文献的相关内容）")

    context_text = "\n\n---\n\n".join(compare_context_parts) if compare_context_parts else "（未检索到相关内容）"

    if task_type == "feasibility":
        system_prompt = FEASIBILITY_PROMPT.strip()
        user_prompt = f"研究想法：{question}\n\n可用的论文结构化摘要/片段如下：\n{context_text}\n\n请按要求输出。"
    else:
        system_prompt = RESEARCH_PROMPT.strip()
        user_prompt = f"用户问题：{question}\n\n可用的论文结构化摘要/片段如下：\n{context_text}\n\n请按要求输出。"

    answer = call_llm(system_prompt, user_prompt)
    answer = format_response(answer)
    answer = format_response(answer)

    sources = [
        {
            "document_id": meta.get("document_id"),
            "original_name": meta.get("original_name"),
            "chunk_index": meta.get("chunk_index"),
        }
        for meta in metadatas
    ]

    history = models.ChatHistory(
        user_id=user.id,
        question=f"[对比问答]{question}",
        answer=answer,
        sources=json.dumps(sources, ensure_ascii=False),
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    return {"answer": answer, "sources": sources}


def cleanup_history(db: Session) -> int:
    """Delete history older than retention days. Returns number of deleted records."""
    cutoff = datetime.utcnow() - timedelta(days=settings.HISTORY_RETENTION_DAYS)
    q = db.query(models.ChatHistory).filter(models.ChatHistory.created_at < cutoff)
    count = q.count()
    q.delete(synchronize_session=False)
    db.commit()
    return count


def paper_context_chat(
    db: Session,
    user: models.User,
    paper_id: int,
    question: str,
    top_k: int = settings.TOP_K,
) -> Dict[str, Any]:
    """单篇论文工作区对话：Profile + Chroma 检索上下文"""
    paper = db.query(models.Paper).get(paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    # 权限校验：基于对应 Document
    doc = db.query(models.Document).get(paper.document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="文献不存在")
    if (not user.is_admin) and (doc.uploader_id != user.id and doc.is_private):
        raise HTTPException(status_code=403, detail="无权访问该论文")

    # 读取 profile.json（结构化摘要）
    profile_summary = ""
    if paper.profile_path:
        try:
            with open(paper.profile_path, "r", encoding="utf-8") as f:
                profile = json.load(f)
            bib = profile.get("bibliography", {}) or {}
            title = bib.get("title") or paper.title or ""
            authors = bib.get("authors") or ""
            year = bib.get("year") or ""
            core = profile.get("core_findings", "") or ""
            methods = profile.get("methods", "") or ""
            scientific_problem = profile.get("scientific_problem", "") or ""
            profile_summary = "\n".join(
                [
                    f"标题: {title}" if title else "",
                    f"作者: {authors}" if authors else "",
                    f"年份: {year}" if year else "",
                    f"科学问题: {scientific_problem}" if scientific_problem else "",
                    f"方法: {methods}" if methods else "",
                    f"核心发现: {core}" if core else "",
                ]
            ).strip()
        except Exception:
            profile_summary = ""

    # Chroma 中仅检索该文献的相关 chunk
    query_embedding = embedding_model.embed_query(question)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"document_id": paper.document_id},
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    context_parts: List[str] = []
    sources: List[Dict[str, Any]] = []
    for doc_text, meta in zip(documents, metadatas):
        context_parts.append(
            f"[{meta.get('original_name')} - 块 {meta.get('chunk_index')}] {doc_text}"
        )
        sources.append(
            {
                "document_id": meta.get("document_id"),
                "original_name": meta.get("original_name"),
                "chunk_index": meta.get("chunk_index"),
            }
        )
    context_text = "\n\n".join(context_parts) if context_parts else "（未检索到相关内容）"

    system_prompt = (
        "你是一个科研论文阅读助手。\n"
        "优先利用给定的论文结构化摘要（Profile）和原文片段回答问题，"
        "回答要简洁、分点、用中文，不要凭空臆测。\n"
    )

    user_prompt = (
        f"论文结构化摘要：\n{profile_summary or '（无摘要）'}\n\n"
        f"与问题相关的原文片段：\n{context_text}\n\n"
        f"用户问题：{question}\n\n"
        "请结合摘要和原文片段进行回答，如无法从中得到答案请直说。"
    )

    answer = call_llm(system_prompt, user_prompt)

    history = models.ChatHistory(
        user_id=user.id,
        question=f"[论文工作区]{question}",
        answer=answer,
        sources=json.dumps(sources, ensure_ascii=False),
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    return {"answer": answer, "sources": sources}


def paper_compare_chat(
    db: Session,
    user: models.User,
    paper_ids: List[int],
    question: str,
    top_k: int = settings.TOP_K,
) -> Dict[str, Any]:
    """多论文对比：Profile + 分论文的 Chroma 检索"""
    if not paper_ids:
        raise HTTPException(status_code=400, detail="请至少选择一篇论文")

    papers = db.query(models.Paper).filter(models.Paper.id.in_(paper_ids)).all()
    if not papers:
        raise HTTPException(status_code=404, detail="未找到论文")

    # 映射 paper -> document 并做权限校验
    paper_docs: Dict[int, models.Document] = {}
    allowed_paper_ids: List[int] = []
    for p in papers:
        doc = db.query(models.Document).get(p.document_id)
        if not doc:
            continue
        if user.is_admin or (doc.uploader_id == user.id) or (not doc.is_private):
            paper_docs[p.id] = doc
            allowed_paper_ids.append(p.id)
    if not allowed_paper_ids:
        raise HTTPException(status_code=403, detail="没有权限访问所选论文")

    # 读取 Profile 摘要
    profile_summaries: Dict[int, str] = {}
    for p in papers:
        if p.id not in allowed_paper_ids or not p.profile_path:
            continue
        try:
            with open(p.profile_path, "r", encoding="utf-8") as f:
                profile = json.load(f)
            bib = profile.get("bibliography", {}) or {}
            title = bib.get("title") or p.title or ""
            authors = bib.get("authors") or ""
            year = bib.get("year") or ""
            methods = profile.get("methods", "") or ""
            core = profile.get("core_findings", "") or ""
            scientific_problem = profile.get("scientific_problem", "") or ""
            summary = "\n".join(
                [
                    f"标题: {title}" if title else "",
                    f"作者: {authors}" if authors else "",
                    f"年份: {year}" if year else "",
                    f"科学问题: {scientific_problem}" if scientific_problem else "",
                    f"方法: {methods}" if methods else "",
                    f"核心发现: {core}" if core else "",
                ]
            ).strip()
            profile_summaries[p.id] = summary
        except Exception:
            profile_summaries[p.id] = ""

    # 在向量库中按 document_id 范围检索
    query_embedding = embedding_model.embed_query(question)
    doc_ids = [paper_docs[pid].id for pid in allowed_paper_ids]
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where={"document_id": {"$in": doc_ids}},
    )

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    grouped_chunks: Dict[int, List[str]] = {}
    for doc_text, meta in zip(documents, metadatas):
        doc_id = meta.get("document_id")
        if doc_id is None:
            continue
        # 反查 paper_id
        pid = next(
            (p_id for p_id, d in paper_docs.items() if d.id == doc_id),
            None,
        )
        if pid is None:
            continue
        label = f"[{meta.get('original_name')} - 块 {meta.get('chunk_index')}] {doc_text}"
        grouped_chunks.setdefault(pid, []).append(label)

    # 构造多论文对比上下文
    compare_parts: List[str] = []
    for pid in allowed_paper_ids:
        doc = paper_docs[pid]
        profile_text = profile_summaries.get(pid, "") or "（无结构化摘要）"
        chunks_text = (
            "\n".join(grouped_chunks.get(pid, []))
            if grouped_chunks.get(pid)
            else "（未检索到该论文的相关内容）"
        )
        compare_parts.append(
            f"论文ID {pid} - 《{doc.original_name}》\n"
            f"[结构化摘要]\n{profile_text}\n\n[相关原文片段]\n{chunks_text}\n"
        )

    context_text = "\n\n".join(compare_parts)

    system_prompt = (
        "你是一个科研综述与对比分析助手。\n"
        "请基于多篇论文的结构化摘要与原文片段，回答用户的问题，"
        "清晰指出各论文在方法、数据、结果上的相同点和差异点，并给出原因分析。\n"
    )

    user_prompt = (
        f"用户问题：{question}\n\n"
        f"以下是多篇论文的摘要和相关片段：\n{context_text}\n\n"
        "请分条说明：1) 主要共同点；2) 关键差异；3) 可能的原因或启发。"
    )

    answer = call_llm(system_prompt, user_prompt)

    sources = [
        {
            "document_id": meta.get("document_id"),
            "original_name": meta.get("original_name"),
            "chunk_index": meta.get("chunk_index"),
        }
        for meta in metadatas
    ]

    history = models.ChatHistory(
        user_id=user.id,
        question=f"[论文对比]{question}",
        answer=answer,
        sources=json.dumps(sources, ensure_ascii=False),
    )
    db.add(history)
    db.commit()
    db.refresh(history)

    return {"answer": answer, "sources": sources}


# def call_llm(system_prompt: str, user_prompt: str) -> str:
#     """Call vLLM OpenAI-compatible DeepSeek-R1 service."""
#     import openai

#     openai_client = openai.OpenAI(
#         base_url=settings.VLLM_API_BASE,
#         api_key=settings.VLLM_API_KEY,
#     )

#     # 使用 vLLM 实际返回的模型路径
#     model_name = "/mnt/d/agent_litkb/15b_model"
    
#     resp = openai_client.chat.completions.create(
#         model=model_name,
#         messages=[
#             {"role": "system", "content": system_prompt},
#             {"role": "user", "content": user_prompt},
#         ],
#         temperature=0.2,
#     )
#     return resp.choices[0].message.content.strip()
def call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call vLLM OpenAI-compatible DeepSeek-R1 service."""
    import openai

    openai_client = openai.OpenAI(
        base_url=settings.VLLM_API_BASE,
        api_key=settings.VLLM_API_KEY,
    )

    # 使用配置中的模型路径
    model_name = settings.LLM_MODEL_NAME
    
    try:
        resp = openai_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
            max_tokens=1024,
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"vLLM 调用失败: {e}")
        return f"生成回答时出错: {str(e)}"

# 注释掉 Transformers 版本
# def call_llm(system_prompt: str, user_prompt: str) -> str:
#     """直接使用 Transformers 加载本地 DeepSeek 模型"""
#     ... (原有代码)