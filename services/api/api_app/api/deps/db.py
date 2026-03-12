"""数据库会话依赖注入 - 为 FastAPI 路由提供数据库会话。"""

# 从 session.py 导入 get_db_session 并重新导出为 get_db
# get_db 就是 get_db_session 的别名，方便路由层使用更短的名称
from api_app.infra.db.session import get_db_session as get_db

__all__ = ["get_db"]
