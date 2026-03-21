"""
LLM 输出 JSON 修复工具。
LLM 常见问题：markdown 代码块包裹、前后多余文本、尾部逗号等，
本模块提供统一的修复函数。
"""
from __future__ import annotations

import json
import re


def repair_llm_json(raw: str) -> str:
    """
    尝试修复 LLM 输出中的常见 JSON 问题。

    修复策略（按顺序尝试）：
    1. 去除 ```json ... ``` 或 ``` ... ``` markdown 代码块包裹
    2. 去除 JSON 前后的多余文本（找到第一个 { 或 [ 和最后一个 } 或 ]）
    3. 修复尾部多余逗号（trailing comma）
    4. 验证修复后的字符串是合法 JSON

    - raw: LLM 的原始输出字符串
    - 返回: 修复后的 JSON 字符串
    - 抛出: json.JSONDecodeError 当修复失败时
    """
    # 先去除首尾空白
    text = raw.strip()

    # 直接尝试解析，如果本身就是合法 JSON 则直接返回
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    # 去除 markdown 代码块包裹：```json ... ``` 或 ``` ... ```
    text = re.sub(
        r"^```(?:json)?\s*\n?(.*?)\n?\s*```$",
        r"\1",
        text,
        flags=re.DOTALL,
    )
    text = text.strip()

    # 尝试解析去除代码块后的结果
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass

    # 提取最外层的 JSON 对象或数组
    # 找到第一个 { 或 [ 以及最后一个 } 或 ]
    first_brace = text.find("{")
    first_bracket = text.find("[")

    # 确定起始位置和对应的结束字符
    if first_brace == -1 and first_bracket == -1:
        raise json.JSONDecodeError("无法找到 JSON 起始符号", text, 0)

    if first_brace == -1:
        start = first_bracket
        end_char = "]"
    elif first_bracket == -1:
        start = first_brace
        end_char = "}"
    elif first_brace < first_bracket:
        start = first_brace
        end_char = "}"
    else:
        start = first_bracket
        end_char = "]"

    # 找最后一个对应的结束符号
    end = text.rfind(end_char)
    if end == -1 or end < start:
        raise json.JSONDecodeError("无法找到 JSON 结束符号", text, len(text) - 1)

    text = text[start : end + 1]

    # 修复尾部多余逗号：逗号后面紧跟 } 或 ]
    text = re.sub(r",\s*([}\]])", r"\1", text)

    # 最终尝试解析
    json.loads(text)
    return text
