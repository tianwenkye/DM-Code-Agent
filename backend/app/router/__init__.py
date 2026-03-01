"""路由模块"""

from .chat_rt import router as chat_router
from .user_rt import router as user_router
from .history_rt import router as history_router

__all__ = ["chat_router", "user_router", "history_router"]

