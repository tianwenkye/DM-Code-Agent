"""用户认证相关路由"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/user", tags=["user"])


@router.get("/info")
async def get_user_info():
    """获取用户信息（示例）"""
    return {"message": "用户认证功能待实现"}


@router.post("/login")
async def login():
    """用户登录（示例）"""
    return {"message": "用户登录功能待实现"}


@router.post("/logout")
async def logout():
    """用户登出（示例）"""
    return {"message": "用户登出功能待实现"}
