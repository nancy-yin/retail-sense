"""运行环境适配：本地保留 JSON，公网演示仅使用 Session 内存状态。"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def is_read_only_demo() -> bool:
    """判断是否应禁用本地文件写入。

    Streamlit Community Cloud 的运行目录位于 ``/mount/src``，重启或重新部署后
    文件会重置。本地 Git 克隆保留原有 JSON 持久化；未检测到 Git 仓库的副本也
    默认采用安全的演示模式。需要强制本地文件持久化时可设置
    ``RETAILSENSE_PERSISTENCE=local``。
    """
    persistence = os.getenv("RETAILSENSE_PERSISTENCE", "").strip().lower()
    if persistence == "local":
        return False
    if persistence in {"memory", "demo"}:
        return True

    cloud_markers = (
        "STREAMLIT_SHARING_MODE",
        "STREAMLIT_CLOUD",
    )
    if any(os.getenv(marker) for marker in cloud_markers):
        return True
    if Path("/mount/src").exists():
        return True
    return not (PROJECT_ROOT / ".git").exists()
