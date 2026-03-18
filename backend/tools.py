"""
Tool wrappers used by the ResearchAgent.

These wrap existing functionality (RAG, paper workspace, mentor agent, etc.)
into a uniform interface so the Agent can route calls based on high-level intents.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from . import mentor_agent, models, rag


def rag_search_tool(
    db: Session,
    user: models.User,
    query: str,
    scope: str = "all",
    group_ids: Optional[List[int]] = None,
    top_k: int = 15,
) -> Dict[str, Any]:
    """
    输入:
        query, scope, group_ids, top_k
    输出:
        {
          "chunks": [...],
          "paper_id": null,  # 暂不绑定具体 paper id
          "chunk_id": <chroma index or None>,
        }
    """
    result = rag.rag_query(
        db,
        user,
        question=query,
        scope=scope,
        group_ids=group_ids,
        top_k=top_k,
    )
    # 将现有 sources 直接暴露为 chunks 元数据
    return {
        "answer": result["answer"],
        "sources": result["sources"],
    }


def paper_compare_tool(
    db: Session,
    user: models.User,
    paper_ids: List[int],
    question: str,
) -> Dict[str, Any]:
    """
    输入:
        paper_ids, question
    输出:
        {
          "comparison_summary": str,
          "sources": [...]
        }
    """
    result = rag.paper_compare_chat(
        db,
        user,
        paper_ids=paper_ids,
        question=question,
    )
    return {
        "comparison_summary": result["answer"],
        "sources": result["sources"],
    }


def mentor_writing_tool(
    db: Session,
    user: models.User,
    student_paper_id: int,
    question: str,
) -> Dict[str, Any]:
    """
    复用目前的导师 Agent，作为 Writing / Experiment / Citation 综合工具。
    """
    result = mentor_agent.mentor_chat(
        db,
        user,
        student_paper_id=student_paper_id,
        question=question,
    )
    return result

