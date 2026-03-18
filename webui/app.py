from __future__ import annotations

import json
import os
from typing import Dict, List, Optional, Tuple

import gradio as gr
import requests
import os

API_BASE = "http://127.0.0.1:9000/api"


# 避免某些 Windows/代理环境下 Gradio 自检 localhost 失败而强制要求 share=True
os.environ.setdefault("NO_PROXY", "127.0.0.1,localhost")
os.environ.setdefault("no_proxy", "127.0.0.1,localhost")


# -------- Gradio 5.15.0 + gradio_client 1.7.0 兼容性补丁 --------
# 某些情况下 gradio 会在生成 API info 时遇到 JSON Schema 中 `additionalProperties: true`
# 导致 gradio_client 类型转换把 bool 当作 dict 处理并崩溃：
# TypeError: argument of type 'bool' is not iterable
#
# 这里对 gradio_client 的 get_type 做一个安全兜底：遇到 bool schema 时返回 Any。
try:
    import gradio_client.utils as _gc_utils

    _orig_get_type = _gc_utils.get_type
    _orig_json_schema_to_python_type = _gc_utils._json_schema_to_python_type

    def _patched_get_type(schema):  # type: ignore[override]
        if isinstance(schema, bool):
            return "Any"
        return _orig_get_type(schema)

    _gc_utils.get_type = _patched_get_type  # type: ignore[assignment]

    def _patched_json_schema_to_python_type(schema, defs=None):  # type: ignore[override]
        if isinstance(schema, bool):
            return "Any"
        return _orig_json_schema_to_python_type(schema, defs)

    _gc_utils._json_schema_to_python_type = _patched_json_schema_to_python_type  # type: ignore[assignment]
except Exception:
    pass


def _auth_headers(token: Optional[str]) -> Dict[str, str]:
    return {"Authorization": f"Bearer {token}"} if token else {}


def login(username: str, password: str) -> Tuple[str, str, str]:
    if not username or not password:
        return "", "请输入用户名和密码", ""
    try:
        resp = requests.post(
            f"{API_BASE}/auth/token",
            data={"username": username, "password": password},
            timeout=30,
        )
        if resp.status_code != 200:
            return "", f"登录失败：{resp.json().get('detail', resp.text)}", ""
        token = resp.json()["access_token"]
        me = requests.get(
            f"{API_BASE}/auth/me",
            headers=_auth_headers(token),
            timeout=30,
        ).json()
        welcome = f"已登录用户：{me['username']}（{'管理员' if me['is_admin'] else '普通用户'}）"
        return token, welcome, json.dumps(me, ensure_ascii=False)
    except Exception as e:
        return "", f"登录异常：{e}", ""


def load_documents(token: str) -> List[Dict]:
    if not token:
        return []
    resp = requests.get(
        f"{API_BASE}/documents",
        headers=_auth_headers(token),
        timeout=60,
    )
    if resp.status_code != 200:
        return []
    return resp.json()


def refresh_doc_table(token: str) -> List[List]:
    docs = load_documents(token)
    table = [
        [
            d["id"],
            d["original_name"],
            f"{d['size_bytes'] / 1024:.1f} KB",
            d.get("group_id") or "-",
            "私有" if d["is_private"] else "群组/共享",
            d["created_at"].replace("T", " ")[:19],
        ]
        for d in docs
    ]
    return table


def upload_file(
    token: str,
    file,
    scope: str,
    group_id_text: str,
) -> Tuple[str, List[List]]:
    if not token:
        return "请先登录", []
    if file is None:
        return "请先选择文件", []
    is_private = scope == "私有"
    group_id = None
    if scope == "群组共享":
        try:
            group_id = int(group_id_text)
        except Exception:
            return "请填写有效的群组ID（整数）", []
    files = {"file": (file.name, open(file.name, "rb").read())}
    data = {"is_private": str(is_private).lower()}
    if group_id is not None:
        data["group_id"] = str(group_id)
    resp = requests.post(
        f"{API_BASE}/documents/upload",
        headers=_auth_headers(token),
        data=data,
        files=files,
        timeout=600,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return f"上传失败：{detail}", []
    msg = "上传并索引成功"
    return msg, refresh_doc_table(token)


def delete_document_ui(token: str, doc_id_text: str) -> Tuple[str, List[List]]:
    if not token:
        return "请先登录", []
    try:
        doc_id = int(doc_id_text)
    except Exception:
        return "请填写有效的文献ID（整数）", []
    resp = requests.delete(
        f"{API_BASE}/documents/{doc_id}",
        headers=_auth_headers(token),
        timeout=120,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return f"删除失败：{detail}", []
    return "删除成功", refresh_doc_table(token)


def rag_ask(
    token: str,
    question: str,
    scope: str,
    group_ids_text: str,
) -> Tuple[str, str]:
    if not token:
        return "请先登录", ""
    if not question.strip():
        return "请输入问题", ""
    scope_map = {"仅自己私有文献": "private", "指定群组共享文献": "groups", "全部可见文献": "all"}
    payload: Dict = {"question": question, "scope": scope_map[scope]}
    if scope == "指定群组共享文献":
        try:
            ids = [int(x) for x in group_ids_text.split(",") if x.strip()]
        except Exception:
            return "群组ID格式错误，应为用逗号分隔的整数", ""
        payload["group_ids"] = ids
    resp = requests.post(
        f"{API_BASE}/rag/query",
        headers={**_auth_headers(token), "Content-Type": "application/json"},
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=600,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return f"问答失败：{detail}", ""
    data = resp.json()
    answer = data.get("answer", "")
    sources = data.get("sources", [])
    src_lines = [
        f"文献ID {s['document_id']} - {s['original_name']} - 块 {s['chunk_index']}"
        for s in sources
    ]
    src_text = "\n".join(src_lines) if src_lines else "无引用来源"
    return answer, src_text


def rag_compare_ui(
    token: str,
    question: str,
    doc_ids_text: str,
) -> Tuple[str, str]:
    if not token:
        return "请先登录", ""
    if not question.strip():
        return "请输入问题", ""
    try:
        ids = [int(x) for x in doc_ids_text.split(",") if x.strip()]
    except Exception:
        return "文献ID格式错误，应为用逗号分隔的整数", ""
    payload = {"question": question, "document_ids": ids}
    resp = requests.post(
        f"{API_BASE}/rag/compare",
        headers={**_auth_headers(token), "Content-Type": "application/json"},
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=600,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return f"对比问答失败：{detail}", ""
    data = resp.json()
    answer = data.get("answer", "")
    sources = data.get("sources", [])
    src_lines = [
        f"文献ID {s['document_id']} - {s['original_name']} - 块 {s['chunk_index']}"
        for s in sources
    ]
    src_text = "\n".join(src_lines) if src_lines else "无引用来源"
    return answer, src_text


def load_history_ui(token: str, keyword: str) -> List[List]:
    if not token:
        return []
    params = {}
    if keyword.strip():
        params["q"] = keyword
    resp = requests.get(
        f"{API_BASE}/history",
        headers=_auth_headers(token),
        params=params,
        timeout=120,
    )
    if resp.status_code != 200:
        return []
    rows = []
    for h in resp.json():
        rows.append(
            [
                h["id"],
                h["created_at"].replace("T", " ")[:19],
                (h["question"][:50] + "...") if len(h["question"]) > 50 else h["question"],
            ]
        )
    return rows


def build_dashboard_ui(token: str) -> Dict:
    if not token:
        return {}
    resp = requests.get(
        f"{API_BASE}/admin/dashboard",
        headers=_auth_headers(token),
        timeout=60,
    )
    if resp.status_code != 200:
        return {}
    return resp.json()


def load_student_papers(token: str) -> List[Dict]:
    if not token:
        return []
    resp = requests.get(
        f"{API_BASE}/student_papers",
        headers=_auth_headers(token),
        timeout=60,
    )
    if resp.status_code != 200:
        return []
    return resp.json()


def create_student_paper_ui(token: str, title: str) -> Tuple[str, List[List]]:
    if not token:
        return "请先登录", []
    if not title.strip():
        return "请输入论文标题", []
    payload = {"title": title}
    resp = requests.post(
        f"{API_BASE}/student_papers/create",
        headers={**_auth_headers(token), "Content-Type": "application/json"},
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=60,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return f"创建失败：{detail}", []
    msg = "创建成功"
    # 返回最新列表
    papers = load_student_papers(token)
    table = [
        [
            p["id"],
            p["title"],
            p["created_at"].replace("T", " ")[:19],
        ]
        for p in papers
    ]
    return msg, table


def load_student_paper_detail_ui(token: str, paper_id_text: str) -> Tuple[str, str]:
    if not token:
        return "", ""
    try:
        paper_id = int(paper_id_text)
    except Exception:
        return "", ""
    resp = requests.get(
        f"{API_BASE}/student_papers/{paper_id}",
        headers=_auth_headers(token),
        timeout=60,
    )
    if resp.status_code != 200:
        return "", ""
    data = resp.json()
    return data.get("title", ""), data.get("content", "")


def save_student_paper_ui(
    token: str,
    paper_id_text: str,
    content: str,
) -> str:
    if not token:
        return "请先登录"
    try:
        paper_id = int(paper_id_text)
    except Exception:
        return "请填写有效的论文ID（整数）"
    payload = {"content": content}
    resp = requests.post(
        f"{API_BASE}/student_papers/{paper_id}/save",
        headers={**_auth_headers(token), "Content-Type": "application/json"},
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=60,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return f"保存失败：{detail}"
    return "已保存"


def mentor_chat_ui(
    token: str,
    paper_id_text: str,
    question: str,
) -> Tuple[str, str]:
    if not token:
        return "请先登录", ""
    if not question.strip():
        return "请输入问题", ""
    try:
        paper_id = int(paper_id_text)
    except Exception:
        return "请填写有效的论文ID（整数）", ""
    payload = {"question": question}
    resp = requests.post(
        f"{API_BASE}/student_papers/{paper_id}/mentor_chat",
        headers={**_auth_headers(token), "Content-Type": "application/json"},
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=600,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return f"导师回答失败：{detail}", ""
    data = resp.json()
    answer = data.get("answer", "")
    citations = data.get("citations", []) or []
    # 把引用列表整理为简单可复制的行
    cite_lines = [f"- {c}" for c in citations] if citations else ["（暂无引用建议）"]
    return answer, "\n".join(cite_lines)


def load_papers(token: str) -> List[Dict]:
    if not token:
        return []
    resp = requests.get(
        f"{API_BASE}/papers",
        headers=_auth_headers(token),
        timeout=60,
    )
    if resp.status_code != 200:
        return []
    return resp.json()


def load_paper_profile_ui(token: str, paper_id_text: str) -> str:
    if not token:
        return "请先登录"
    try:
        paper_id = int(paper_id_text)
    except Exception:
        return "请填写有效的论文ID（整数）"
    resp = requests.get(
        f"{API_BASE}/papers/{paper_id}/profile",
        headers=_auth_headers(token),
        timeout=60,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return f"获取论文结构化信息失败：{detail}"
    data = resp.json()
    return json.dumps(data, ensure_ascii=False, indent=2) if data else "暂无结构化信息"


def load_paper_notes_ui(token: str, paper_id_text: str) -> str:
    if not token:
        return ""
    try:
        paper_id = int(paper_id_text)
    except Exception:
        return ""
    resp = requests.get(
        f"{API_BASE}/papers/{paper_id}/notes",
        headers=_auth_headers(token),
        timeout=60,
    )
    if resp.status_code != 200:
        return ""
    return resp.json().get("content", "")


def save_paper_notes_ui(token: str, paper_id_text: str, content: str) -> str:
    if not token:
        return "请先登录"
    try:
        paper_id = int(paper_id_text)
    except Exception:
        return "请填写有效的论文ID（整数）"
    resp = requests.post(
        f"{API_BASE}/papers/{paper_id}/notes",
        headers={**_auth_headers(token)},
        params={"content": content},
        timeout=60,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return f"保存失败：{detail}"
    return "已保存"


def paper_chat_ui(token: str, paper_id_text: str, question: str) -> Tuple[str, str]:
    if not token:
        return "请先登录", ""
    if not question.strip():
        return "请输入问题", ""
    try:
        paper_id = int(paper_id_text)
    except Exception:
        return "请填写有效的论文ID（整数）", ""
    payload = {"paper_id": paper_id, "question": question}
    resp = requests.post(
        f"{API_BASE}/papers/chat",
        headers={**_auth_headers(token), "Content-Type": "application/json"},
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=600,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return f"问答失败：{detail}", ""
    data = resp.json()
    answer = data.get("answer", "")
    sources = data.get("sources", [])
    src_lines = [
        f"文献ID {s['document_id']} - {s['original_name']} - 块 {s['chunk_index']}"
        for s in sources
    ]
    src_text = "\n".join(src_lines) if src_lines else "无引用来源"
    return answer, src_text


def paper_compare_ui_workspace(
    token: str,
    paper_ids_text: str,
    question: str,
) -> Tuple[str, str]:
    if not token:
        return "请先登录", ""
    if not question.strip():
        return "请输入问题", ""
    try:
        ids = [int(x) for x in paper_ids_text.split(",") if x.strip()]
    except Exception:
        return "论文ID格式错误，应为用逗号分隔的整数", ""
    payload = {"paper_ids": ids, "question": question}
    resp = requests.post(
        f"{API_BASE}/papers/compare",
        headers={**_auth_headers(token), "Content-Type": "application/json"},
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=600,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return f"对比失败：{detail}", ""
    data = resp.json()
    answer = data.get("answer", "")
    sources = data.get("sources", [])
    src_lines = [
        f"文献ID {s['document_id']} - {s['original_name']} - 块 {s['chunk_index']}"
        for s in sources
    ]
    src_text = "\n".join(src_lines) if src_lines else "无引用来源"
    return answer, src_text


# -------------------- Research Copilot: Conversations + Chat --------------------


def list_conversations_ui(token: str) -> List[List]:
    if not token:
        return []
    resp = requests.get(
        f"{API_BASE}/conversations",
        headers=_auth_headers(token),
        timeout=60,
    )
    if resp.status_code != 200:
        return []
    rows = []
    for c in resp.json():
        rows.append(
            [
                c["id"],
                c.get("title") or f"会话 {c['id']}",
                c.get("collection_id") or "-",
                c.get("student_paper_id") or "-",
                c["created_at"].replace("T", " ")[:19],
            ]
        )
    return rows


def create_conversation_ui(
    token: str,
    title: str,
    collection_id_text: str,
    student_paper_id_text: str,
) -> Tuple[str, List[List]]:
    if not token:
        return "请先登录", []
    payload: Dict[str, Optional[int | str]] = {"title": title or None}
    if collection_id_text.strip():
        try:
            payload["collection_id"] = int(collection_id_text)
        except Exception:
            return "collection_id 应为整数", []
    if student_paper_id_text.strip():
        try:
            payload["student_paper_id"] = int(student_paper_id_text)
        except Exception:
            return "student_paper_id 应为整数", []
    resp = requests.post(
        f"{API_BASE}/conversations",
        headers={**_auth_headers(token), "Content-Type": "application/json"},
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        timeout=30,
    )
    if resp.status_code != 200:
        try:
            detail = resp.json().get("detail", resp.text)
        except Exception:
            detail = resp.text
        return f"创建会话失败：{detail}", []
    msg = "会话创建成功"
    return msg, list_conversations_ui(token)


def load_conversation_messages_ui(
    token: str,
    conversation_id_text: str,
) -> List[Tuple[str, str]]:
    """将 Message 列表转换为 Chatbot 的 (user, assistant) 对话历史。"""
    if not token:
        return []
    try:
        cid = int(conversation_id_text)
    except Exception:
        return []
    resp = requests.get(
        f"{API_BASE}/conversations/{cid}/messages",
        headers=_auth_headers(token),
        params={"limit": 200},
        timeout=60,
    )
    if resp.status_code != 200:
        return []
    data = resp.json()
    history: List[Tuple[str, str]] = []
    current_user_msg: Optional[str] = None
    for m in data:
        if m["role"] == "user":
            # 开启新的 turn
            if current_user_msg is not None:
                # 上一轮用户没有等到助手回应，先推空
                history.append((current_user_msg, ""))
            current_user_msg = m["content"]
        elif m["role"] == "assistant":
            if current_user_msg is None:
                history.append(("", m["content"]))
            else:
                history.append((current_user_msg, m["content"]))
                current_user_msg = None
    if current_user_msg is not None:
        history.append((current_user_msg, ""))
    return history


def _parse_sse_answer(raw_text: str) -> str:
    """
    从 SSE 文本中提取拼接后的回答，忽略 [END] 标记。
    """
    lines = raw_text.splitlines()
    chunks: List[str] = []
    for ln in lines:
        if not ln.startswith("data:"):
            continue
        content = ln[len("data:") :].strip()
        if content == "[END]":
            break
        chunks.append(content)
    return "".join(chunks)


def chat_send_ui(
    token: str,
    conversation_id_text: str,
    user_input: str,
    history: List[Tuple[str, str]],
) -> Tuple[List[Tuple[str, str]], str]:
    """
    - 先把 user 消息写入 /conversations/{id}/messages
    - 再调用 /chat/stream，解析 SSE 得到完整回答
    - 最后重新加载消息列表为 Chatbot 历史
    """
    if not token:
        return history, "请先登录"
    if not user_input.strip():
        return history, "请输入问题"
    try:
        cid = int(conversation_id_text)
    except Exception:
        return history, "请填写有效的会话ID（整数）"

    # 写入用户消息
    payload_msg = {"role": "user", "content": user_input, "sources": None}
    resp_msg = requests.post(
        f"{API_BASE}/conversations/{cid}/messages",
        headers={**_auth_headers(token), "Content-Type": "application/json"},
        data=json.dumps(payload_msg, ensure_ascii=False).encode("utf-8"),
        timeout=30,
    )
    if resp_msg.status_code != 200:
        try:
            detail = resp_msg.json().get("detail", resp_msg.text)
        except Exception:
            detail = resp_msg.text
        return history, f"发送消息失败：{detail}"

    # 调用流式接口（这里一次性获取 SSE 文本，再解析）
    resp_stream = requests.post(
        f"{API_BASE}/chat/stream",
        headers=_auth_headers(token),
        params={"conversation_id": cid},
        timeout=600,
    )
    if resp_stream.status_code != 200:
        try:
            detail = resp_stream.json().get("detail", resp_stream.text)
        except Exception:
            detail = resp_stream.text
        return history, f"生成回答失败：{detail}"

    full_sse_text = resp_stream.text
    answer = _parse_sse_answer(full_sse_text)

    # 重新加载消息，映射到 Chatbot 历史
    new_history = load_conversation_messages_ui(token, str(cid))
    return new_history, ""


def main():
    with gr.Blocks(title="本地文献智能体知识库", theme=gr.themes.Soft()) as demo:
        gr.Markdown("## 本地文献智能体知识库（多用户 / 群组共享 / RAG 问答）")

        token_state = gr.State("")
        user_state = gr.State("")

        with gr.Tab("登录"):
            gr.Markdown("### 登录")
            login_username = gr.Textbox(label="用户名", value="admin")
            login_password = gr.Textbox(label="密码", type="password", value="admin123")
            login_button = gr.Button("登录", variant="primary")
            login_status = gr.Markdown("")
            login_user_json = gr.Textbox(
                label="用户信息（JSON）", interactive=False, lines=3
            )

            def on_login(username, password):
                token, msg, user_json = login(username, password)
                return token, msg, user_json, token, user_json

            login_button.click(
                on_login,
                inputs=[login_username, login_password],
                outputs=[token_state, login_status, login_user_json, token_state, user_state],
            )

        with gr.Tab("文献管理"):
            gr.Markdown("### 文献上传与管理")
            with gr.Row():
                upload_file_comp = gr.File(label="选择文献文件（PDF/TXT/DOCX/XLSX）")
                upload_scope = gr.Radio(
                    ["私有", "群组共享"],
                    value="私有",
                    label="共享范围",
                )
                upload_group_id = gr.Textbox(
                    label="群组ID（当选择群组共享时必填）",
                    placeholder="例如：1 或 1,2",
                )
            upload_button = gr.Button("上传并构建索引", variant="primary")
            upload_status = gr.Markdown("")

            gr.Markdown("#### 当前可见文献列表")
            doc_table = gr.Dataframe(
                headers=["ID", "文件名", "大小", "群组ID", "可见性", "上传时间"],
                datatype=["number", "str", "str", "str", "str", "str"],
                interactive=False,
                row_count=(0, "dynamic"),
            )

            refresh_docs_button = gr.Button("刷新文献列表")
            delete_doc_id = gr.Textbox(label="要删除的文献ID")
            delete_doc_button = gr.Button("删除选中文献", variant="secondary")
            delete_status = gr.Markdown("")

            upload_button.click(
                upload_file,
                inputs=[token_state, upload_file_comp, upload_scope, upload_group_id],
                outputs=[upload_status, doc_table],
            )

            refresh_docs_button.click(
                refresh_doc_table,
                inputs=[token_state],
                outputs=[doc_table],
            )

            delete_doc_button.click(
                delete_document_ui,
                inputs=[token_state, delete_doc_id],
                outputs=[delete_status, doc_table],
            )

        with gr.Tab("RAG 问答"):
            gr.Markdown("### 基于权限范围的文献问答")
            question = gr.Textbox(
                label="请输入你的问题",
                lines=4,
                placeholder="例如：请总结我有关某主题的主要研究结论？",
            )
            scope = gr.Radio(
                ["仅自己私有文献", "指定群组共享文献", "全部可见文献"],
                value="全部可见文献",
                label="检索范围",
            )
            scope_group_ids = gr.Textbox(
                label="当选择“指定群组共享文献”时，填写群组ID（逗号分隔）",
                placeholder="例如：1,2,3",
            )
            ask_button = gr.Button("开始问答", variant="primary")
            answer_output = gr.Markdown(label="回答")
            source_output = gr.Textbox(
                label="引用来源（文献ID / 名称 / 块编号）",
                lines=6,
                interactive=False,
            )

            ask_button.click(
                rag_ask,
                inputs=[token_state, question, scope, scope_group_ids],
                outputs=[answer_output, source_output],
            )

        with gr.Tab("对比问答"):
            gr.Markdown("### 多文献对比问答")
            compare_question = gr.Textbox(
                label="问题",
                lines=4,
                placeholder="例如：对比几篇文献中的实验方法和主要结论差异。",
            )
            compare_doc_ids = gr.Textbox(
                label="要对比的文献ID列表（逗号分隔）",
                placeholder="例如：1,2,5",
            )
            compare_button = gr.Button("开始对比问答", variant="primary")
            compare_answer = gr.Markdown(label="对比回答")
            compare_sources = gr.Textbox(
                label="引用来源",
                lines=6,
                interactive=False,
            )

            compare_button.click(
                rag_compare_ui,
                inputs=[token_state, compare_question, compare_doc_ids],
                outputs=[compare_answer, compare_sources],
            )

        with gr.Tab("历史记录"):
            gr.Markdown("### 一周内问答历史")
            history_keyword = gr.Textbox(label="按关键词搜索问题或回答")
            history_button = gr.Button("搜索历史")
            history_table = gr.Dataframe(
                headers=["ID", "时间", "问题（摘要）"],
                datatype=["number", "str", "str"],
                interactive=False,
                row_count=(0, "dynamic"),
            )

            history_button.click(
                load_history_ui,
                inputs=[token_state, history_keyword],
                outputs=[history_table],
            )

        with gr.Tab("管理员仪表盘"):
            gr.Markdown("### 管理员仪表盘（仅管理员账号可用）")
            dash_button = gr.Button("刷新仪表盘")
            dash_markdown = gr.Markdown("")

            def on_dash(token: str) -> str:
                data = build_dashboard_ui(token)
                if not data:
                    return "无法获取仪表盘数据（可能未登录或非管理员）。"
                md = [
                    f"- 总文献数量：**{data['total_documents']}**",
                    f"- 总存储容量：**{data['total_storage_bytes'] / (1024 * 1024):.2f} MB**",
                    f"- 向量索引条目（近似）：**{data['total_indexed_chunks']}**",
                    f"- 用户数量：**{data['total_users']}**",
                    f"- 群组数量：**{data['total_groups']}**",
                    f"- 近一周问答次数：**{data['recent_questions']}**",
                    "",
                    "#### 最近上传文献：",
                ]
                for doc in data["recent_documents"]:
                    md.append(
                        f"- ID {doc['id']} | {doc['original_name']} | "
                        f"{doc['size_bytes'] / 1024:.1f} KB | "
                        f"{doc['created_at'].replace('T', ' ')[:19]}"
                    )
                return "\n".join(md)

            dash_button.click(
                on_dash,
                inputs=[token_state],
                outputs=[dash_markdown],
            )

        with gr.Tab("论文工作区"):
            gr.Markdown("### 论文工作区（结构化信息 / 阅读 / 对话 / 多论文对比）")
            with gr.Row():
                # 左侧：论文列表
                with gr.Column(scale=1):
                    gr.Markdown("#### 已索引论文列表")
                    paper_table = gr.Dataframe(
                        headers=["论文ID", "文献ID", "标题/文件名", "创建时间"],
                        datatype=["number", "number", "str", "str"],
                        interactive=False,
                        row_count=(0, "dynamic"),
                    )
                    refresh_papers_btn = gr.Button("刷新论文列表")
                    selected_paper_id = gr.Textbox(
                        label="当前论文ID",
                        placeholder="从列表中选择后，填入此处",
                    )

                # 中间：Profile / 笔记
                with gr.Column(scale=2):
                    gr.Markdown("#### 论文结构化信息（Profile）")
                    profile_view = gr.Code(
                        label="paper_profile.json（只读）",
                        language="json",
                        interactive=False,
                    )
                    gr.Markdown("#### 论文笔记（Markdown）")
                    notes_box = gr.Textbox(
                        label="paper_notes.md",
                        lines=12,
                        placeholder="在这里整理你的阅读笔记和思考……",
                    )
                    load_notes_btn = gr.Button("加载当前论文笔记")
                    save_notes_btn = gr.Button("保存笔记")
                    notes_status = gr.Markdown("")

                # 右侧：对话助手 + 多论文对比
                with gr.Column(scale=2):
                    gr.Markdown("#### 当前论文对话助手")
                    paper_question = gr.Textbox(
                        label="问题",
                        lines=4,
                        placeholder="例如：这篇论文的核心科学问题是什么？方法有哪些关键步骤？",
                    )
                    paper_chat_btn = gr.Button("基于当前论文对话", variant="primary")
                    paper_chat_answer = gr.Markdown(label="回答")
                    paper_chat_sources = gr.Textbox(
                        label="引用来源",
                        lines=6,
                        interactive=False,
                    )

                    gr.Markdown("#### 多论文对比（基于论文工作区）")
                    compare_paper_ids = gr.Textbox(
                        label="要对比的论文ID列表（逗号分隔）",
                        placeholder="例如：1,2,3",
                    )
                    compare_ws_question = gr.Textbox(
                        label="对比问题",
                        lines=3,
                        placeholder="例如：对比这些论文的研究方法和实验结果。",
                    )
                    compare_ws_btn = gr.Button("开始多论文对比", variant="secondary")
                    compare_ws_answer = gr.Markdown(label="对比回答")
                    compare_ws_sources = gr.Textbox(
                        label="引用来源",
                        lines=6,
                        interactive=False,
                    )

            # 交互逻辑

            def refresh_paper_table(token: str) -> List[List]:
                papers = load_papers(token)
                rows: List[List] = []
                for p in papers:
                    rows.append(
                        [
                            p["id"],
                            p["document_id"],
                            p.get("title") or p.get("file_path") or "",
                            p["created_at"].replace("T", " ")[:19],
                        ]
                    )
                return rows

            refresh_papers_btn.click(
                refresh_paper_table,
                inputs=[token_state],
                outputs=[paper_table],
            )

            # 加载 profile 与笔记
            def load_profile_and_notes(token: str, paper_id_text: str) -> Tuple[str, str]:
                profile_json = load_paper_profile_ui(token, paper_id_text)
                notes = load_paper_notes_ui(token, paper_id_text)
                return profile_json, notes

            load_notes_btn.click(
                load_profile_and_notes,
                inputs=[token_state, selected_paper_id],
                outputs=[profile_view, notes_box],
            )

            save_notes_btn.click(
                save_paper_notes_ui,
                inputs=[token_state, selected_paper_id, notes_box],
                outputs=[notes_status],
            )

            paper_chat_btn.click(
                paper_chat_ui,
                inputs=[token_state, selected_paper_id, paper_question],
                outputs=[paper_chat_answer, paper_chat_sources],
            )

            compare_ws_btn.click(
                paper_compare_ui_workspace,
                inputs=[token_state, compare_paper_ids, compare_ws_question],
                outputs=[compare_ws_answer, compare_ws_sources],
            )

        with gr.Tab("Research Copilot"):
            gr.Markdown("### 多轮对话科研助手（基于 Conversation + Research Agent）")
            with gr.Row():
                # 左侧：会话列表
                with gr.Column(scale=1):
                    gr.Markdown("#### 会话列表（一个会话 = 一个研究主题）")
                    convo_table = gr.Dataframe(
                        headers=["会话ID", "标题", "collection_id", "student_paper_id", "创建时间"],
                        datatype=["number", "str", "str", "str", "str"],
                        interactive=False,
                        row_count=(0, "dynamic"),
                    )
                    refresh_convos_btn = gr.Button("刷新会话列表")
                    new_convo_title = gr.Textbox(label="新建会话标题（可选）")
                    new_convo_collection = gr.Textbox(
                        label="collection_id（可选，整数）",
                        placeholder="目前可暂时留空，后续用于限定文献集合",
                    )
                    new_convo_student_paper = gr.Textbox(
                        label="student_paper_id（可选，整数）",
                        placeholder="若与某篇学生论文绑定，则填写其ID",
                    )
                    create_convo_btn = gr.Button("新建会话", variant="primary")
                    convo_status = gr.Markdown("")
                    current_convo_id = gr.Textbox(
                        label="当前会话ID",
                        placeholder="从上方列表中选定后填入此处",
                    )

                # 中间：Chat 窗口
                with gr.Column(scale=2):
                    gr.Markdown("#### Chat 窗口")
                    chat_history = gr.Chatbot(
                        label="对话历史",
                        height=400,
                    )
                    user_input = gr.Textbox(
                        label="输入你的科研问题",
                        lines=3,
                        placeholder="例如：请帮我梳理基于 Transformer 的图生成研究方向，并给出可行的实验设计建议。",
                    )
                    send_btn = gr.Button("发送并生成回答", variant="primary")
                    chat_status = gr.Markdown("")

                # 右侧：Paper Explorer（占位版：复用论文列表与 profile）
                with gr.Column(scale=2):
                    gr.Markdown("#### Paper Explorer（文献浏览）")
                    explorer_paper_table = gr.Dataframe(
                        headers=["论文ID", "文献ID", "标题/文件名", "创建时间"],
                        datatype=["number", "number", "str", "str"],
                        interactive=False,
                        row_count=(0, "dynamic"),
                    )
                    refresh_explorer_papers_btn = gr.Button("刷新论文列表")
                    explorer_paper_id = gr.Textbox(
                        label="浏览论文ID",
                        placeholder="在右侧输入想要查看的论文ID",
                    )
                    explorer_profile = gr.Code(
                        label="论文 Profile（paper_profile.json）",
                        language="json",
                        interactive=False,
                    )

            # 交互逻辑：会话

            refresh_convos_btn.click(
                list_conversations_ui,
                inputs=[token_state],
                outputs=[convo_table],
            )

            create_convo_btn.click(
                create_conversation_ui,
                inputs=[
                    token_state,
                    new_convo_title,
                    new_convo_collection,
                    new_convo_student_paper,
                ],
                outputs=[convo_status, convo_table],
            )

            # 初始化选定会话时的消息加载
            def load_chat_for_convo(token: str, convo_id: str) -> List[Tuple[str, str]]:
                return load_conversation_messages_ui(token, convo_id)

            # 当 current_convo_id 改变时，刷新 Chat 历史
            current_convo_id.change(
                load_chat_for_convo,
                inputs=[token_state, current_convo_id],
                outputs=[chat_history],
            )

            send_btn.click(
                chat_send_ui,
                inputs=[token_state, current_convo_id, user_input, chat_history],
                outputs=[chat_history, chat_status],
            )

            # 交互逻辑：Paper Explorer

            def refresh_explorer_paper_table(token: str) -> List[List]:
                papers = load_papers(token)
                rows: List[List] = []
                for p in papers:
                    rows.append(
                        [
                            p["id"],
                            p["document_id"],
                            p.get("title") or p.get("file_path") or "",
                            p["created_at"].replace("T", " ")[:19],
                        ]
                    )
                return rows

            refresh_explorer_papers_btn.click(
                refresh_explorer_paper_table,
                inputs=[token_state],
                outputs=[explorer_paper_table],
            )

            explorer_paper_id.change(
                load_paper_profile_ui,
                inputs=[token_state, explorer_paper_id],
                outputs=[explorer_profile],
            )

        with gr.Tab("学生论文工作区"):
            gr.Markdown("### 学生论文写作工作区（Markdown 编辑 + 导师 Agent）")
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("#### 学生论文列表")
                    student_paper_table = gr.Dataframe(
                        headers=["论文ID", "标题", "创建时间"],
                        datatype=["number", "str", "str"],
                        interactive=False,
                        row_count=(0, "dynamic"),
                    )
                    refresh_sp_btn = gr.Button("刷新论文列表")
                    new_sp_title = gr.Textbox(label="新建论文标题")
                    create_sp_btn = gr.Button("新建论文", variant="primary")
                    create_sp_status = gr.Markdown("")
                    current_sp_id = gr.Textbox(
                        label="当前论文ID",
                        placeholder="从列表中选择后填入此处",
                    )

                with gr.Column(scale=2):
                    gr.Markdown("#### 论文编辑器（Markdown）")
                    sp_title_box = gr.Textbox(
                        label="标题（只读，创建时确定）",
                        interactive=False,
                    )
                    sp_editor = gr.Textbox(
                        label="paper.md",
                        lines=20,
                        placeholder="# Introduction\n\n在这里开始撰写你的论文……",
                    )
                    load_sp_btn = gr.Button("加载当前论文内容")
                    save_sp_btn = gr.Button("保存论文内容")
                    sp_save_status = gr.Markdown("")

                with gr.Column(scale=2):
                    gr.Markdown("#### 导师 Agent")
                    mentor_question = gr.Textbox(
                        label="向导师提问",
                        lines=4,
                        placeholder="例如：我的研究是否有人做过？方法是否合理？还需要补充哪些实验？",
                    )
                    mentor_btn = gr.Button("向导师提问", variant="primary")
                    mentor_answer = gr.Markdown(label="导师回答")
                    mentor_citations = gr.Markdown(label="引用建议（可点击复制到论文）")

            def refresh_student_paper_table(token: str) -> List[List]:
                papers = load_student_papers(token)
                rows: List[List] = []
                for p in papers:
                    rows.append(
                        [
                            p["id"],
                            p["title"],
                            p["created_at"].replace("T", " ")[:19],
                        ]
                    )
                return rows

            refresh_sp_btn.click(
                refresh_student_paper_table,
                inputs=[token_state],
                outputs=[student_paper_table],
            )

            create_sp_btn.click(
                create_student_paper_ui,
                inputs=[token_state, new_sp_title],
                outputs=[create_sp_status, student_paper_table],
            )

            load_sp_btn.click(
                load_student_paper_detail_ui,
                inputs=[token_state, current_sp_id],
                outputs=[sp_title_box, sp_editor],
            )

            save_sp_btn.click(
                save_student_paper_ui,
                inputs=[token_state, current_sp_id, sp_editor],
                outputs=[sp_save_status],
            )

            mentor_btn.click(
                mentor_chat_ui,
                inputs=[token_state, current_sp_id, mentor_question],
                outputs=[mentor_answer, mentor_citations],
            )

    # 避免 gradio_client 在生成 API schema 时触发类型转换 bug，这里禁用 API 展示。
    # 本项目是本地使用为主，因此也不需要 share 公网链接。
    # 端口优先使用环境变量，避免 7860 被占用导致启动失败：
    #   GRADIO_SERVER_PORT=7861 python app.py
    # 如果不设置，则默认 7860
    server_port_env = os.getenv("GRADIO_SERVER_PORT")
    server_port = int(server_port_env) if server_port_env else 7860

    demo.launch(
        server_name=os.getenv("GRADIO_SERVER_NAME", "127.0.0.1"),
        server_port=server_port,
        share=False,
        debug=True,
        show_api=False,
    )


if __name__ == "__main__":
    main()

