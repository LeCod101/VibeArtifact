"""Agent 依赖注入 - 为 API 路由提供 AgentRunner 实例。

M4 阶段不通过 AgentRunner 调用真实 LLM，
路由层直接使用 mock 函数模拟 agent 输出。
此文件为后续 M5 接入真实 LLM 预留接口。
"""


def get_agent_runner():
    """获取 AgentRunner 实例（M4 占位）。

    M4 阶段路由不使用 AgentRunner，
    此函数仅为依赖注入接口预留。
    M5 替换为真实 LLM provider 后启用。

    返回：
        None（M4 未启用）
    """
    return None
