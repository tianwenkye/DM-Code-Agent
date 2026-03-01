"""聊天相关路由"""

from __future__ import annotations

import json
from typing import Dict

from fastapi import APIRouter, BackgroundTasks, HTTPException
from sse_starlette.sse import EventSourceResponse

from ..service.agent_service import get_agent_service
from ..schemas.models import ChatRequest, ChatResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
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


@router.get("/{session_id}/stream")
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


@router.delete("/{session_id}")
async def delete_chat(session_id: str):
    """删除聊天会话"""
    agent_service = get_agent_service()

    if agent_service.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="会话不存在")

    agent_service.delete_session(session_id)
    return {"message": "会话已删除"}


@router.post("/{session_id}/reset")
async def reset_chat(session_id: str):
    """重置会话历史"""
    agent_service = get_agent_service()

    if agent_service.get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="会话不存在")

    agent_service.reset_session(session_id)
    return {"message": "会话历史已重置"}
