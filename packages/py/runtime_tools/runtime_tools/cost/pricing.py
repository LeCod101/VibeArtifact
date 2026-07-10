"""
国产模型成本估算表。

LiteLLM 曾自动查价格表计算成本，LangChain 原生集成没有这一能力，
改为本模块维护的静态价格表 + 手工计算。价格随时间/厂商政策变化，
本表为 best-effort 估算，未收录的 (provider, model) 组合按 0.0 处理
并记录一条日志，不影响主流程。

价格来源（记录调研时间，需定期核对官方定价页）：
- DeepSeek: 官方 API 文档 https://api-docs.deepseek.com/quick_start/pricing-details-usd
  （deepseek-chat: 输入 $0.27/1M(cache miss)，输出 $1.10/1M；
   deepseek-reasoner: 输入 $0.55/1M，输出 $2.19/1M）
- Moonshot (Kimi): 官方定价页 https://platform.kimi.com/docs/pricing/chat-v1
  （moonshot-v1-8k 约 ¥12/1M tokens，已按约 7.2 的 USD/CNY 汇率折算为美元）
- MiniMax: https://developer.puter.com/tutorials/minimax-api-pricing
  （MiniMax-M3: 输入 $0.30/1M，输出 $1.20/1M）
- DashScope（通义千问）: 官方定价随模型/上下文长度呈阶梯定价，未采集到稳定数字，
  暂缺省为 0（会记录警告日志，不阻断成本记账）。
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# (provider, model) -> (input_price_per_1m_usd, output_price_per_1m_usd)
_PRICING_TABLE: dict[tuple[str, str], tuple[float, float]] = {
    ("deepseek", "deepseek-chat"): (0.27, 1.10),
    ("deepseek", "deepseek-reasoner"): (0.55, 2.19),
    ("moonshot", "moonshot-v1-8k"): (1.65, 1.65),
    ("moonshot", "moonshot-v1-32k"): (3.30, 3.30),
    ("moonshot", "moonshot-v1-128k"): (8.25, 8.25),
    ("minimax", "MiniMax-M3"): (0.30, 1.20),
}


def calculate_cost(
    provider: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
) -> float:
    """
    估算一次 LLM 调用的成本（美元）。

    未收录的 (provider, model) 组合返回 0.0 并记录警告日志，
    不抛出异常（成本记账是 best-effort，不应影响生成主流程）。

    - provider: provider 名称（如 "deepseek"）
    - model: 模型标识（如 "deepseek-chat"）
    - prompt_tokens: 输入 token 数
    - completion_tokens: 输出 token 数
    - 返回: 估算成本（美元）
    """
    key = (provider, model)
    prices = _PRICING_TABLE.get(key)
    if prices is None:
        logger.warning(
            "未找到 (%s, %s) 的价格表条目，成本记为 0.0", provider, model,
        )
        return 0.0

    input_price, output_price = prices
    return (
        prompt_tokens / 1_000_000 * input_price
        + completion_tokens / 1_000_000 * output_price
    )
