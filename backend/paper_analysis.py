import json
from typing import Any, Dict

from .config import settings
from .rag import call_llm


PAPER_PROFILE_TEMPLATE: Dict[str, Any] = {
    "bibliography": {},

    "task_type": "",
    "method_type": "",
    "application_domain": "",

    "scientific_problem": "",
    "research_goal": "",

    "method_summary": "",
    "method_components": [],
    "method_innovation": "",

    "datasets": [],
    "evaluation_metrics": [],

    "results_summary": "",
    "quantitative_results": [],

    "baselines": [],

    "strengths": "",
    "limitations": "",
    "open_questions": "",

    "research_lineage": "",
    "related_directions": [],

    "research_inspiration": "",
}


def _build_system_prompt() -> str:
    return (
        "你是遥感领域论文分析助手。\n"
        "你的任务不是摘抄，而是构建科研知识结构。\n\n"
        "必须做到：\n"
        "1. 判断任务类型（超分/分割/检测/变化检测）\n"
        "2. 判断方法类别（CNN/Transformer/Diffusion/Hybrid）\n"
        "3. 提炼方法核心结构\n"
        "4. 总结创新点\n\n"
        "输出必须是JSON，不允许解释。"
    )


def _build_user_prompt(text: str) -> str:
    # 为控制上下文长度，仅使用前若干字符
    max_chars = int(getattr(settings, "PAPER_ANALYSIS_MAX_CHARS", 8000))
    snippet = text[:max_chars]
    return (
        "下面是论文正文或主要内容的片段，请基于这些内容进行结构化分析并输出 JSON：\n\n"
        f"{snippet}\n\n"
        "请严格只输出一个 JSON 对象，键必须为：\n"
        "{"
        "\"bibliography\": {\"authors\":\"\",\"year\":\"\",\"title\":\"\",\"venue\":\"\",\"volume\":\"\",\"issue\":\"\",\"pages\":\"\",\"doi\":\"\"},"
        "\"task_type\":\"\","
        "\"method_type\":\"\","
        "\"application_domain\":\"\","
        "\"scientific_problem\":\"\","
        "\"research_goal\":\"\","
        "\"method_summary\":\"\","
        "\"method_components\":[],"
        "\"method_innovation\":\"\","
        "\"datasets\":[],"
        "\"evaluation_metrics\":[],"
        "\"results_summary\":\"\","
        "\"quantitative_results\":[],"
        "\"baselines\":[],"
        "\"strengths\":\"\","
        "\"limitations\":\"\","
        "\"open_questions\":\"\","
        "\"research_lineage\":\"\","
        "\"related_directions\":[],"
        "\"research_inspiration\":\"\""
        "}\n"
        "不要添加任何 JSON 之外的解释性文字。"
    )


def normalize_profile(profile: Dict[str, Any]) -> Dict[str, Any]:
    def _safe_lower(x: Any) -> str:
        return str(x or "").strip().lower()

    def norm_task(t: str) -> str:
        t = _safe_lower(t)
        if "super" in t or "超分" in t or "sr" == t:
            return "super_resolution"
        if "segment" in t or "分割" in t:
            return "segmentation"
        if "detect" in t or "检测" in t:
            return "detection"
        if "change" in t or "变化" in t:
            return "change_detection"
        return t

    def norm_method(m: str) -> str:
        m = _safe_lower(m)
        if "transformer" in m or "vit" in m:
            return "transformer"
        if "cnn" in m or "conv" in m:
            return "cnn"
        if "diffusion" in m:
            return "diffusion"
        if "hybrid" in m or ("cnn" in m and "transformer" in m):
            return "hybrid"
        return "other"

    profile["task_type"] = norm_task(profile.get("task_type", ""))
    profile["method_type"] = norm_method(profile.get("method_type", ""))

    # Backward-compatible fields for existing UI/endpoints (best-effort).
    profile.setdefault("methods", profile.get("method_summary", ""))
    profile.setdefault("core_findings", profile.get("results_summary", ""))
    profile.setdefault("evaluation_methods", ", ".join(profile.get("evaluation_metrics", []) or []))

    return profile


def analyze_paper(text: str) -> Dict[str, Any]:
    """
    调用本地 LLM 对论文文本进行结构化分析，返回 paper_profile JSON。
    """
    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(text)

    raw = call_llm(system_prompt, user_prompt)

    profile: Dict[str, Any] = {}
    try:
        # 尝试定位首尾大括号，避免模型输出多余前后缀
        start = raw.find("{")
        end = raw.rfind("}")
        if start != -1 and end != -1 and end > start:
            raw_json = raw[start : end + 1]
        else:
            raw_json = raw
        profile = json.loads(raw_json)
    except Exception:
        # 回退到空模板，至少保证结构存在
        profile = {}

    merged: Dict[str, Any] = {}
    for k, v in PAPER_PROFILE_TEMPLATE.items():
        if k in profile:
            merged[k] = profile[k]
        else:
            merged[k] = v

    # bibliography 子结构兜底
    if not isinstance(merged.get("bibliography"), dict):
        merged["bibliography"] = {}

    merged = normalize_profile(merged)
    return merged

