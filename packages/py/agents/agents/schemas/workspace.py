"""
工作区文件数据模块。

定义 Agent 层使用的轻量工作区文件模型，
是 platform_data.models.workspace.WorkspaceFile 的内存态对应物
（Agent 包不依赖 platform_data，通过此模型解耦）。
"""

from pydantic import BaseModel


class WorkspaceFileData(BaseModel):
    """
    工作区文件的内存态表示。

    - path: 文件路径（相对于生成项目根目录）
    - content: 文件内容（UTF-8 文本）
    - kind: 文件类别，取值 "code" / "doc" / "diagram"
    """

    path: str
    content: str
    kind: str = "code"
