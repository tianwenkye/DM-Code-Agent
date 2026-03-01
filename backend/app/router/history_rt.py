"""历史记录相关路由"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
async def get_history():
    """获取历史记录（示例）"""
    return {"message": "历史记录功能待实现"}


@router.delete("/{history_id}")
async def delete_history(history_id: str):
    """删除历史记录（示例）"""
    return {"message": f"删除历史记录 {history_id} 功能待实现"}
