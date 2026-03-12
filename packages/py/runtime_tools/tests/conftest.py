"""运行时工具测试配置 - 将 runtime_tools 包加入 sys.path。"""

import sys
from pathlib import Path

# 将 packages/py/runtime_tools 加入 sys.path，使 runtime_tools 包可被直接导入
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
