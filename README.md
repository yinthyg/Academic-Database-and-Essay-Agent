## 本地文献智能体知识库（多用户 / 群组共享 / RAG 问答）

本项目在本地（优先 Windows）运行，为实验室/课题组提供一个**本地文献知识库 + 研究对话助手**：支持文献上传入库、RAG 问答、多文献对比、学生写作工作区、管理员后台等。

默认管理员账号：**admin / admin123**（首次启动自动创建）。

### 项目架构（高层）

```
┌──────────────┐        HTTP(S)        ┌──────────────────────┐
│  FigmaUI 前端 │  <----------------->  │  FastAPI 后端 (/api)  │
│  (Vite/React) │                      │  Auth/Docs/RAG/Admin   │
└──────────────┘                       └───────────┬───────────┘
                                                    │
                                                    │  本地持久化
                                                    ▼
                                            ┌───────────────────┐
                                            │ data/              │
                                            │ - app.db (SQLite)  │
                                            │ - chroma/ (向量库) │
                                            │ - uploads/ (原文件)│
                                            │ - papers/ (工作区) │
                                            └───────────────────┘

FastAPI 还会通过 OpenAI 兼容接口调用 vLLM：
┌──────────────────────────┐
│ vLLM (OpenAI compatible)  │  <- DeepSeek-R1 等模型
│ http://127.0.0.1:8000/v1  │
└──────────────────────────┘
```

**关键数据流**：上传文献 → 提取文本 → 分块 → 计算 embedding → 写入 Chroma → 生成 `paper_profile.json`（结构化解析）与 `chunks.json`（切片） → 前端用于详情页预览与后续问答引用。

### 技术栈

- **前端（默认）**：`figmaUI/`
  - Vite + React 18 + TypeScript
  - Tailwind CSS（及 Radix UI 组件）
  - 路由：React Router（`createBrowserRouter`）
  - SSE/流式：`/api/chat/stream`（前端支持“思考中 + 流式输出”体验）
- **后端**：`backend/`
  - FastAPI + SQLAlchemy + SQLite
  - 认证：OAuth2 password flow + JWT
- **RAG / 向量库**
  - 向量库：Chroma（Persistent）
  - 嵌入模型：SentenceTransformers（默认 `BAAI/bge-small-zh-v1.5`）
  - 分块：LangChain `RecursiveCharacterTextSplitter`
- **LLM 推理**
  - 通过 vLLM 提供 OpenAI 兼容 API（后端调用 `VLLM_API_BASE`）
- **文档解析**
  - PDF：pdfplumber / pypdf
  - DOCX：python-docx
  - XLSX：pandas

### 目录结构

- `backend/`：FastAPI 后端（认证、用户/群组、文献管理、RAG、历史、仪表盘、流式对话）
- `figmaUI/`：新版前端（Research Copilot / Student Workspace / 文献上传与管理 / 管理员后台）
- `webui/`：旧版 Gradio Web UI（可选）
- `data/`：本地数据目录
  - `app.db`：SQLite
  - `chroma/`：Chroma 向量库持久化
  - `uploads/{user_id}/`：上传原文件
  - `papers/{paper_id}/`：文献工作区（`paper_profile.json`、`chunks.json`、`paper_notes.md` 等）
- 启动脚本（Windows）
  - `start_vllm.bat`：启动 vLLM（需自行准备模型与环境）
  - `start_backend.bat`：启动 FastAPI 后端（默认 `127.0.0.1:9000`）
  - `start_figma_ui.bat`：启动前端（默认 `127.0.0.1:5173`）
  - `start_webui.bat`：启动 Gradio UI（可选）

---

## 快速开始（Windows / 开发模式）

### 1) 安装后端依赖

项目已自带虚拟环境 `agent` 与 `requirements.txt`。如需重装：

```bash
cd D:\agent_litkb
call agent\Scripts\activate.bat
pip install -r requirements.txt
```

### 2) 启动 vLLM（可选但推荐）

双击或执行：

```bash
D:\agent_litkb\start_vllm.bat
```

默认地址为 `http://127.0.0.1:8000/v1`（可在 `backend/config.py` 修改 `VLLM_API_BASE` / `LLM_MODEL_NAME`）。

> 若不启动 vLLM：文献结构化解析与问答会受影响（后端会返回错误信息）。

### 3) 启动后端（FastAPI）

```bash
D:\agent_litkb\start_backend.bat
```

后端默认监听：`http://127.0.0.1:9000`  
健康检查：打开 `http://127.0.0.1:9000/` 可看到后端运行信息（含 `api_prefix=/api`）。

### 4) 启动前端（FigmaUI）

首次启动先安装依赖：

```bash
cd D:\agent_litkb\figmaUI
npm install
```

启动：

```bash
D:\agent_litkb\start_figma_ui.bat
```

访问：`http://127.0.0.1:5173`

前端默认后端 API：`http://127.0.0.1:9000/api`。  
如需改为其他机器/端口，建议用环境变量：

```bash
set VITE_API_BASE_URL=http://127.0.0.1:9000/api
```

或在 `figmaUI/.env` 中配置（推荐）。

### 5)（可选）启动旧版 Gradio UI

```bash
D:\agent_litkb\start_webui.bat
```

默认：`http://127.0.0.1:7860`

---

## 功能说明（FigmaUI）

### 登录与权限

- 默认管理员：`admin / admin123`
- 普通用户仅能看到自己上传的私有文献与共享文献；管理员可见全库并可进入后台。

### 文献上传（支持批量）

- 路由：`/documents/upload`
- 支持：PDF / TXT / DOCX / XLSX
- 支持 Shift 多选（批量上传），返回每个文件的成功/失败明细

后端接口：
- `POST /api/documents/upload`：单文件上传并入库 RAG
- `POST /api/documents/upload/batch`：批量上传（支持部分成功、可选失败回滚）

### 文献管理与详情页（三栏）

- 列表：`/documents`（点击行进入详情）
- 详情：`/documents/:documentId`
  - 左侧：原文预览/提取文本
  - 右上：RAG 切片列表（可搜索）
  - 右下：结构化解析（20条），未生成则显示“正在解析中...”

后端接口：
- `GET /api/documents` / `GET /api/documents/{id}`
- `GET /api/documents/{id}/file`：用于预览（**不会强制下载**）
- `GET /api/documents/{id}/text`
- `GET /api/documents/{id}/chunks`
- `GET /api/documents/{id}/analysis`

### 文献问答（流式）

- 路由：`/`（Research Copilot）
- 后端：`POST /api/chat/stream?conversation_id=...`（SSE 风格流式）
- 前端体验：在模型开始输出前显示“模型正在思考…”，并支持流式展示回复。

### 学生工作区

- 路由：`/workspace`
- 学生可创建自己的写作稿件，保存与导师/AI 互动（后端保存至 `data/student_papers/`）。

### 管理员后台

- 路由：`/admin`（仅管理员可见）
- 能力：账号管理、仪表盘统计、历史记录审计与清理等。

---

## 配置（后端）

配置文件：`backend/config.py`

- **API 前缀**：`API_V1_PREFIX`（默认 `/api`）
- **数据目录**：`data/`（SQLite、Chroma、uploads、papers）
- **RAG 分块**：`CHUNK_SIZE` / `CHUNK_OVERLAP` / `TOP_K`
- **vLLM**：`VLLM_API_BASE` / `LLM_MODEL_NAME`
- **历史**：`HISTORY_RETENTION_DAYS`
- **默认管理员**：`DEFAULT_ADMIN_USERNAME` / `DEFAULT_ADMIN_PASSWORD`

修改配置后重启后端生效。

---

## 部署建议（内网 / 半生产）

当前仓库默认以开发方式运行（前端 Vite dev server + 后端 FastAPI）。如果用于实验室内网长期运行，建议：

- 前端构建静态文件：在 `figmaUI/` 执行 `npm run build`
- 用 Nginx/Apache 或任意静态服务器托管 `figmaUI/dist/`
- 后端使用 `uvicorn` 以固定端口启动，并在反向代理层做 HTTPS/鉴权策略
- 数据备份：定期备份 `data/app.db` 与 `data/chroma/`（建议直接备份整个 `data/`）

---

## 常见问题

### 显存不足 / 模型太大

- 可使用更小/量化模型（例如 distill/7B/awq），并同步调整 `backend/config.py` 的 `LLM_MODEL_NAME` 与 vLLM 启动参数。

### 并发与性能

- 向量化与结构化解析是重计算：默认批量上传采用**串行**策略以避免机器卡死。
- 如果要提升吞吐，可后续引入任务队列（Celery/RQ）与异步后台任务，并给前端提供任务进度接口。


