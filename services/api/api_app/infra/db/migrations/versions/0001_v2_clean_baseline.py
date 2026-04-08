"""V2 全量 baseline 迁移 — 全新数据模型。

Revision ID: 0001_v2_baseline
Revises:
Create Date: 2026-04-08
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0001_v2_baseline"
down_revision = None
branch_labels = None
depends_on = None

# ── 枚举定义 ──────────────────────────────────────────────────────────

user_status = postgresql.ENUM("active", "disabled", name="user_status", create_type=False)
project_status = postgresql.ENUM("active", "archived", "deleted", name="project_status", create_type=False)
conversation_mode = postgresql.ENUM("chat", "delegated", name="conversation_mode", create_type=False)
conversation_status = postgresql.ENUM("active", "archived", name="conversation_status", create_type=False)
message_role = postgresql.ENUM("user", "assistant", "system", name="message_role", create_type=False)
run_status = postgresql.ENUM(
    "pending", "running", "completed", "failed", "needs_attention", "waiting_approval",
    name="run_status", create_type=False,
)
template_category = postgresql.ENUM(
    "saas", "api", "landing", "dashboard", "other",
    name="template_category", create_type=False,
)


def upgrade() -> None:
    # ── 创建枚举类型 ──────────────────────────────────────────────────
    user_status.create(op.get_bind(), checkfirst=True)
    project_status.create(op.get_bind(), checkfirst=True)
    conversation_mode.create(op.get_bind(), checkfirst=True)
    conversation_status.create(op.get_bind(), checkfirst=True)
    message_role.create(op.get_bind(), checkfirst=True)
    run_status.create(op.get_bind(), checkfirst=True)
    template_category.create(op.get_bind(), checkfirst=True)

    # ── users ─────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(100), nullable=True),
        sa.Column("status", user_status, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )

    # ── projects ──────────────────────────────────────────────────────
    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", project_status, nullable=False, server_default="active"),
        sa.Column("project_type", sa.String(20), nullable=False, server_default="homework"),
        sa.Column("course_name", sa.String(100), nullable=True),
        sa.Column("tech_requirements", sa.Text(), nullable=True),
        sa.Column("deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("advisor_name", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_projects_user_id", "projects", ["user_id"])

    # ── conversations ─────────────────────────────────────────────────
    op.create_table(
        "conversations",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(300), nullable=True),
        sa.Column("mode", conversation_mode, nullable=False),
        sa.Column("summary", sa.Text(), nullable=True),
        sa.Column("status", conversation_status, nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
    )
    op.create_index("ix_conversations_project_id", "conversations", ["project_id"])

    # ── messages ──────────────────────────────────────────────────────
    op.create_table(
        "messages",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("conversation_id", sa.UUID(), nullable=False),
        sa.Column("role", message_role, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("content_type", sa.String(50), nullable=False, server_default="text"),
        sa.Column("tool_calls", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("artifacts_created", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("provider", sa.String(100), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_cost", sa.Numeric(12, 6), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"]),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"])

    # ── artifacts ─────────────────────────────────────────────────────
    op.create_table(
        "artifacts",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("artifact_type", sa.String(30), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("file_path", sa.String(500), nullable=True),
        sa.Column("language", sa.String(30), nullable=True),
        sa.Column("version_num", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("parent_id", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_id"], ["artifacts.id"]),
    )
    op.create_index("ix_artifacts_project_id", "artifacts", ["project_id"])

    # ── artifact_exports ──────────────────────────────────────────────
    op.create_table(
        "artifact_exports",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("export_type", sa.String(10), nullable=False),
        sa.Column("file_url", sa.String(1000), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_artifact_exports_project_id", "artifact_exports", ["project_id"])

    # ── job_runs ──────────────────────────────────────────────────────
    op.create_table(
        "job_runs",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("job_type", sa.String(100), nullable=False),
        sa.Column("status", run_status, nullable=False, server_default="pending"),
        sa.Column("input_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
    )
    op.create_index("ix_job_runs_project_id", "job_runs", ["project_id"])

    # ── agent_runs ────────────────────────────────────────────────────
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("job_run_id", sa.UUID(), nullable=False),
        sa.Column("agent_name", sa.String(100), nullable=False),
        sa.Column("model", sa.String(100), nullable=True),
        sa.Column("provider", sa.String(100), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_cost", sa.Numeric(12, 6), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("status", run_status, nullable=False, server_default="pending"),
        sa.Column("input_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("output_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["job_run_id"], ["job_runs.id"]),
    )
    op.create_index("ix_agent_runs_job_run_id", "agent_runs", ["job_run_id"])

    # ── cost_ledger ───────────────────────────────────────────────────
    op.create_table(
        "cost_ledger",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("agent_run_id", sa.UUID(), nullable=True),
        sa.Column("model", sa.String(100), nullable=False),
        sa.Column("provider", sa.String(100), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False),
        sa.Column("completion_tokens", sa.Integer(), nullable=False),
        sa.Column("total_cost", sa.Numeric(12, 6), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"]),
    )
    op.create_index("ix_cost_ledger_project_id", "cost_ledger", ["project_id"])

    # ── audit_events ──────────────────────────────────────────────────
    op.create_table(
        "audit_events",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("event_type", sa.String(100), nullable=False),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
    )
    op.create_index("ix_audit_events_project_id", "audit_events", ["project_id"])
    op.create_index("ix_audit_events_user_id", "audit_events", ["user_id"])

    # ── project_templates ─────────────────────────────────────────────
    op.create_table(
        "project_templates",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("category", template_category, nullable=False),
        sa.Column("snapshot_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_by", sa.UUID(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
    )

    # ── user_api_keys ─────────────────────────────────────────────────
    op.create_table(
        "user_api_keys",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("encrypted_key", sa.Text(), nullable=False),
        sa.Column("masked_key", sa.String(100), nullable=False, server_default="***"),
        sa.Column("display_label", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("is_valid", sa.Boolean(), nullable=True),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )

    # ── user_model_preferences ────────────────────────────────────────
    op.create_table(
        "user_model_preferences",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("reasoning_model", sa.String(200), nullable=True),
        sa.Column("generation_model", sa.String(200), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id"),
    )

    # ── usage_records ─────────────────────────────────────────────────
    op.create_table(
        "usage_records",
        sa.Column("id", sa.UUID(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False),
        sa.Column("model", sa.String(200), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_cost", sa.Numeric(12, 6), nullable=False, server_default="0"),
        sa.Column("key_source", sa.String(20), nullable=False, server_default="user"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="SET NULL"),
    )


def downgrade() -> None:
    # 按创建的逆序删除表
    op.drop_table("usage_records")
    op.drop_table("user_model_preferences")
    op.drop_table("user_api_keys")
    op.drop_table("project_templates")
    op.drop_table("audit_events")
    op.drop_table("cost_ledger")
    op.drop_table("agent_runs")
    op.drop_table("job_runs")
    op.drop_table("artifact_exports")
    op.drop_table("artifacts")
    op.drop_table("messages")
    op.drop_table("conversations")
    op.drop_table("projects")
    op.drop_table("users")

    # 删除枚举类型
    template_category.drop(op.get_bind(), checkfirst=True)
    run_status.drop(op.get_bind(), checkfirst=True)
    message_role.drop(op.get_bind(), checkfirst=True)
    conversation_status.drop(op.get_bind(), checkfirst=True)
    conversation_mode.drop(op.get_bind(), checkfirst=True)
    project_status.drop(op.get_bind(), checkfirst=True)
    user_status.drop(op.get_bind(), checkfirst=True)
