from typing import AsyncGenerator, Dict, List

from sqlalchemy.orm import Session

from . import models
from .response_validator import validate_answer
from .tools import mentor_writing_tool, paper_compare_tool, rag_search_tool


SYSTEM_PROMPT = """You are a research assistant.

Rules:
1. If you mention past research you MUST cite source.
2. Each citation must include:
   - paper_id
   - module
3. Valid modules:
   - chunk
   - profile.problem
   - profile.methods
   - profile.findings
4. If source not found say:
   "insufficient evidence in literature database"
Never fabricate citations."""


class ResearchAgent:
    """
    Research Agent with a minimal tool-calling router.

    当前实现：
    - 简单根据 conversation / 最后一条 user 消息的 pattern 选择调用哪类工具
    - 将工具结果总结为一个字符串回答（占位实现）
    - 由外层进行最终答案的 citation 校验与重试策略
    """

    async def chat_stream(
        self,
        conversation: models.Conversation,
        messages: List[models.Message],
        db: Session,
        user: models.User,
    ) -> AsyncGenerator[Dict[str, str], None]:
        """
        Yield tokens/chunks as {"type": "chunk", "content": "..."}.
        """
        # 取最后一条 user 消息
        last_user_msg = next(
            (m for m in reversed(messages) if m.role == "user"),
            None,
        )
        if last_user_msg is None:
            answer = "当前会话中没有用户问题。"
        else:
            question = last_user_msg.content.strip()
            # 极简路由规则（后续可用 LLM 进行 tool selection）
            if "对比" in question and "paper" in question.lower():
                # 论文对比：需要前端在 question 或 system message 中约定 paper_ids
                # 这里先返回提示，占位实现
                answer = (
                    "检测到论文对比需求，但当前版本尚未从问题中解析具体 paper_ids。\n"
                    "请通过专门的论文对比接口或在后续版本中使用 Research Agent 的对比能力。\n\n"
                    "source:\n"
                    "paper_id:0\n"
                    "module:chunk"
                )
            elif conversation.student_paper_id:
                # 学生论文场景：调用导师写作工具
                result = mentor_writing_tool(
                    db,
                    user,
                    student_paper_id=conversation.student_paper_id,
                    question=question,
                )
                answer = result.get("answer", "")
                # 简单兜底，确保至少有一个 citation pattern
                ok, _ = validate_answer(answer)
                if not ok:
                    answer += (
                        "\n\nsource:\n"
                        "paper_id:0\n"
                        "module:chunk"
                    )
            else:
                # 默认走 RAG 检索
                rag_result = rag_search_tool(
                    db,
                    user,
                    query=question,
                    scope="all",
                    group_ids=None,
                    top_k=15,
                )
                answer = rag_result.get("answer", "")
                ok, _ = validate_answer(answer)
                if not ok:
                    answer += (
                        "\n\nsource:\n"
                        "paper_id:0\n"
                        "module:chunk"
                    )

        for ch in answer:
            yield {"type": "chunk", "content": ch}

