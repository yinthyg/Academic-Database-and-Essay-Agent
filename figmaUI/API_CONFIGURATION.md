# API配置指南

## 快速配置

### 1. 修改API地址

在 `/src/app/lib/api.ts` 文件的第3行修改后端地址：

```typescript
const API_BASE = "http://127.0.0.1:9000/api";
```

如果您的后端部署在其他地址，请修改为对应的URL，例如：
- 本地开发：`http://localhost:9000/api`
- 生产环境：`https://api.yourdomain.com/api`

### 2. CORS配置

确保后端服务器允许前端域名的跨域请求。在FastAPI中添加：

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],  # 前端地址
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## API端点映射

| 前端功能 | API端点 | 方法 | 说明 |
|---------|---------|------|------|
| **认证** |
| 登录 | `/auth/token` | POST | 表单数据：username, password |
| 获取用户信息 | `/auth/me` | GET | 需要Bearer Token |
| **会话系统** |
| 获取会话列表 | `/conversations` | GET | 返回所有会话 |
| 创建会话 | `/conversations` | POST | JSON: {title?, collection_id?, student_paper_id?} |
| 获取消息 | `/conversations/{id}/messages` | GET | 查询参数：limit |
| 发送消息 | `/conversations/{id}/messages` | POST | JSON: {role, content, sources?} |
| 流式聊天 | `/chat/stream` | POST | 查询参数：conversation_id，返回SSE |
| **论文管理** |
| 获取论文列表 | `/papers` | GET | 返回所有论文 |
| 获取论文详情 | `/papers/{id}/profile` | GET | 返回结构化信息 |
| 获取论文笔记 | `/papers/{id}/notes` | GET | 返回笔记内容 |
| 保存论文笔记 | `/papers/{id}/notes` | POST | 查询参数：content |
| 论文对话 | `/papers/chat` | POST | JSON: {paper_id, question} |
| 多论文对比 | `/papers/compare` | POST | JSON: {paper_ids[], question} |
| **学生论文** |
| 获取论文列表 | `/student_papers` | GET | 返回用户的所有论文 |
| 创建论文 | `/student_papers/create` | POST | JSON: {title} |
| 获取论文详情 | `/student_papers/{id}` | GET | 返回title和content |
| 保存论文 | `/student_papers/{id}/save` | POST | JSON: {content} |
| AI导师对话 | `/student_papers/{id}/mentor_chat` | POST | JSON: {question} |
| **文献管理** |
| 获取文献列表 | `/documents` | GET | 返回可见文献 |
| 上传文献 | `/documents/upload` | POST | 表单数据：file, is_private, group_id? |
| 删除文献 | `/documents/{id}` | DELETE | 删除指定文献 |
| **RAG问答** |
| RAG查询 | `/rag/query` | POST | JSON: {question, scope, group_ids?} |
| 文献对比 | `/rag/compare` | POST | JSON: {question, document_ids[]} |

## 请求示例

### 1. 登录
```typescript
const formData = new FormData();
formData.append("username", "admin");
formData.append("password", "admin123");

const response = await fetch("http://127.0.0.1:9000/api/auth/token", {
  method: "POST",
  body: formData,
});

const data = await response.json();
// 返回: { access_token: "...", token_type: "bearer" }
```

### 2. 获取会话列表
```typescript
const response = await fetch("http://127.0.0.1:9000/api/conversations", {
  headers: {
    Authorization: `Bearer ${token}`,
  },
});

const conversations = await response.json();
```

### 3. 创建会话
```typescript
const response = await fetch("http://127.0.0.1:9000/api/conversations", {
  method: "POST",
  headers: {
    Authorization: `Bearer ${token}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    title: "Deep Learning Research",
  }),
});

const newConversation = await response.json();
```

### 4. 流式聊天
```typescript
const response = await fetch(
  "http://127.0.0.1:9000/api/chat/stream?conversation_id=1",
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  }
);

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split("\n");

  for (const line of lines) {
    if (line.startsWith("data:")) {
      const content = line.slice(5).trim();
      if (content === "[END]") {
        // 流结束
      } else {
        // 显示内容
        console.log(content);
      }
    }
  }
}
```

### 5. AI导师对话
```typescript
const response = await fetch(
  "http://127.0.0.1:9000/api/student_papers/1/mentor_chat",
  {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      question: "Can you suggest citations for my paper?",
    }),
  }
);

const data = await response.json();
// 返回: { answer: "...", citations: ["...", "..."] }
```

## 响应格式

### 成功响应
大多数端点返回JSON格式的数据。具体格式请参考后端API文档。

### 错误响应
```json
{
  "detail": "错误描述信息"
}
```

HTTP状态码：
- 200: 成功
- 401: 未认证
- 403: 无权限
- 404: 资源不存在
- 422: 验证错误
- 500: 服务器错误

## SSE流式响应格式

流式聊天使用Server-Sent Events (SSE)协议：

```
data: Hello
data: world
data: !
data: [END]
```

前端解析：
1. 读取响应流
2. 按行分割
3. 提取 `data:` 后的内容
4. 遇到 `[END]` 停止

## 环境变量（可选）

如果需要支持多环境配置，可以创建 `.env` 文件：

```env
VITE_API_BASE_URL=http://127.0.0.1:9000/api
```

然后在代码中使用：
```typescript
const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:9000/api";
```

## 调试技巧

### 1. 开启网络日志
在浏览器开发者工具的Network标签查看所有API请求。

### 2. 添加拦截器
在 `api.ts` 中添加统一的请求/响应拦截：

```typescript
async function fetchWithInterceptor(url: string, options: RequestInit) {
  console.log(`[API] ${options.method || 'GET'} ${url}`);
  
  const response = await fetch(url, options);
  
  console.log(`[API] Response: ${response.status}`);
  
  return response;
}
```

### 3. 错误追踪
所有API调用都包含 try-catch 错误处理，错误会显示在UI中。

## 性能优化

### 1. 请求缓存
对于不常变化的数据（如论文列表），可以添加本地缓存。

### 2. 请求去重
防止重复请求同一资源。

### 3. 连接池
浏览器会自动管理HTTP连接池，无需特殊配置。

## 安全注意事项

1. **Token存储**：当前使用localStorage，生产环境建议使用httpOnly cookie
2. **HTTPS**：生产环境必须使用HTTPS
3. **Token刷新**：实现token自动刷新机制
4. **输入验证**：所有用户输入都需要验证

## 后端要求

确保后端实现以下功能：

1. ✅ JWT Token认证
2. ✅ CORS跨域支持
3. ✅ SSE流式输出
4. ✅ 文件上传
5. ✅ 权限控制
6. ✅ 错误统一返回格式

## 常见问题

### Q: 跨域错误
A: 检查后端CORS配置，允许前端域名

### Q: Token过期
A: 重新登录获取新token，或实现自动刷新

### Q: SSE不工作
A: 检查后端是否正确设置Content-Type为text/event-stream

### Q: 上传文件失败
A: 检查文件大小限制和后端配置
