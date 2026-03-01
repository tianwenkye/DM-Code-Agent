"""Agent 服务封装"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import uuid
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Dict, List, Optional

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from . import (
    LLMError,
    ReactAgent,
    Tool,
    create_llm_client,
    default_tools,
    PROVIDER_DEFAULTS,
)
from .mcp import MCPManager, load_mcp_config
from .skills import SkillManager

from ..schemas.models import StepEvent


load_dotenv()


@dataclass
class Session:
    """会话数据类"""

    session_id: str
    agent: ReactAgent
    queue: asyncio.Queue[StepEvent]
    loop: asyncio.AbstractEventLoop
    is_running: bool = False


class AgentService:
    """Agent 服务管理类"""

    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.mcp: Optional[MCPManager] = None
        self.skill_manager: Optional[SkillManager] = None
        self._initialized = False
        self.rag_enabled = True
        self.rag_service = None

    async def initialize(self) -> None:
        """初始化 MCP 和技能管理器"""
        if self._initialized:
            return

        try:
            mcp_config = load_mcp_config()
            self.mcp = MCPManager(mcp_config)
            started_count = self.mcp.start_all()
            if started_count > 0:
                print(f"✓ 启动了 {started_count} 个 MCP 服务器")

            self.skill_manager = SkillManager()
            skill_count = self.skill_manager.load_all()
            if skill_count > 0:
                print(f"✓ 加载了 {skill_count} 个技能")

            self._initialized = True
        except Exception as e:
            print(f"⚠ 初始化 MCP/技能管理器失败：{e}")

        try:
            if self.rag_enabled:
                from .core.retrieval_service import RetrievalService
                self.rag_service = RetrievalService()
                print("✓ RAG服务已初始化")
        except Exception as e:
            print(f"⚠ RAG服务初始化失败：{e}")
            self.rag_enabled = False

    def _get_api_key(self, provider: str) -> str | None:
        """根据提供商获取 API 密钥"""
        provider_env_map = {
            "deepseek": "DEEPSEEK_API_KEY",
            "openai": "OPENAI_API_KEY",
            "claude": "CLAUDE_API_KEY",
            "gemini": "GEMINI_API_KEY",
            "glm": "GLM_API_KEY",
        }
        env_var = provider_env_map.get(provider.lower())
        return os.getenv(env_var) if env_var else None

    async def create_session(
        self,
        provider: str = "deepseek",
        model: str = "deepseek-chat",
        base_url: Optional[str] = None,
        max_steps: int = 100,
        temperature: float = 0.7,
        es_index_names: Optional[List[str]] = None,
    ) -> str:
        """创建新会话"""
        await self.initialize()

        session_id = str(uuid.uuid4())

        api_key = self._get_api_key(provider)
        if not api_key:
            raise ValueError(f"未找到 {provider.upper()}_API_KEY 环境变量")

        if not base_url:
            provider_defaults = PROVIDER_DEFAULTS.get(provider, {})
            base_url = provider_defaults.get("base_url", "https://api.deepseek.com")

        client = create_llm_client(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url,
        )

        mcp_tools = self.mcp.get_tools() if self.mcp else []
        tools = default_tools(include_mcp=True, mcp_tools=mcp_tools)

        queue: asyncio.Queue[StepEvent] = asyncio.Queue()
        loop = asyncio.get_event_loop()

        def step_callback(step_num: int, step: Any) -> None:
            """步骤回调"""
            logger.info(f"步骤回调: {step_num}, 动作: {step.action}")
            if session_id in self.sessions:
                event = StepEvent(
                    step_num=step_num,
                    thought=step.thought,
                    action=step.action,
                    action_input=step.action_input,
                    observation=step.observation,
                    is_final=False,
                )
                asyncio.run_coroutine_threadsafe(
                    self.sessions[session_id].queue.put(event),
                    loop
                )
                logger.info(f"步骤事件已放入队列: {step_num}")
            else:
                logger.warning(f"会话 {session_id} 不存在，无法添加步骤事件")

        agent = ReactAgent(
            client,
            tools,
            max_steps=max_steps,
            temperature=temperature,
            step_callback=step_callback,
            skill_manager=self.skill_manager,
            rag_service=self.rag_service if self.rag_enabled else None,
            es_index_names=es_index_names or [],
        )

        session = Session(
            session_id=session_id,
            agent=agent,
            queue=queue,
            loop=loop
        )
        self.sessions[session_id] = session

        return session_id

    async def run_task(self, session_id: str, task: str) -> str:
        """在指定会话中执行任务"""
        logger.info(f"开始执行任务，会话 ID: {session_id}, 任务: {task[:50]}...")
        
        if session_id not in self.sessions:
            raise ValueError(f"会话 {session_id} 不存在")

        session = self.sessions[session_id]
        if session.is_running:
            raise ValueError(f"会话 {session_id} 正在运行中")

        session.is_running = True
        logger.info(f"会话 {session_id} 状态设置为运行中")

        try:
            enhanced_task = task
            if self.rag_enabled and session.agent.rag_service and session.agent.es_index_names:
                try:
                    retrieval_results = session.agent.rag_service.retrieve_content(
                        question=task,
                        index_names=session.agent.es_index_names
                    )
                    enhanced_task = session.agent.rag_service.build_enhanced_task(
                        task, retrieval_results
                    )
                    print(f"✓ RAG检索完成，检索到 {len(retrieval_results)} 个相关文档块")
                except Exception as e:
                    print(f"⚠ RAG检索失败：{e}，使用原始任务")
            
            logger.info(f"调用 agent.run，任务: {enhanced_task[:50]}...")
            result = await asyncio.to_thread(session.agent.run, enhanced_task)
            logger.info(f"agent.run 完成，结果: {str(result)[:100]}...")

            final_answer = result.get("final_answer", "")
            final_event = StepEvent(
                step_num=0,
                is_final=True,
                final_answer=final_answer,
            )
            await session.queue.put(final_event)
            logger.info(f"最终事件已放入队列")

            return final_answer
        except Exception as e:
            logger.error(f"执行任务时出错: {e}", exc_info=True)
            raise
        finally:
            session.is_running = False
            logger.info(f"会话 {session_id} 状态设置为未运行")

    async def stream_steps(self, session_id: str) -> AsyncGenerator[Dict[str, Any], None]:
        """流式获取执行步骤"""
        logger.info(f"开始流式获取步骤，会话 ID: {session_id}")
        
        if session_id not in self.sessions:
            raise ValueError(f"会话 {session_id} 不存在")

        session = self.sessions[session_id]
        timeout_count = 0
        max_timeouts = 300
        event_count = 0

        logger.info(f"开始等待事件，会话运行状态: {session.is_running}")

        while timeout_count < max_timeouts:
            try:
                event = await asyncio.wait_for(session.queue.get(), timeout=1.0)
                timeout_count = 0
                event_count += 1
                logger.info(f"收到事件 {event_count}: is_final={event.is_final}")
                yield event.model_dump()
                if event.is_final:
                    logger.info(f"收到最终事件，结束流式传输")
                    break
            except asyncio.TimeoutError:
                timeout_count += 1
                logger.debug(f"超时 {timeout_count}/{max_timeouts}, 会话运行状态: {session.is_running}")
                if not session.is_running and timeout_count > 5:
                    logger.warning(f"会话未运行且超时，结束流式传输")
                    break
                continue
        
        logger.info(f"流式传输结束，共收到 {event_count} 个事件")

    def reset_session(self, session_id: str) -> None:
        """重置会话历史"""
        if session_id not in self.sessions:
            raise ValueError(f"会话 {session_id} 不存在")

        self.sessions[session_id].agent.reset_conversation()

    def delete_session(self, session_id: str) -> None:
        """删除会话"""
        if session_id in self.sessions:
            del self.sessions[session_id]

    def get_session(self, session_id: str) -> Optional[Session]:
        """获取会话"""
        return self.sessions.get(session_id)

    async def cleanup(self) -> None:
        """清理资源"""
        if self.mcp:
            self.mcp.stop_all()


_agent_service: Optional[AgentService] = None


def get_agent_service() -> AgentService:
    """获取全局 AgentService 实例"""
    global _agent_service
    if _agent_service is None:
        _agent_service = AgentService()
    return _agent_service
