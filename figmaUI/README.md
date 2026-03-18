# Research Copilot - AI研究助手系统

这是一个专业的AI科研助手前端系统，对接您的后端API，提供研究对话、论文管理和写作辅助功能。

## 🌟 主要功能

### 1. Research Copilot（研究对话助手）
- **会话管理**：创建和管理多个研究会话
- **智能对话**：基于RAG的问答系统，支持流式输出
- **引用追踪**：自动显示答案来源和文献引用
- **论文浏览器**：
  - 浏览所有已索引的论文
  - 查看结构化信息（Abstract、Method、Experiment、Conclusion）
  - JSON格式查看

### 2. Student Workspace（学生论文工作区）
- **论文编辑器**：
  - Markdown格式编辑
  - 自动保存功能
  - 实时字数统计
  - 章节快速导航
- **AI导师**：
  - 写作反馈
  - 引用建议
  - 实验方法建议
  - 快捷操作按钮

## 🎨 设计特点

- **简约大气**：科研风格的专业UI设计
- **三栏布局**：类似VSCode + Notion + ChatGPT的综合体验
- **流式输出**：实时打字机效果，提升交互体验
- **清晰的信息层次**：区分建议、引用、来源等不同类型的内容

## 📡 后端API对接

### 认证
- `POST /api/auth/token` - 登录
- `GET /api/auth/me` - 获取用户信息

### 文献管理
- `GET /api/documents` - 获取文献列表
- `POST /api/documents/upload` - 上传文献
- `DELETE /api/documents/{id}` - 删除文献

### RAG问答
- `POST /api/rag/query` - RAG问答
- `POST /api/rag/compare` - 文献对比

### 论文工作区
- `GET /api/papers` - 获取论文列表
- `GET /api/papers/{id}/profile` - 获取论文结构化信息
- `GET /api/papers/{id}/notes` - 获取论文笔记
- `POST /api/papers/{id}/notes` - 保存论文笔记
- `POST /api/papers/chat` - 论文对话
- `POST /api/papers/compare` - 多论文对比

### 学生论文
- `GET /api/student_papers` - 获取学生论文列表
- `POST /api/student_papers/create` - 创建论文
- `GET /api/student_papers/{id}` - 获取论文详情
- `POST /api/student_papers/{id}/save` - 保存论文
- `POST /api/student_papers/{id}/mentor_chat` - AI导师对话

### 会话系统
- `GET /api/conversations` - 获取会话列表
- `POST /api/conversations` - 创建会话
- `GET /api/conversations/{id}/messages` - 获取消息
- `POST /api/conversations/{id}/messages` - 发送消息
- `POST /api/chat/stream` - 流式聊天（SSE）

## 🚀 使用说明

### 1. 配置后端地址
在 `/src/app/lib/api.ts` 文件中修改 API 地址：
```typescript
const API_BASE = "http://127.0.0.1:9000/api";
```

### 2. 登录
- 默认用户名：`admin`
- 默认密码：`admin123`

### 3. Research Copilot使用流程
1. 点击 "New Conversation" 创建新会话
2. 在聊天区域输入问题
3. 查看AI回答和引用来源
4. 在右侧面板浏览论文详情

### 4. Student Workspace使用流程
1. 点击 "New Paper" 创建新论文
2. 在编辑器中书写内容（支持Markdown）
3. 系统自动保存
4. 在右侧AI导师获取写作建议和引用推荐

## 🔧 技术栈

- **React 18** - UI框架
- **React Router 7** - 路由管理
- **Tailwind CSS v4** - 样式系统
- **Radix UI** - UI组件库
- **TypeScript** - 类型安全
- **Fetch API** - HTTP请求
- **Server-Sent Events (SSE)** - 流式数据传输

## 📁 项目结构

```
src/
├── app/
│   ├── lib/
│   │   ├── api.ts              # API客户端
│   │   └── auth-context.tsx    # 认证上下文
│   ├── pages/
│   │   ├── login.tsx           # 登录页面
│   │   ├── research-copilot.tsx  # 研究助手页面
│   │   └── student-workspace.tsx # 论文工作区页面
│   ├── components/
│   │   ├── conversations-sidebar-new.tsx  # 会话侧边栏
│   │   ├── chat-area-new.tsx              # 聊天区域
│   │   ├── paper-explorer-new.tsx         # 论文浏览器
│   │   ├── student-papers-sidebar-new.tsx # 论文列表侧边栏
│   │   ├── paper-editor-new.tsx           # 论文编辑器
│   │   ├── ai-mentor-new.tsx              # AI导师
│   │   └── ui/                            # UI组件库
│   ├── App.tsx              # 应用入口
│   └── routes.tsx           # 路由配置
└── styles/                  # 样式文件
```

## 🔐 认证机制

系统使用 Bearer Token 认证：
- 登录后 token 存储在 localStorage
- 所有 API 请求自动携带 Authorization header
- 未登录自动跳转到登录页面
- 支持退出登录功能

## 💡 特色功能

### 1. 流式聊天
使用 Server-Sent Events (SSE) 实现实时打字机效果，提升用户体验。

### 2. 自动保存
论文编辑器在停止输入2秒后自动保存，防止内容丢失。

### 3. 智能引用
AI导师可以根据论文内容推荐相关引用，并可一键插入（后端支持）。

### 4. 会话记忆
每个会话保持完整的对话历史，支持多轮对话。

### 5. 结构化信息
论文信息以结构化方式展示，支持JSON视图和格式化视图切换。

## 🎯 开发指南

### API错误处理
所有API调用都包含错误处理，错误信息会显示在UI中。

### 状态管理
使用 React Context 管理全局认证状态，组件内部使用 useState 管理本地状态。

### 类型安全
所有API接口都有完整的TypeScript类型定义，确保类型安全。

## 📝 注意事项

1. 确保后端API服务已启动在 `http://127.0.0.1:9000`
2. CORS配置：后端需要允许前端域名的跨域请求
3. 流式API：确保后端正确实现SSE协议
4. Token有效期：根据后端配置，token可能会过期，需要重新登录

## 🐛 常见问题

### Q: 登录失败
A: 检查后端服务是否运行，用户名密码是否正确

### Q: 无法加载数据
A: 检查token是否有效，网络请求是否正常

### Q: 流式输出不工作
A: 检查后端SSE接口是否正确实现

### Q: 自动保存失败
A: 查看控制台错误信息，检查网络连接

## 📄 许可

本项目仅供学习和研究使用。
