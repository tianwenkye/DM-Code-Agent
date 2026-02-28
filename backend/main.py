"""FastAPI 后端服务"""

from __future__ import annotations

import asyncio
import json
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse

from .agent_service import get_agent_service
from .models import ChatRequest, ChatResponse, ErrorResponse


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


@app.post("/api/chat", response_model=ChatResponse)
async def create_chat(request: ChatRequest, background_tasks: BackgroundTasks):
    """创建聊天会话并执行任务"""
    agent_service = get_agent_service()

    try:
        session_id = await agent_service.create_session(
            provider=request.provider,
            model=request.model,
            base_url=request.base_url,
            max_steps=request.max_steps,
            temperature=request.temperature,
        )

        background_tasks.add_task(agent_service.run_task, session_id, request.message)

        return ChatResponse(
            session_id=session_id,
            message="任务已开始执行",
            status="running",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"服务器错误：{e}")


@app.get("/api/chat/{session_id}/stream")
async def stream_chat(session_id: str):
    """流式获取执行步骤（SSE）"""
    agent_service = get_agent_service()

    if agent_service.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="会话不存在")

    async def event_generator():
        try:
            async for event in agent_service.stream_steps(session_id):
                yield {"data": json.dumps(event, ensure_ascii=False), "event": "message"}
        except Exception as e:
            yield {"data": json.dumps({"error": str(e)}, ensure_ascii=False), "event": "error"}

    return EventSourceResponse(event_generator())


@app.delete("/api/chat/{session_id}")
async def delete_chat(session_id: str):
    """删除聊天会话"""
    agent_service = get_agent_service()

    if agent_service.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="会话不存在")

    agent_service.delete_session(session_id)
    return {"message": "会话已删除"}


@app.post("/api/chat/{session_id}/reset")
async def reset_chat(session_id: str):
    """重置会话历史"""
    agent_service = get_agent_service()

    if agent_service.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="会话不存在")

    agent_service.reset_session(session_id)
    return {"message": "会话历史已重置"}


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
