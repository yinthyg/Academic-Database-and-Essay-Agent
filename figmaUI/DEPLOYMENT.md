# 部署指南

## 本地开发

### 前置要求
- Node.js 18+ 或 20+
- pnpm 或 npm
- 后端API服务运行在 `http://127.0.0.1:9000`

### 启动步骤

1. **安装依赖**
```bash
npm install
# 或
pnpm install
```

2. **启动开发服务器**
```bash
npm run dev
# 或
pnpm dev
```

3. **访问应用**
打开浏览器访问：`http://localhost:5173`

4. **登录**
- 用户名：`admin`
- 密码：`admin123`

## 生产环境构建

### 1. 构建生产版本

```bash
npm run build
```

构建产物会生成在 `dist/` 目录。

### 2. 预览构建结果

```bash
npx vite preview
```

## 部署选项

### 选项 1: 静态网站托管

#### Vercel
```bash
# 安装 Vercel CLI
npm i -g vercel

# 部署
vercel
```

在 `vercel.json` 中配置：
```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/" }]
}
```

#### Netlify
```bash
# 安装 Netlify CLI
npm i -g netlify-cli

# 部署
netlify deploy --prod
```

在 `netlify.toml` 中配置：
```toml
[build]
  command = "npm run build"
  publish = "dist"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

#### GitHub Pages

1. 修改 `vite.config.ts` 添加 base：
```typescript
export default {
  base: '/your-repo-name/',
  // ...
}
```

2. 使用 GitHub Actions 自动部署：
```yaml
# .github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-node@v3
        with:
          node-version: 18
      - run: npm install
      - run: npm run build
      - uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./dist
```

### 选项 2: Docker部署

创建 `Dockerfile`：
```dockerfile
# Build stage
FROM node:18-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

创建 `nginx.conf`：
```nginx
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # API代理（可选）
    location /api {
        proxy_pass http://backend:9000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

构建和运行：
```bash
docker build -t research-copilot-frontend .
docker run -p 80:80 research-copilot-frontend
```

### 选项 3: 传统服务器部署

1. **构建**
```bash
npm run build
```

2. **上传dist目录到服务器**
```bash
scp -r dist/* user@server:/var/www/html/
```

3. **配置Nginx**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    root /var/www/html;
    index index.html;

    location / {
        try_files $uri $uri/ /index.html;
    }

    # Gzip压缩
    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
}
```

4. **重启Nginx**
```bash
sudo systemctl restart nginx
```

## 环境变量配置

### 开发环境
创建 `.env.development`：
```env
VITE_API_BASE_URL=http://127.0.0.1:9000/api
```

### 生产环境
创建 `.env.production`：
```env
VITE_API_BASE_URL=https://api.yourdomain.com/api
```

在代码中使用：
```typescript
const API_BASE = import.meta.env.VITE_API_BASE_URL;
```

## 性能优化

### 1. 代码分割
Vite 自动进行代码分割，无需额外配置。

### 2. 资源压缩
在 `vite.config.ts` 中启用：
```typescript
export default {
  build: {
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
      },
    },
  },
}
```

### 3. CDN加速
使用 CDN 托管静态资源：
```typescript
export default {
  build: {
    rollupOptions: {
      external: ['react', 'react-dom'],
      output: {
        paths: {
          react: 'https://cdn.jsdelivr.net/npm/react@18/umd/react.production.min.js',
          'react-dom': 'https://cdn.jsdelivr.net/npm/react-dom@18/umd/react-dom.production.min.js',
        },
      },
    },
  },
}
```

### 4. 图片优化
- 使用 WebP 格式
- 启用图片懒加载
- 压缩图片资源

## SSL/HTTPS配置

### Let's Encrypt (免费)
```bash
# 安装 certbot
sudo apt-get install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

Nginx配置自动更新为：
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # ... 其他配置
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

## 监控和日志

### 1. 错误监控
集成 Sentry：
```bash
npm install @sentry/react
```

```typescript
import * as Sentry from "@sentry/react";

Sentry.init({
  dsn: "your-sentry-dsn",
  environment: import.meta.env.MODE,
});
```

### 2. 访问统计
集成 Google Analytics 或其他分析工具。

### 3. 性能监控
使用 Web Vitals：
```bash
npm install web-vitals
```

## Docker Compose完整示例

创建 `docker-compose.yml`：
```yaml
version: '3.8'

services:
  frontend:
    build: .
    ports:
      - "80:80"
    environment:
      - VITE_API_BASE_URL=http://backend:9000/api
    depends_on:
      - backend

  backend:
    image: your-backend-image
    ports:
      - "9000:9000"
    environment:
      - DATABASE_URL=postgresql://...
```

运行：
```bash
docker-compose up -d
```

## 回滚策略

### 使用Git标签
```bash
# 标记当前版本
git tag v1.0.0

# 回滚到之前版本
git checkout v0.9.0
npm run build
# 重新部署
```

### 使用备份
保留多个版本的构建产物：
```bash
# 备份当前版本
cp -r dist dist-backup-$(date +%Y%m%d)

# 回滚
rm -rf dist
cp -r dist-backup-20240315 dist
```

## 健康检查

### 前端健康检查
创建 `public/health` 文件：
```json
{"status":"ok"}
```

### Nginx健康检查
```nginx
location /health {
    access_log off;
    return 200 "healthy\n";
}
```

## 故障排查

### 1. 白屏问题
- 检查控制台错误
- 确认API地址配置正确
- 检查路由配置

### 2. API请求失败
- 检查CORS配置
- 验证token是否有效
- 确认后端服务正常

### 3. 静态资源404
- 检查base配置
- 确认路由重写规则
- 验证文件路径

### 4. 性能问题
- 开启Gzip压缩
- 使用CDN
- 优化图片资源
- 启用缓存策略

## 备份和恢复

### 备份
```bash
# 备份代码
git archive -o backup.zip HEAD

# 备份配置
tar -czf config-backup.tar.gz .env* nginx.conf
```

### 恢复
```bash
# 恢复代码
unzip backup.zip -d restore-dir

# 恢复配置
tar -xzf config-backup.tar.gz
```

## 持续集成/持续部署 (CI/CD)

### GitHub Actions示例
```yaml
name: CI/CD

on:
  push:
    branches: [main]

jobs:
  build-and-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18
      
      - name: Install dependencies
        run: npm install
      
      - name: Run tests
        run: npm test
      
      - name: Build
        run: npm run build
        env:
          VITE_API_BASE_URL: ${{ secrets.API_BASE_URL }}
      
      - name: Deploy to server
        uses: easingthemes/ssh-deploy@v2
        with:
          SSH_PRIVATE_KEY: ${{ secrets.SSH_PRIVATE_KEY }}
          REMOTE_HOST: ${{ secrets.REMOTE_HOST }}
          REMOTE_USER: ${{ secrets.REMOTE_USER }}
          TARGET: /var/www/html
          SOURCE: dist/
```

## 安全检查清单

- [ ] HTTPS已启用
- [ ] API地址使用环境变量
- [ ] 移除console.log（生产环境）
- [ ] 启用Content Security Policy
- [ ] 设置安全响应头
- [ ] Token安全存储
- [ ] 定期更新依赖包

## 性能检查清单

- [ ] Lighthouse评分 > 90
- [ ] 首屏加载时间 < 3秒
- [ ] 代码分割已启用
- [ ] Gzip压缩已启用
- [ ] 图片已优化
- [ ] CDN已配置

## 支持的浏览器

- Chrome/Edge: 最新版本
- Firefox: 最新版本
- Safari: 最新版本
- 移动浏览器: iOS Safari, Chrome Mobile

## 许可

本项目部署指南仅供参考，实际部署请根据具体环境调整。
