"""Platform data models package."""

# Approval
from platform_data.models.approval import ApprovalAction, ApprovalRecord

# Artifact
from platform_data.models.artifact import Artifact, ArtifactStatus, ArtifactVersion
from platform_data.models.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

# Conversation
from platform_data.models.conversation import (
    Conversation,
    ConversationBranch,
    ConversationMode,
    ConversationStatus,
    Message,
    MessageRole,
)

# Execution & Audit
from platform_data.models.execution import (
    AgentRun,
    AuditEvent,
    CostLedger,
    JobRun,
    LeaseLock,
    RunStatus,
)

# IR
from platform_data.models.ir import (
    IREdge,
    IRNode,
    IROperation,
    IRSnapshot,
    SnapshotStatus,
)
from platform_data.models.project import ModelTier, Project, ProjectConfig, ProjectStatus

# Template
from platform_data.models.template import ProjectTemplate, TemplateCategory

# Usage
from platform_data.models.usage_record import UsageRecord

# User & Project
from platform_data.models.user import User, UserStatus

# User API Key & Model Preference
from platform_data.models.user_api_key import UserApiKey, UserModelPreference

__all__ = [
    "Base",
    "TimestampMixin",
    "UUIDPrimaryKeyMixin",
    # User & Project
    "User",
    "UserStatus",
    "Project",
    "ProjectConfig",
    "ProjectStatus",
    "ModelTier",
    # IR
    "IRSnapshot",
    "IRNode",
    "IREdge",
    "IROperation",
    "SnapshotStatus",
    # Conversation
    "Conversation",
    "ConversationBranch",
    "Message",
    "ConversationMode",
    "ConversationStatus",
    "MessageRole",
    # Artifact
    "Artifact",
    "ArtifactVersion",
    "ArtifactStatus",
    # Execution & Audit
    "JobRun",
    "AgentRun",
    "LeaseLock",
    "CostLedger",
    "AuditEvent",
    "RunStatus",
    # Approval
    "ApprovalRecord",
    "ApprovalAction",
    # Template
    "ProjectTemplate",
    "TemplateCategory",
    # User API Key & Model Preference
    "UserApiKey",
    "UserModelPreference",
    # Usage
    "UsageRecord",
]
