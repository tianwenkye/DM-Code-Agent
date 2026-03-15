"""AskTool - 向用户提问的工具实现"""

from __future__ import annotations

import sys
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from .base import Tool


@dataclass
class AskToolConfig:
    """AskTool 配置"""
    prompt_template: str = "需要您的帮助来完成任务"
    allow_skip: bool = True
    skip_keyword: str = "skip"
    input_timeout: float = 300.0
    max_retries: int = 3
    show_options: bool = True


@dataclass
class QuestionRecord:
    """提问记录"""
    question_id: str
    question: str
    context: str
    user_response: str
    asked_at: float = field(default_factory=lambda: datetime.now().timestamp())
    answered_at: Optional[float] = None


class AskTool:
    """向用户提问的工具
    
    用于在 Agent 执行过程中向用户请求额外信息或确认。
    支持同步阻塞模式，当 Agent 调用此工具时，执行流程会暂停等待用户输入。
    
    Attributes:
        config (AskToolConfig): 工具配置
        _input_handler (Callable): 输入处理函数
        _question_history (List[QuestionRecord]): 提问历史记录
        _question_counter (int): 问题计数器
        _lock (threading.Lock): 线程锁
    """
    
    def __init__(
        self,
        config: Optional[AskToolConfig] = None,
        input_handler: Optional[Callable[[str], str]] = None
    ):
        """初始化 AskTool
        
        Args:
            config (Optional[AskToolConfig]): 工具配置，默认使用 AskToolConfig()
            input_handler (Optional[Callable[[str], str]]): 自定义输入处理函数
        """
        self.config = config or AskToolConfig()
        self._input_handler = input_handler or self._default_input_handler
        self._question_history: List[QuestionRecord] = []
        self._question_counter = 0
        self._lock = threading.Lock()
    
    def _default_input_handler(self, prompt: str) -> str:
        """默认输入处理函数
        
        Args:
            prompt (str): 提示信息
            
        Returns:
            str: 用户输入内容
        """
        try:
            from colorama import Fore, Style
            colors_available = True
        except ImportError:
            colors_available = False
            Fore = type('Fore', (), {'CYAN': '', 'YELLOW': '', 'GREEN': ''})()
            Style = type('Style', (), {'BRIGHT': '', 'RESET_ALL': ''})()
        
        if colors_available:
            print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}{Style.BRIGHT}❓ Agent 需要您的帮助{Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            print(f"{prompt}")
            if self.config.allow_skip:
                print(f"{Fore.CYAN}(输入 '{self.config.skip_keyword}' 跳过此问题){Style.RESET_ALL}")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        else:
            print(f"\n{'='*60}")
            print("❓ Agent 需要您的帮助")
            print(f"{'='*60}")
            print(f"{prompt}")
            if self.config.allow_skip:
                print(f"(输入 '{self.config.skip_keyword}' 跳过此问题)")
            print(f"{'='*60}")
        
        try:
            user_input = input("> ").strip()
            return user_input
        except (EOFError, KeyboardInterrupt):
            return self.config.skip_keyword if self.config.allow_skip else ""
    
    def execute(self, arguments: Dict[str, Any]) -> str:
        """执行提问工具
        
        Args:
            arguments (Dict[str, Any]): 工具参数
                - question (str): 要问用户的问题（必需）
                - context (str): 问题的上下文信息（可选）
                - options (List[str]): 选项列表（可选）
                - default (str): 默认答案（可选）
                
        Returns:
            str: 用户的回答或跳过提示
        """
        question = arguments.get("question", "")
        context = arguments.get("context", "")
        options = arguments.get("options", [])
        default = arguments.get("default", "")
        
        if not question:
            return "错误: 缺少 question 参数"
        
        with self._lock:
            self._question_counter += 1
            question_id = f"q_{self._question_counter}"
        
        full_prompt = f"{self.config.prompt_template}\n\n问题: {question}"
        
        if context:
            full_prompt += f"\n\n上下文信息: {context}"
        
        if options and self.config.show_options:
            options_text = "\n".join([f"  {i+1}. {opt}" for i, opt in enumerate(options)])
            full_prompt += f"\n\n可选答案:\n{options_text}"
        
        if default:
            full_prompt += f"\n\n(默认: {default})"
        
        record = QuestionRecord(
            question_id=question_id,
            question=question,
            context=context,
            user_response=""
        )
        
        retry_count = 0
        while retry_count < self.config.max_retries:
            response = self._input_handler(full_prompt)
            
            if self.config.allow_skip and response.lower() == self.config.skip_keyword:
                record.user_response = "[跳过]"
                record.answered_at = datetime.now().timestamp()
                self._question_history.append(record)
                return "用户跳过了此问题"
            
            if options:
                try:
                    choice = int(response)
                    if 1 <= choice <= len(options):
                        response = options[choice - 1]
                    else:
                        print(f"请输入 1-{len(options)} 之间的数字")
                        retry_count += 1
                        continue
                except ValueError:
                    if response in options:
                        pass
                    else:
                        print(f"无效的选择，请重新输入")
                        retry_count += 1
                        continue
            
            if not response and default:
                response = default
            
            if response:
                record.user_response = response
                record.answered_at = datetime.now().timestamp()
                self._question_history.append(record)
                return f"用户回答: {response}"
            
            retry_count += 1
            if retry_count < self.config.max_retries:
                print("请提供有效的回答")
        
        record.user_response = "[重试次数超限]"
        record.answered_at = datetime.now().timestamp()
        self._question_history.append(record)
        return "用户未提供有效回答，已达到最大重试次数"
    
    def to_tool(self) -> Tool:
        """转换为 Tool 对象
        
        Returns:
            Tool: 工具对象
        """
        return Tool(
            name="ask_tool",
            description=(
                "向用户提问以获取必要信息。"
                "当你需要用户提供额外信息、确认操作或做出选择时使用此工具。"
                "Arguments: {"
                "\"question\": string (required, 要问用户的问题), "
                "\"context\": optional string (问题的上下文信息), "
                "\"options\": optional array of strings (可选答案列表), "
                "\"default\": optional string (默认答案)"
                "}. "
                "返回用户的回答内容。"
            ),
            runner=self.execute
        )
    
    def get_question_history(self) -> List[Dict[str, Any]]:
        """获取提问历史记录
        
        Returns:
            List[Dict[str, Any]]: 提问历史列表
        """
        return [
            {
                "question_id": r.question_id,
                "question": r.question,
                "context": r.context,
                "user_response": r.user_response,
                "asked_at": r.asked_at,
                "answered_at": r.answered_at,
            }
            for r in self._question_history
        ]
    
    def clear_history(self) -> None:
        """清空提问历史"""
        with self._lock:
            self._question_history.clear()
            self._question_counter = 0


def ask_user(arguments: Dict[str, Any]) -> str:
    """向用户提问的独立函数
    
    Args:
        arguments (Dict[str, Any]): 工具参数
        
    Returns:
        str: 用户的回答
    """
    tool = AskTool()
    return tool.execute(arguments)
