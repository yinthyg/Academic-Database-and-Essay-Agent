# 快速开始指南

## 5分钟上手 Research Copilot

### 第一步：启动后端服务

确保您的后端API服务已经运行：
```bash
# 假设您的后端在这个地址
http://127.0.0.1:9000
```

### 第二步：安装前端依赖

```bash
npm install
```

### 第三步：启动前端开发服务器

```bash
npm run dev
```

浏览器自动打开 `http://localhost:5173`

### 第四步：登录

使用默认账户登录：
- **用户名**: `admin`
- **密码**: `admin123`

## 核心功能演示

### 功能1：Research Copilot - 研究对话

#### 1.1 创建会话
1. 登录后自动进入 Research Copilot 页面
2. 点击左侧 "New Conversation" 按钮
3. 输入会话标题（可选）
4. 点击 "Create"

#### 1.2 开始对话
1. 在中间的聊天区域输入问题，例如：
   ```
   Can you explain transformer architectures?
   ```
2. 按 Enter 发送
3. 观察AI的流式回答和引用来源

#### 1.3 浏览论文
1. 在右侧 Paper Explorer 中浏览论文列表
2. 点击任一论文查看详情
3. 切换 "Structured" 和 "JSON" 视图
4. 点击 "Back to list" 返回列表

### 功能2：Student Workspace - 论文写作

#### 2.1 切换到写作工作区
点击左侧 "Student Workspace" 按钮

#### 2.2 创建论文
1. 点击左侧 "New Paper" 按钮
2. 输入论文标题，例如：
   ```
   A Survey on Transformer Architectures in NLP
   ```
3. 点击 "Create"

#### 2.3 开始写作
1. 在中间编辑器中输入内容
2. 支持 Markdown 格式
3. 系统自动保存（2秒后）
4. 实时显示字数统计

示例内容：
```markdown
# A Survey on Transformer Architectures in NLP

## Abstract

This paper presents a comprehensive survey of transformer 
architectures and their applications in natural language 
processing.

## 1. Introduction

Transformers have revolutionized NLP since their introduction 
in 2017...

## 2. Background

### 2.1 Attention Mechanism
...
```

#### 2.4 使用AI导师
1. 在右侧 AI Mentor 面板输入问题：
   ```
   Can you suggest citations for transformer papers?
   ```
2. 或点击快捷按钮：
   - "Review Section" - 审查章节
   - "Find Citations" - 查找引用
   - "Improve Writing" - 改进写作

3. AI导师会提供：
   - 写作建议
   - 相关引用
   - 实验方法建议

## 常用快捷键

### 聊天区域
- `Enter` - 发送消息
- `Shift + Enter` - 换行

### 编辑器
- `Ctrl/Cmd + S` - 手动保存（自动保存已启用）
- `Ctrl/Cmd + F` - 查找文本

## API配置（如需修改）

如果后端地址不是 `http://127.0.0.1:9000`，请修改：

**文件**: `/src/app/lib/api.ts`
**第3行**:
```typescript
const API_BASE = "http://your-backend-address:port/api";
```

## 数据流程图

### Research Copilot流程
```
用户登录 → 创建会话 → 发送问题 → 后端RAG处理 
→ 流式返回答案 → 显示引用来源 → 浏览论文详情
```

### Student Workspace流程
```
用户登录 → 创建论文 → 编辑内容 → 自动保存 
→ 询问AI导师 → 获取建议和引用 → 继续写作
```

## 功能对应的后端API

| 功能 | API端点 |
|------|---------|
| 登录 | `POST /api/auth/token` |
| 创建会话 | `POST /api/conversations` |
| 发送消息 | `POST /api/conversations/{id}/messages` |
| 流式聊天 | `POST /api/chat/stream` |
| 获取论文列表 | `GET /api/papers` |
| 获取论文详情 | `GET /api/papers/{id}/profile` |
| 创建学生论文 | `POST /api/student_papers/create` |
| 保存论文内容 | `POST /api/student_papers/{id}/save` |
| AI导师对话 | `POST /api/student_papers/{id}/mentor_chat` |

## 测试数据准备

### 1. 上传文献（使用后端提供的接口）
```bash
curl -X POST "http://127.0.0.1:9000/api/documents/upload" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@paper.pdf" \
  -F "is_private=false"
```

### 2. 创建论文索引
后端会自动为上传的文献创建论文索引。

### 3. 测试对话
在 Research Copilot 中问：
```
What are the main contributions of this paper?
Can you compare the methods used in different papers?
Suggest related work for my research on transformers
```

## 常见使用场景

### 场景1：文献调研
1. 上传多篇相关论文
2. 创建会话询问：
   - "总结这些论文的核心观点"
   - "对比不同方法的优缺点"
   - "找出研究空白"

### 场景2：论文写作
1. 创建新论文
2. 边写边问AI导师：
   - "如何改进这段文字？"
   - "需要引用哪些重要论文？"
   - "实验设计是否合理？"

### 场景3：文献笔记
1. 在 Paper Explorer 查看论文详情
2. 复制重要信息
3. 在 Student Paper 中整理笔记

## 性能提示

### 优化加载速度
- 首次加载会稍慢，请耐心等待
- 后续切换页面会很快（已缓存）
- 流式输出会实时显示，无需等待完整响应

### 节省流量
- 论文列表会缓存，避免重复请求
- 消息历史按需加载
- 自动保存会批量处理请求

## 故障排除

### 问题1：无法登录
**解决方案**：
1. 检查后端服务是否运行
2. 确认用户名密码正确
3. 查看浏览器控制台错误信息

### 问题2：消息发送失败
**解决方案**：
1. 检查网络连接
2. 确认token未过期（重新登录）
3. 查看后端日志

### 问题3：论文列表为空
**解决方案**：
1. 确认已上传文献
2. 检查权限设置
3. 刷新页面

### 问题4：自动保存不工作
**解决方案**：
1. 检查网络连接
2. 查看保存状态提示
3. 手动点击保存（如有）

## 下一步

- 📖 阅读完整 [README.md](./README.md) 了解所有功能
- 🔧 查看 [API_CONFIGURATION.md](./API_CONFIGURATION.md) 配置API
- 🚀 参考 [DEPLOYMENT.md](./DEPLOYMENT.md) 部署到生产环境

## 获取帮助

如遇到问题：
1. 查看浏览器控制台（F12）的错误信息
2. 检查后端日志
3. 参考文档中的故障排除部分

## 示例工作流程

### 完整工作流：从文献调研到论文完成

**第一天：文献上传和调研**
1. 登录系统
2. 上传10篇相关论文（通过后端API）
3. 创建会话 "Transformer Survey Research"
4. 询问：
   - "总结所有论文的核心贡献"
   - "找出最常用的方法"
   - "识别研究趋势"

**第二天：论文框架**
1. 切换到 Student Workspace
2. 创建论文 "A Survey on Transformer Architectures"
3. 写入框架：
   ```markdown
   # Abstract
   # 1. Introduction
   # 2. Background
   # 3. Methods
   # 4. Applications
   # 5. Future Directions
   # 6. Conclusion
   ```
4. 询问AI导师："这个框架合理吗？"

**第三天：内容填充**
1. 逐章节填写内容
2. 每写完一节，询问AI导师
3. 获取引用建议并插入
4. 系统自动保存进度

**第四天：完善和引用**
1. 在 Research Copilot 询问更多细节
2. 补充引用
3. 使用AI导师改进文字表达
4. 最终审阅

**第五天：导出和提交**
1. 复制最终内容
2. 下载或导出
3. 提交论文

## 提示和技巧

### 写出更好的问题
❌ 不好的问题：
```
transformer
tell me about papers
```

✅ 好的问题：
```
What are the key innovations in transformer architectures 
compared to RNN-based models?

Can you compare BERT and GPT in terms of training objectives 
and architecture?
```

### 高效使用AI导师
- 具体说明需要什么帮助
- 提供上下文信息
- 一次问一个清晰的问题
- 利用快捷按钮快速操作

### 组织论文内容
- 使用Markdown标题结构化内容
- 定期保存和备份
- 利用章节导航快速跳转
- 保持逻辑清晰的章节顺序

---

**恭喜！您已经掌握了 Research Copilot 的基本使用方法。开始您的研究之旅吧！** 🚀
