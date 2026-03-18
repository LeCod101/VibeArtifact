"""
Agent 全局注册表模块。

提供 AgentRegistry 单例，管理所有已注册 Agent 的配置。
支持按 ID 查询、按类别筛选、按模型档位筛选等操作。
"""

from agents.configs.base import AgentConfig, ModelTier, RoleCategory


class AgentRegistry:
    """
    Agent 全局注册表。

    单例模式，管理所有已注册 Agent 的配置。
    通过 get_instance() 获取全局唯一实例。
    """

    _instance: "AgentRegistry | None" = None

    def __init__(self) -> None:
        """初始化注册表，创建空的 Agent 配置字典。"""
        self._agents: dict[str, AgentConfig] = {}

    @classmethod
    def get_instance(cls) -> "AgentRegistry":
        """
        获取全局单例。

        如果实例不存在则创建新实例。
        返回全局唯一的 AgentRegistry 实例。
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    @classmethod
    def reset(cls) -> None:
        """
        重置单例（测试用）。

        将全局实例置为 None，下次调用 get_instance() 会创建新实例。
        """
        cls._instance = None

    def register(self, config: AgentConfig) -> None:
        """
        注册一个 Agent（幂等）。

        将 AgentConfig 加入注册表。如果 agent_id 已存在则跳过，保证重复调用安全。
        - config: 要注册的 Agent 配置
        """
        if config.agent_id in self._agents:
            return
        self._agents[config.agent_id] = config

    def get(self, agent_id: str) -> AgentConfig:
        """
        根据 ID 获取 Agent 配置。

        - agent_id: Agent 唯一标识
        返回对应的 AgentConfig，未找到则抛出 KeyError。
        """
        if agent_id not in self._agents:
            raise KeyError(f"Agent '{agent_id}' 未注册")
        return self._agents[agent_id]

    def list_agents(self) -> list[AgentConfig]:
        """
        列出所有已注册 Agent。

        返回所有已注册的 AgentConfig 列表。
        """
        return list(self._agents.values())

    def list_by_category(self, category: RoleCategory) -> list[AgentConfig]:
        """
        按角色类别筛选 Agent。

        - category: 角色类别枚举值
        返回匹配该类别的所有 AgentConfig 列表。
        """
        return [
            a for a in self._agents.values() if a.role_category == category
        ]

    def list_by_tier(self, tier: ModelTier) -> list[AgentConfig]:
        """
        按模型档位筛选 Agent。

        - tier: 模型档位枚举值
        返回匹配该档位的所有 AgentConfig 列表。
        """
        return [a for a in self._agents.values() if a.model_tier == tier]
