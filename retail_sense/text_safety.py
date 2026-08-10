"""HTML、CSV 与文件名输出边界的轻量安全处理。"""

from __future__ import annotations

import html
import re


def escape_html(value: object) -> str:
    """转义即将插入 unsafe_allow_html 内容的动态文本。"""
    return html.escape(str(value), quote=True)


def csv_safe(value: object) -> object:
    """阻止电子表格将外部文本解释为公式。"""
    if not isinstance(value, str):
        return value
    if value.lstrip().startswith(("=", "+", "-", "@")):
        return "'" + value
    return value


def safe_filename(value: object, fallback: str = "report") -> str:
    """生成不含路径分隔符和控制字符的短文件名。"""
    cleaned = re.sub(r"[^\w.-]+", "_", str(value), flags=re.UNICODE)
    cleaned = cleaned.strip("._")[:80]
    return cleaned or fallback
