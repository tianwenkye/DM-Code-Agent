# DM-Code-Agent Web 应用

基于 Vue 3 和 FastAPI 的 DM-Code-Agent 聊天 Web 界面。

## 功能特性

- 🎨 现代化聊天界面
- 🔄 实时显示 Agent 执行步骤
- 💬 支持多轮对话
- 🎯 支持多种 LLM 提供商（DeepSeek、OpenAI、Claude、Gemini、GLM）
- 📡 SSE 实时推送执行状态
- ⚙️ 可配置模型参数

## 快速开始

### 1. 安装依赖

```bash
./install.sh
```

或手动安装：

```bash
pip install -r requirements.txt
cd frontend
npm install
cd ..
```

### 2. 配置环境变量

确保 `.env` 文件中配置了相应的 API 密钥：

```env
DEEPSEEK_API_KEY=your_deepseek_key
OPENAI_API_KEY=your_openai_key
CLAUDE_API_KEY=your_claude_key
GEMINI_API_KEY=your_gemini_key
GLM_API_KEY=your_glm_key
```

### 3. 启动服务

#### 方式一：分别启动

**后端：**
```bash
uvicorn backend.main:app --reload --port 8000
```

**前端：**
```bash
cd frontend
npm run dev
```

#### 方式二：使用 tmux 同时启动

```bash
./start-all.sh
```

### 4. 访问应用

- 前端界面：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 项目结构

```
DM-Code-Agent/
├── backend/                    # FastAPI 后端
│   ├── __init__.py
│   ├── main.py                 # FastAPI 应用入口
│   ├── agent_service.py        # Agent 服务封装
│   └── models.py               # Pydantic 数据模型
├── frontend/                   # Vue 3 前端
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── src/
│       ├── main.ts
│       ├── types.ts
│       ├── App.vue
│       └── components/
│           └── ChatMessage.vue
├── install.sh                  # 安装脚本
└── start-all.sh              # 启动脚本
```

## API 端点

### POST /api/chat
创建聊天会话并执行任务

**请求体：**
```json
{
  "message": "用户消息",
  "provider": "deepseek",
  "model": "deepseek-chat",
  "base_url": "https://api.deepseek.com",
  "max_steps": 100,
  "temperature": 0.7
}
```

**响应：**
```json
{
  "session_id": "uuid",
  "message": "任务已开始执行",
  "status": "running"
}
```

### GET /api/chat/{session_id}/stream
流式获取执行步骤（SSE）

### DELETE /api/chat/{session_id}
删除聊天会话

### POST /api/chat/{session_id}/reset
重置会话历史

### GET /api/health
健康检查

## 技术栈

### 后端
- FastAPI
- uvicorn
- sse-starlette
- pydantic

### 前端
- Vue 3
- TypeScript
- Vite
- Axios

## 开发说明

### 后端开发

后端服务使用 FastAPI，支持热重载：

```bash
uvicorn backend.main:app --reload --port 8000
```

### 前端开发

前端使用 Vite 开发服务器：

```bash
cd frontend
npm run dev
```

构建生产版本：

```bash
cd frontend
npm run build
```

## 注意事项

1. 确保 `.env` 文件中配置了正确的 API 密钥
2. 后端默认运行在 8000 端口
3. 前端默认运行在 3000 端口
4. 使用 SSE 进行实时通信，需要保持连接稳定
5. 会话数据存储在内存中，重启后会丢失

## 许可证

MIT License
