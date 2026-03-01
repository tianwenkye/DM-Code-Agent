"""后端数据模型定义"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """聊天请求模型"""

    message: str = Field(..., description="用户输入的消息")
    provider: str = Field(default="glm", description="LLM 提供商")
    model: str = Field(default="ep-20260210175539-4gr98", description="模型名称")
    base_url: Optional[str] = Field(default="https://ark.cn-beijing.volces.com/api/v3", description="API 基础 URL")
    max_steps: int = Field(default=100, description="最大执行步骤数")
    temperature: float = Field(default=0.7, description="温度参数")


class ChatResponse(BaseModel):
    """聊天响应模型"""

    session_id: str = Field(..., description="会话 ID")
    message: str = Field(..., description="最终响应消息")
    status: str = Field(default="completed", description="执行状态")


class StepEvent(BaseModel):
    """执行步骤事件模型（用于 SSE）"""

    step_num: int = Field(..., description="步骤编号")
    thought: str = Field(default="", description="思考过程")
    action: str = Field(default="", description="执行的动作")
    action_input: Optional[Dict[str, Any]] = Field(default=None, description="动作输入")
    observation: str = Field(default="", description="观察结果")
    is_final: bool = Field(default=False, description="是否为最终步骤")
    final_answer: Optional[str] = Field(default=None, description="最终答案")


class ErrorResponse(BaseModel):
    """错误响应模型"""

    error: str = Field(..., description="错误信息")
    detail: Optional[str] = Field(default=None, description="详细错误信息")
