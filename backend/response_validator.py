import re
from typing import Tuple


_CITATION_PATTERN = re.compile(r"paper_id:\d+", re.IGNORECASE)


def contains_research_claim(answer: str) -> bool:
    """
    Very lightweight heuristic:
    - if text mentions '研究', 'experiment', '实验', 'result', '结果', 'paper'
      we treat it as containing research claims.
    This can be refined later.
    """
    keywords = ["研究", "实验", "结果", "paper", "study", "experiment", "finding"]
    lower = answer.lower()
    if any(k in answer for k in keywords) or any(k in lower for k in keywords):
        return True
    return False


def has_valid_citation(answer: str) -> bool:
    """
    Check if answer contains at least one `paper_id:\\d+` pattern.
    """
    return _CITATION_PATTERN.search(answer) is not None


def validate_answer(answer: str) -> Tuple[bool, str]:
    """
    Return (is_valid, error_message).

    Logic:
    - If answer has no research claims -> always pass.
    - If answer has research claims but no citation -> fail.
    """
    if not contains_research_claim(answer):
        return True, ""
    if has_valid_citation(answer):
        return True, ""
    return False, "Missing required citation pattern 'paper_id:<'number'>'"

