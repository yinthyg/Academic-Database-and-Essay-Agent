from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlalchemy.orm import Session

from . import models
from .config import settings


def _paper_dir(paper_id: int) -> Path:
    return settings.STUDENT_PAPERS_DIR / str(paper_id)


def create_student_paper(
    db: Session,
    user: models.User,
    title: str,
) -> models.StudentPaper:
    """创建学生论文记录与对应的工作区目录与初始 paper.md。"""
    paper = models.StudentPaper(
        user_id=user.id,
        title=title.strip() or "Untitled",
        content_path="",  # 稍后填充
    )
    db.add(paper)
    db.commit()
    db.refresh(paper)

    # 文件系统结构
    paper_dir = _paper_dir(paper.id)
    paper_dir.mkdir(parents=True, exist_ok=True)
    content_path = paper_dir / "paper.md"

    # 写入初始内容
    header = f"# {paper.title}\n\n" f"创建时间：{datetime.utcnow().isoformat()}Z\n\n"
    content_path.write_text(header, encoding="utf-8")

    paper.content_path = str(content_path)
    db.commit()
    db.refresh(paper)

    return paper


def load_student_paper_content(paper: models.StudentPaper) -> str:
    path = Path(paper.content_path)
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def save_student_paper_content(paper: models.StudentPaper, content: str) -> None:
    path = Path(paper.content_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content or "", encoding="utf-8")

