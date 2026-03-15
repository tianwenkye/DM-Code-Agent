"""用户输入处理器 - 处理运行时用户干预"""

from __future__ import annotations

import queue
import sys
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class InterventionType(Enum):
    """干预类型枚举"""
    CANCEL = "cancel"
    PAUSE = "pause"
    RESUME = "resume"
    INPUT = "input"
    SKIP = "skip"


@dataclass
class UserIntervention:
    """用户干预事件"""
    type: InterventionType
    content: str = ""
    timestamp: float = field(default_factory=lambda: datetime.now().timestamp())
    source: str = "user"


@dataclass
class InterventionConfig:
    """干预配置"""
    enable_hotkeys: bool = True
    enable_input_queue: bool = True
    pause_on_input: bool = False
    input_timeout: float = 0.1
    max_queue_size: int = 100
    hotkey_cancel: str = "\x03"
    hotkey_pause: str = "p"
    hotkey_input: str = "i"
    hotkey_skip: str = "s"


class UserInputHandler:
    """用户输入处理器
    
    处理 Agent 运行时的用户干预，包括：
    - 热键触发（取消、暂停、插入指令）
    - 异步输入队列
    - 同步阻塞输入
    
    Attributes:
        config (InterventionConfig): 处理器配置
        _input_queue (queue.Queue): 用户输入队列
        _lock (threading.Lock): 线程锁
        _on_intervention (Callable): 干预回调函数
        _listener_thread (threading.Thread): 监听线程
        _running (bool): 运行状态
        _paused (bool): 暂停状态
        _pause_event (threading.Event): 暂停事件
        _intervention_history (List[UserIntervention]): 干预历史
    """
    
    def __init__(
        self,
        config: Optional[InterventionConfig] = None,
        on_intervention: Optional[Callable[[UserIntervention], None]] = None
    ):
        """初始化用户输入处理器
        
        Args:
            config (Optional[InterventionConfig]): 处理器配置
            on_intervention (Optional[Callable[[UserIntervention], None]]): 干预回调函数
        """
        self.config = config or InterventionConfig()
        self._input_queue: queue.Queue[UserIntervention] = queue.Queue(
            maxsize=self.config.max_queue_size
        )
        self._lock = threading.Lock()
        self._on_intervention = on_intervention
        self._listener_thread: Optional[threading.Thread] = None
        self._running = False
        self._paused = False
        self._pause_event = threading.Event()
        self._pause_event.set()
        self._intervention_history: List[UserIntervention] = []
        self._pending_inputs: List[str] = []
    
    def start(self) -> None:
        """启动监听线程"""
        if self._running:
            return
        
        self._running = True
        self._listener_thread = threading.Thread(
            target=self._listen_loop,
            daemon=True,
            name="user-input-listener"
        )
        self._listener_thread.start()
    
    def stop(self) -> None:
        """停止监听线程"""
        self._running = False
        self._pause_event.set()
        if self._listener_thread and self._listener_thread.is_alive():
            self._listener_thread.join(timeout=2.0)
    
    def _listen_loop(self) -> None:
        """监听循环（简化版，不使用 select）"""
        try:
            from colorama import Fore, Style
            colors_available = True
        except ImportError:
            colors_available = False
            Fore = type('Fore', (), {'CYAN': '', 'YELLOW': '', 'GREEN': '', 'RED': ''})()
            Style = type('Style', (), {'BRIGHT': '', 'RESET_ALL': ''})()
        
        if colors_available:
            print(f"\n{Fore.CYAN}💡 干预模式已启用{Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}输入 'p' 暂停 | 'i <消息>' 插入指令 | 's' 跳过当前步骤{Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}按 Ctrl+C 取消任务{Style.RESET_ALL}\n")
        else:
            print("\n💡 干预模式已启用")
            print("  输入 'p' 暂停 | 'i <消息>' 插入指令 | 's' 跳过当前步骤")
            print("  按 Ctrl+C 取消任务\n")
    
    def check_intervention(self, timeout: float = 0.0) -> Optional[UserIntervention]:
        """检查是否有用户干预
        
        Args:
            timeout (float): 超时时间（秒）
            
        Returns:
            Optional[UserIntervention]: 干预事件，无则返回 None
        """
        try:
            return self._input_queue.get(timeout=timeout)
        except queue.Empty:
            return None
    
    def submit_intervention(self, intervention: UserIntervention) -> bool:
        """提交干预事件
        
        Args:
            intervention (UserIntervention): 干预事件
            
        Returns:
            bool: 是否成功提交
        """
        try:
            self._input_queue.put_nowait(intervention)
            with self._lock:
                self._intervention_history.append(intervention)
            if self._on_intervention:
                self._on_intervention(intervention)
            return True
        except queue.Full:
            return False
    
    def submit_input(self, content: str) -> bool:
        """提交用户输入
        
        Args:
            content (str): 输入内容
            
        Returns:
            bool: 是否成功提交
        """
        return self.submit_intervention(
            UserIntervention(type=InterventionType.INPUT, content=content)
        )
    
    def request_cancel(self) -> bool:
        """请求取消任务
        
        Returns:
            bool: 是否成功提交
        """
        return self.submit_intervention(
            UserIntervention(type=InterventionType.CANCEL, content="用户请求取消")
        )
    
    def request_pause(self) -> bool:
        """请求暂停
        
        Returns:
            bool: 是否成功提交
        """
        if not self._paused:
            self._paused = True
            self._pause_event.clear()
            return self.submit_intervention(
                UserIntervention(type=InterventionType.PAUSE, content="用户请求暂停")
            )
        return False
    
    def request_resume(self) -> bool:
        """请求恢复
        
        Returns:
            bool: 是否成功提交
        """
        if self._paused:
            self._paused = False
            self._pause_event.set()
            return self.submit_intervention(
                UserIntervention(type=InterventionType.RESUME, content="用户请求恢复")
            )
        return False
    
    def request_skip(self) -> bool:
        """请求跳过当前步骤
        
        Returns:
            bool: 是否成功提交
        """
        return self.submit_intervention(
            UserIntervention(type=InterventionType.SKIP, content="用户请求跳过")
        )
    
    def wait_for_resume(self, timeout: Optional[float] = None) -> bool:
        """等待恢复
        
        Args:
            timeout (Optional[float]): 超时时间（秒）
            
        Returns:
            bool: 是否恢复
        """
        return self._pause_event.wait(timeout=timeout)
    
    def is_paused(self) -> bool:
        """是否暂停状态
        
        Returns:
            bool: 是否暂停
        """
        return self._paused
    
    def is_running(self) -> bool:
        """是否运行状态
        
        Returns:
            bool: 是否运行
        """
        return self._running
    
    def add_pending_input(self, content: str) -> None:
        """添加待处理输入
        
        Args:
            content (str): 输入内容
        """
        with self._lock:
            self._pending_inputs.append(content)
    
    def get_pending_inputs(self) -> List[str]:
        """获取并清空待处理输入
        
        Returns:
            List[str]: 待处理输入列表
        """
        with self._lock:
            inputs = list(self._pending_inputs)
            self._pending_inputs.clear()
            return inputs
    
    def get_intervention_history(self) -> List[Dict[str, Any]]:
        """获取干预历史
        
        Returns:
            List[Dict[str, Any]]: 干预历史列表
        """
        with self._lock:
            return [
                {
                    "type": i.type.value,
                    "content": i.content,
                    "timestamp": i.timestamp,
                    "source": i.source,
                }
                for i in self._intervention_history
            ]
    
    def clear_history(self) -> None:
        """清空历史记录"""
        with self._lock:
            self._intervention_history.clear()
            self._pending_inputs.clear()


class BlockingInputHandler:
    """阻塞式输入处理器
    
    用于同步阻塞等待用户输入的场景。
    """
    
    def __init__(
        self,
        timeout: float = 300.0,
        prompt_prefix: str = "💬",
        show_instructions: bool = True
    ):
        """初始化阻塞式输入处理器
        
        Args:
            timeout (float): 超时时间（秒）
            prompt_prefix (str): 提示前缀
            show_instructions (bool): 是否显示使用说明
        """
        self.timeout = timeout
        self.prompt_prefix = prompt_prefix
        self.show_instructions = show_instructions
    
    def get_input(
        self,
        prompt: str,
        default: Optional[str] = None,
        allow_empty: bool = False
    ) -> str:
        """获取用户输入（阻塞）
        
        Args:
            prompt (str): 提示信息
            default (Optional[str]): 默认值
            allow_empty (bool): 是否允许空输入
            
        Returns:
            str: 用户输入
        """
        try:
            from colorama import Fore, Style
            colors_available = True
        except ImportError:
            colors_available = False
            Fore = type('Fore', (), {'CYAN': '', 'YELLOW': '', 'GREEN': ''})()
            Style = type('Style', (), {'BRIGHT': '', 'RESET_ALL': ''})()
        
        full_prompt = f"\n{self.prompt_prefix} {prompt}"
        if default:
            full_prompt += f" [默认: {default}]"
        full_prompt += ": "
        
        if colors_available:
            print(f"{Fore.CYAN}{full_prompt}{Style.RESET_ALL}", end="", flush=True)
        else:
            print(full_prompt, end="", flush=True)
        
        try:
            user_input = input().strip()
            if not user_input and default:
                return default
            if not user_input and not allow_empty:
                print(f"{Fore.YELLOW}请输入有效内容{Style.RESET_ALL}")
                return self.get_input(prompt, default, allow_empty)
            return user_input
        except (EOFError, KeyboardInterrupt):
            if default:
                return default
            return ""
    
    def get_confirmation(self, prompt: str, default: bool = False) -> bool:
        """获取用户确认
        
        Args:
            prompt (str): 提示信息
            default (bool): 默认值
            
        Returns:
            bool: 用户确认结果
        """
        default_str = "Y/n" if default else "y/N"
        response = self.get_input(f"{prompt} [{default_str}]", allow_empty=True)
        
        if not response:
            return default
        
        return response.lower() in ("y", "yes", "是")
    
    def get_choice(
        self,
        prompt: str,
        options: List[str],
        default: Optional[int] = None
    ) -> int:
        """获取用户选择
        
        Args:
            prompt (str): 提示信息
            options (List[str]): 选项列表
            default (Optional[int]): 默认选项索引
            
        Returns:
            int: 选择的选项索引
        """
        try:
            from colorama import Fore, Style
        except ImportError:
            Fore = type('Fore', (), {'CYAN': '', 'YELLOW': ''})()
            Style = type('Style', (), {'RESET_ALL': ''})()
        
        print(f"\n{self.prompt_prefix} {prompt}")
        for i, option in enumerate(options):
            marker = "→" if default is not None and i == default else " "
            print(f"  {marker} {i + 1}. {option}")
        
        while True:
            response = self.get_input(
                f"请选择 (1-{len(options)})",
                default=str(default + 1) if default is not None else None,
                allow_empty=True
            )
            
            try:
                choice = int(response) - 1
                if 0 <= choice < len(options):
                    return choice
                print(f"{Fore.YELLOW}请输入 1-{len(options)} 之间的数字{Style.RESET_ALL}")
            except ValueError:
                print(f"{Fore.YELLOW}请输入有效的数字{Style.RESET_ALL}")
