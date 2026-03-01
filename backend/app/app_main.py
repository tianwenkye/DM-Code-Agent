"""FastAPI 后端服务"""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .service.agent_service import get_agent_service
from .router import chat_router, user_router, history_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    agent_service = get_agent_service()
    await agent_service.initialize()
    yield
    await agent_service.cleanup()


app = FastAPI(
    title="DM-Code-Agent API",
    description="基于 ReAct 智能体的聊天 API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(user_router)
app.include_router(history_router)


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
