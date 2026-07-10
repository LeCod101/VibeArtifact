"""工作区文件仓储 - 提供 workspace_files 表的数据访问方法。

写入采用 PostgreSQL ON CONFLICT upsert：同一 (run_id, file_path)
重复写入时覆盖 content 并将 version 递增，保证"最新版本可查"。
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from platform_data.models.workspace import WorkspaceFile
from platform_data.repositories.base import BaseRepository


class WorkspaceRepository(BaseRepository[WorkspaceFile]):
    """工作区文件仓储，Agent/Gate/Exporter 读写产物文件的唯一入口。"""

    model_class = WorkspaceFile

    async def write_files(
        self,
        run_id: UUID,
        files: list[dict],
    ) -> int:
        """批量 upsert 工作区文件。

        每个文件字典需包含 path、content、kind、agent 键，
        可选 turn 键（review 轮次，Phase 4 使用）。
        同一 (run_id, file_path) 已存在时覆盖内容并 version + 1。

        参数:
            run_id: 所属 job_run 的 UUID
            files: 文件字典列表

        返回:
            写入（含覆盖）的文件数
        """
        written = 0
        for f in files:
            path = f.get("path", "")
            content = f.get("content", "")
            if not path or not content:
                continue

            stmt = pg_insert(WorkspaceFile).values(
                run_id=run_id,
                file_path=path,
                content=content,
                file_kind=f.get("kind", "code"),
                version=1,
                written_by_agent=f.get("agent", ""),
                written_by_turn=f.get("turn"),
            )
            stmt = stmt.on_conflict_do_update(
                constraint="uq_workspace_files_run_path",
                set_={
                    "content": stmt.excluded.content,
                    "file_kind": stmt.excluded.file_kind,
                    "version": WorkspaceFile.version + 1,
                    "written_by_agent": stmt.excluded.written_by_agent,
                    "written_by_turn": stmt.excluded.written_by_turn,
                },
            )
            await self.session.execute(stmt)
            written += 1

        await self.session.flush()
        return written

    async def read_all(self, run_id: UUID) -> list[WorkspaceFile]:
        """读取指定 run 的全部工作区文件（按路径排序）。

        参数:
            run_id: job_run 的 UUID

        返回:
            WorkspaceFile 实例列表
        """
        stmt = (
            select(WorkspaceFile)
            .where(WorkspaceFile.run_id == run_id)
            .order_by(WorkspaceFile.file_path)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def read_paths(self, run_id: UUID, prefix: str) -> list[WorkspaceFile]:
        """按路径前缀读取指定 run 的工作区文件。

        参数:
            run_id: job_run 的 UUID
            prefix: 路径前缀（如 "backend/"）

        返回:
            匹配前缀的 WorkspaceFile 实例列表
        """
        stmt = (
            select(WorkspaceFile)
            .where(
                WorkspaceFile.run_id == run_id,
                WorkspaceFile.file_path.startswith(prefix),
            )
            .order_by(WorkspaceFile.file_path)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
