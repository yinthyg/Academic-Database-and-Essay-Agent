# Research Copilot - 项目总览

## 📋 项目简介

Research Copilot 是一个专业的AI驱动的科研助手系统，旨在帮助研究人员和学生更高效地进行文献调研、论文阅读和学术写作。

### 核心价值
- 🤖 **AI增强**：基于RAG技术的智能问答
- 📚 **文献管理**：结构化的论文信息展示
- ✍️ **写作辅助**：AI导师提供实时写作建议
- 💬 **对话记忆**：完整的会话历史管理
- 🔄 **流式体验**：实时打字机效果的回答

## 🏗️ 架构设计

### 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户浏览器                              │
│  ┌───────────────────────────────────────────────────┐  │
│  │              React 前端应用                         │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  │  │
│  │  │ Research    │  │  Student    │  │  Login   │  │  │
│  │  │ Copilot     │  │  Workspace  │  │  Page    │  │  │
│  │  └─────────────┘  └─────────────┘  └──────────┘  │  │
│  │         │                │                │        │  │
│  │         └────────────────┴────────────────┘        │  │
│  │                       │                            │  │
│  │              ┌────────▼────────┐                   │  │
│  │              │  API Client     │                   │  │
│  │              │  (api.ts)       │                   │  │
│  │              └────────┬────────┘                   │  │
│  └───────────────────────┼────────────────────────────┘  │
└────────────────────────────┼──────────────────────────────┘
                             │ HTTP/SSE
                             │ Bearer Token
┌────────────────────────────▼──────────────────────────────┐
│                    后端 API 服务器                          │
│  (FastAPI + PostgreSQL + Qdrant + OpenAI)                │
│  ┌────────────┐  ┌────────────┐  ┌───────────────┐      │
│  │   Auth     │  │    RAG     │  │  Student      │      │
│  │   Service  │  │   Engine   │  │  Papers       │      │
│  └────────────┘  └────────────┘  └───────────────┘      │
│  ┌────────────┐  ┌────────────┐  ┌───────────────┐      │
│  │   Papers   │  │ Conversations│  │  Documents  │      │
│  │   Service  │  │   Service   │  │   Service    │      │
│  └────────────┘  └────────────┘  └───────────────┘      │
└───────────────────────────────────────────────────────────┘
```

### 技术栈

#### 前端
- **框架**: React 18.3.1
- **路由**: React Router 7.13.0
- **样式**: Tailwind CSS v4.1.12
- **UI库**: Radix UI + shadcn/ui
- **语言**: TypeScript
- **构建**: Vite 6.3.5
- **状态管理**: React Context + Hooks

#### 后端（您的现有系统）
- **框架**: FastAPI
- **数据库**: PostgreSQL
- **向量数据库**: Qdrant
- **AI模型**: OpenAI API
- **认证**: JWT Token

### 数据流

#### 1. 认证流程
```
用户输入凭证 → POST /api/auth/token → 返回Token 
→ 存储到localStorage → 后续请求携带Token
```

#### 2. 研究对话流程
```
创建会话 → 发送问题 → 创建用户消息 
→ 调用流式API → SSE流式返回 → 实时显示
→ 加载完整消息历史
```

#### 3. 论文写作流程
```
创建论文 → 编辑内容 → 2秒延迟 → 自动保存
→ 询问AI导师 → 获取建议 → 继续写作
```

## 📁 项目结构

```
research-copilot-frontend/
├── src/
│   ├── app/
│   │   ├── lib/
│   │   │   ├── api.ts                 # API客户端（核心）
│   │   │   ├── auth-context.tsx       # 认证上下文
│   │   │   └── utils.ts               # 工具函数
│   │   ├── pages/
│   │   │   ├── login.tsx              # 登录页
│   │   │   ├── research-copilot.tsx   # 研究助手页
│   │   │   ├── student-workspace.tsx  # 论文工作区页
│   │   │   └── protected-route.tsx    # 路由保护
│   │   ├── components/
│   │   │   ├── conversations-sidebar-new.tsx  # 会话侧边栏
│   │   │   ├── chat-area-new.tsx              # 聊天区域
│   │   │   ├── paper-explorer-new.tsx         # 论文浏览器
│   │   │   ├── student-papers-sidebar-new.tsx # 论文列表
│   │   │   ├── paper-editor-new.tsx           # 论文编辑器
│   │   │   ├── ai-mentor-new.tsx              # AI导师
│   │   │   └── ui/                            # UI组件库
│   │   ├── App.tsx                    # 应用入口
│   │   └── routes.tsx                 # 路由配置
│   └── styles/
│       ├── index.css                  # 全局样式
│       ├── tailwind.css               # Tailwind配置
│       ├── theme.css                  # 主题变量
│       └── fonts.css                  # 字体导入
├── public/                            # 静态资源
├── docs/
│   ├── README.md                      # 项目说明
│   ├── QUICKSTART.md                  # 快速开始
│   ├── API_CONFIGURATION.md           # API配置
│   ├── DEPLOYMENT.md                  # 部署指南
│   ├── FEATURES.md                    # 功能清单
│   └── PROJECT_OVERVIEW.md            # 项目总览（本文档）
├── package.json                       # 依赖配置
├── vite.config.ts                     # Vite配置
├── tsconfig.json                      # TypeScript配置
└── postcss.config.mjs                 # PostCSS配置
```

## 🎨 设计理念

### UI/UX原则
1. **简约大气**：科研风格，专注内容
2. **清晰层次**：三栏布局，功能区分明确
3. **流畅交互**：实时反馈，加载状态明确
4. **专业配色**：蓝色（研究）+ 紫色（写作）

### 用户体验设计
- **一键操作**：快捷按钮减少输入
- **自动保存**：防止内容丢失
- **流式输出**：提升等待体验
- **智能提示**：空状态引导用户

## 🔌 API集成

### 端点总览
- **8个**认证相关端点
- **12个**会话和消息端点
- **10个**论文相关端点
- **6个**学生论文端点
- **4个**文献管理端点
- **2个**RAG问答端点

详见：[API_CONFIGURATION.md](./API_CONFIGURATION.md)

## 🚀 开发流程

### 环境准备
```bash
# 1. 克隆项目
git clone <repository-url>
cd research-copilot-frontend

# 2. 安装依赖
npm install

# 3. 配置API地址（如需要）
# 编辑 src/app/lib/api.ts

# 4. 启动开发服务器
npm run dev

# 5. 访问应用
# http://localhost:5173
```

### 开发规范
- **组件命名**：PascalCase
- **文件命名**：kebab-case
- **变量命名**：camelCase
- **类型定义**：使用interface
- **注释**：关键逻辑添加注释
- **格式化**：使用Prettier

### Git工作流
```bash
# 功能开发
git checkout -b feature/new-feature
# 开发和测试
git add .
git commit -m "feat: add new feature"
git push origin feature/new-feature
# 创建Pull Request
```

## 📊 性能指标

### 目标性能
- **首屏加载**: < 3秒
- **路由切换**: < 300ms
- **API响应**: < 1秒
- **流式输出**: 实时（<100ms延迟）
- **自动保存**: 2秒延迟

### 优化措施
- 代码分割（Vite自动）
- 懒加载组件
- 请求缓存
- 防抖/节流
- 虚拟滚动（待实现）

## 🔒 安全考虑

### 已实现
- ✅ Bearer Token认证
- ✅ 路由保护
- ✅ XSS防护（React默认）
- ✅ HTTPS支持（生产环境）

### 待加强
- [ ] CSRF防护
- [ ] Token自动刷新
- [ ] 输入验证增强
- [ ] 权限细化

## 🧪 测试策略

### 测试层次
1. **单元测试**：工具函数、组件
2. **集成测试**：页面流程
3. **E2E测试**：完整用户场景
4. **性能测试**：加载速度、响应时间

### 测试工具（计划）
- Vitest - 单元测试
- React Testing Library - 组件测试
- Playwright - E2E测试
- Lighthouse - 性能测试

## 📈 监控和分析

### 前端监控（可选）
- **错误监控**: Sentry
- **性能监控**: Web Vitals
- **用户分析**: Google Analytics
- **日志**: Console + 服务器日志

## 🔄 CI/CD流程

```
代码提交 → GitHub Actions 触发
  ↓
运行测试
  ↓
构建生产版本
  ↓
部署到服务器/CDN
  ↓
健康检查
  ↓
通知完成
```

## 📱 响应式设计

### 断点
- **Desktop**: 1024px+
- **Tablet**: 768px - 1023px
- **Mobile**: < 767px

### 适配策略
- 三栏布局 → 单栏布局（移动端）
- 侧边栏折叠
- 字体大小调整
- 触摸优化

## 🌍 国际化（计划）

### 支持语言
- 英语（默认）
- 中文（计划）

### 实现方案
- react-i18next
- 语言切换按钮
- 本地化日期/数字

## 🎯 用户画像

### 主要用户
1. **研究生**: 文献调研、论文写作
2. **科研人员**: 文献管理、研究助手
3. **教授/导师**: 指导学生、审阅论文
4. **本科生**: 学习写作、文献阅读

### 使用场景
1. 文献调研（每周）
2. 论文写作（每月）
3. 文献笔记（每天）
4. AI问答（随时）

## 💼 商业价值

### 核心优势
1. **效率提升**: 50%+ 文献调研时间节省
2. **质量保证**: AI辅助减少错误
3. **知识管理**: 结构化信息存储
4. **学习曲线**: 直观的UI，快速上手

### 应用领域
- 高校科研
- 企业研发
- 独立研究
- 学术写作

## 📝 更新日志

### Version 1.0.0 (2024-03-17)
**初始发布**
- ✅ 完整的认证系统
- ✅ Research Copilot功能
- ✅ Student Workspace功能
- ✅ 流式聊天支持
- ✅ 论文浏览器
- ✅ AI导师功能
- ✅ 完整文档

## 🛠️ 故障排查

### 常见问题

#### 1. 无法连接后端
**症状**: API请求失败，CORS错误
**解决**:
```bash
# 检查后端是否运行
curl http://127.0.0.1:9000/api/auth/me

# 检查CORS配置
# 确保后端允许前端域名
```

#### 2. Token过期
**症状**: 401错误，需要重新登录
**解决**: 重新登录获取新Token

#### 3. 流式输出不工作
**症状**: 消息不逐字显示
**解决**: 检查后端SSE实现

## 🎓 学习资源

### 相关技术文档
- [React官方文档](https://react.dev)
- [React Router文档](https://reactrouter.com)
- [Tailwind CSS文档](https://tailwindcss.com)
- [Radix UI文档](https://www.radix-ui.com)
- [FastAPI文档](https://fastapi.tiangolo.com)

### 推荐阅读
- 《Clean Code》- 代码质量
- 《Refactoring》- 代码重构
- 《The Pragmatic Programmer》- 编程实践

## 🤝 贡献指南

### 如何贡献
1. Fork项目
2. 创建功能分支
3. 提交代码
4. 发起Pull Request
5. 代码审查
6. 合并到主分支

### 贡献类型
- 🐛 Bug修复
- ✨ 新功能
- 📝 文档改进
- 🎨 UI优化
- ⚡ 性能优化

## 📞 联系方式

### 问题反馈
- GitHub Issues
- 电子邮件
- 项目文档

### 技术支持
- 查看文档
- 搜索Issues
- 提交新Issue

## 📄 许可证

本项目仅供学习和研究使用。

---

## 🎉 致谢

感谢所有贡献者和用户的支持！

**让研究更简单，让写作更高效！** 🚀

---

*最后更新: 2024-03-17*
*版本: 1.0.0*
*作者: Research Copilot Team*
