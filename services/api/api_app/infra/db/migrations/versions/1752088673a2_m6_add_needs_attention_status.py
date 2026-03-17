"""
M6: 添加 needs_attention 状态到 run_status 枚举。

needs_attention 表示 Gate 检查失败且自动修复无效，
需要人工介入的 run 状态。
"""

from __future__ import annotations

from alembic import op

revision: str = "1752088673a2"
down_revision: str | None = "28f6cc24530e"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    向 run_status 枚举类型添加 needs_attention 值。

    PostgreSQL 枚举类型只能追加值，不能删除，
    使用 ALTER TYPE ... ADD VALUE 语法。
    """
    op.execute(
        "ALTER TYPE run_status ADD VALUE IF NOT EXISTS 'needs_attention'"
    )


def downgrade() -> None:
    """
    降级不支持删除枚举值（PostgreSQL 限制）。

    如需回滚，需手动处理数据库枚举类型。
    """
    # PostgreSQL 不支持直接删除枚举值，降级为空操作
    pass
