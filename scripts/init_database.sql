-- ============================================================================
-- VibeArtifact v2 数据库初始化脚本
-- 重构后全量建表（对应 Alembic revision: 0001_v2_baseline）
--
-- 目标数据库：PostgreSQL 15+
-- 使用方式：
--   1. 创建数据库：CREATE DATABASE vibeartifact;
--   2. 连接数据库后执行本脚本：psql -U vibe -d vibeartifact -f init_database.sql
--
-- 表结构概览（14 张表）：
--   核心业务：users, projects, conversations, messages, artifacts, artifact_exports
--   执行审计：job_runs, agent_runs, cost_ledger, audit_events
--   用户配置：user_api_keys, user_model_preferences, usage_records
--   内容模板：project_templates
-- ============================================================================

BEGIN;

-- ============================================================================
-- 0. 扩展
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";  -- 提供 gen_random_uuid()

-- ============================================================================
-- 1. 枚举类型（7 个）
-- ============================================================================

DO $$ BEGIN
    CREATE TYPE user_status AS ENUM ('active', 'disabled');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE project_status AS ENUM ('active', 'archived', 'deleted');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE conversation_mode AS ENUM ('chat', 'delegated');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE conversation_status AS ENUM ('active', 'archived');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE message_role AS ENUM ('user', 'assistant', 'system');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE run_status AS ENUM (
        'pending', 'running', 'completed', 'failed',
        'needs_attention', 'waiting_approval'
    );
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

DO $$ BEGIN
    CREATE TYPE template_category AS ENUM ('saas', 'api', 'landing', 'dashboard', 'other');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- ============================================================================
-- 2. 核心业务表
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 2.1 users - 用户账户表
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS users (
    id          UUID        NOT NULL DEFAULT gen_random_uuid(),
    email       VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    display_name VARCHAR(100),
    status      user_status NOT NULL DEFAULT 'active',
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT pk_users PRIMARY KEY (id),
    CONSTRAINT uq_users_email UNIQUE (email)
);

-- ---------------------------------------------------------------------------
-- 2.2 projects - 项目表
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS projects (
    id               UUID          NOT NULL DEFAULT gen_random_uuid(),
    user_id          UUID          NOT NULL,
    name             VARCHAR(200)  NOT NULL,
    description      TEXT,
    status           project_status NOT NULL DEFAULT 'active',
    project_type     VARCHAR(20)   NOT NULL DEFAULT 'homework',
    course_name      VARCHAR(100),
    tech_requirements TEXT,
    deadline         TIMESTAMPTZ,
    advisor_name     VARCHAR(100),
    created_at       TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT pk_projects PRIMARY KEY (id),
    CONSTRAINT fk_projects_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS ix_projects_user_id ON projects(user_id);

-- ---------------------------------------------------------------------------
-- 2.3 conversations - 对话表
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS conversations (
    id          UUID                NOT NULL DEFAULT gen_random_uuid(),
    project_id  UUID                NOT NULL,
    title       VARCHAR(300),
    mode        conversation_mode   NOT NULL,
    summary     TEXT,
    status      conversation_status NOT NULL DEFAULT 'active',
    created_at  TIMESTAMPTZ         NOT NULL DEFAULT now(),
    updated_at  TIMESTAMPTZ         NOT NULL DEFAULT now(),

    CONSTRAINT pk_conversations PRIMARY KEY (id),
    CONSTRAINT fk_conversations_project FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX IF NOT EXISTS ix_conversations_project_id ON conversations(project_id);

-- ---------------------------------------------------------------------------
-- 2.4 messages - 消息表
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS messages (
    id                UUID          NOT NULL DEFAULT gen_random_uuid(),
    conversation_id   UUID          NOT NULL,
    role              message_role  NOT NULL,
    content           TEXT          NOT NULL,
    content_type      VARCHAR(50)   NOT NULL DEFAULT 'text',
    -- 工具调用记录（JSON）
    tool_calls        JSONB,
    -- 本轮消息产生的产物 ID 列表
    artifacts_created JSONB,
    -- LLM 调用元数据
    model             VARCHAR(100),
    provider          VARCHAR(100),
    prompt_tokens     INTEGER,
    completion_tokens INTEGER,
    total_cost        NUMERIC(12,6),
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT pk_messages PRIMARY KEY (id),
    CONSTRAINT fk_messages_conversation FOREIGN KEY (conversation_id)
        REFERENCES conversations(id)
);

CREATE INDEX IF NOT EXISTS ix_messages_conversation_id ON messages(conversation_id);

-- ---------------------------------------------------------------------------
-- 2.5 artifacts - 产物表（通过 parent_id 自引用形成版本链）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS artifacts (
    id            UUID          NOT NULL DEFAULT gen_random_uuid(),
    project_id    UUID          NOT NULL,
    artifact_type VARCHAR(30)   NOT NULL,
    title         VARCHAR(255)  NOT NULL,
    content       TEXT          NOT NULL,
    file_path     VARCHAR(500),
    language      VARCHAR(30),
    version_num   INTEGER       NOT NULL DEFAULT 1,
    -- 父版本 ID，同一产物链上通过此字段回溯
    parent_id     UUID,
    created_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT pk_artifacts PRIMARY KEY (id),
    CONSTRAINT fk_artifacts_project FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE,
    CONSTRAINT fk_artifacts_parent FOREIGN KEY (parent_id)
        REFERENCES artifacts(id)
);

CREATE INDEX IF NOT EXISTS ix_artifacts_project_id ON artifacts(project_id);

-- ---------------------------------------------------------------------------
-- 2.6 artifact_exports - 产物导出记录表
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS artifact_exports (
    id              UUID          NOT NULL DEFAULT gen_random_uuid(),
    project_id      UUID          NOT NULL,
    export_type     VARCHAR(10)   NOT NULL,   -- zip / pdf
    file_url        VARCHAR(1000),
    file_size_bytes BIGINT,
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT pk_artifact_exports PRIMARY KEY (id),
    CONSTRAINT fk_artifact_exports_project FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_artifact_exports_project_id ON artifact_exports(project_id);

-- ============================================================================
-- 3. 执行与审计表
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 3.1 job_runs - Celery 任务运行记录
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS job_runs (
    id             UUID        NOT NULL DEFAULT gen_random_uuid(),
    project_id     UUID        NOT NULL,
    job_type       VARCHAR(100) NOT NULL,
    status         run_status  NOT NULL DEFAULT 'pending',
    input_payload  JSONB,
    output_payload JSONB,
    error_message  TEXT,
    started_at     TIMESTAMPTZ,
    completed_at   TIMESTAMPTZ,
    created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),

    CONSTRAINT pk_job_runs PRIMARY KEY (id),
    CONSTRAINT fk_job_runs_project FOREIGN KEY (project_id) REFERENCES projects(id)
);

CREATE INDEX IF NOT EXISTS ix_job_runs_project_id ON job_runs(project_id);

-- ---------------------------------------------------------------------------
-- 3.2 agent_runs - Agent/LLM 调用记录
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS agent_runs (
    id                UUID          NOT NULL DEFAULT gen_random_uuid(),
    job_run_id        UUID          NOT NULL,
    agent_name        VARCHAR(100)  NOT NULL,
    model             VARCHAR(100),
    provider          VARCHAR(100),
    prompt_tokens     INTEGER,
    completion_tokens INTEGER,
    total_cost        NUMERIC(12,6),
    latency_ms        INTEGER,
    status            run_status    NOT NULL DEFAULT 'pending',
    input_payload     JSONB,
    output_payload    JSONB,
    error_message     TEXT,
    started_at        TIMESTAMPTZ,
    completed_at      TIMESTAMPTZ,
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT pk_agent_runs PRIMARY KEY (id),
    CONSTRAINT fk_agent_runs_job FOREIGN KEY (job_run_id) REFERENCES job_runs(id)
);

CREATE INDEX IF NOT EXISTS ix_agent_runs_job_run_id ON agent_runs(job_run_id);

-- ---------------------------------------------------------------------------
-- 3.3 cost_ledger - 成本账本
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS cost_ledger (
    id                UUID          NOT NULL DEFAULT gen_random_uuid(),
    project_id        UUID          NOT NULL,
    agent_run_id      UUID,
    model             VARCHAR(100)  NOT NULL,
    provider          VARCHAR(100)  NOT NULL,
    prompt_tokens     INTEGER       NOT NULL,
    completion_tokens INTEGER       NOT NULL,
    total_cost        NUMERIC(12,6) NOT NULL,
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT pk_cost_ledger PRIMARY KEY (id),
    CONSTRAINT fk_cost_ledger_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT fk_cost_ledger_agent_run FOREIGN KEY (agent_run_id) REFERENCES agent_runs(id)
);

CREATE INDEX IF NOT EXISTS ix_cost_ledger_project_id ON cost_ledger(project_id);

-- ---------------------------------------------------------------------------
-- 3.4 audit_events - 审计事件表
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS audit_events (
    id          UUID          NOT NULL DEFAULT gen_random_uuid(),
    project_id  UUID,
    user_id     UUID,
    event_type  VARCHAR(100)  NOT NULL,
    payload     JSONB,
    created_at  TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT pk_audit_events PRIMARY KEY (id),
    CONSTRAINT fk_audit_events_project FOREIGN KEY (project_id) REFERENCES projects(id),
    CONSTRAINT fk_audit_events_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS ix_audit_events_project_id ON audit_events(project_id);
CREATE INDEX IF NOT EXISTS ix_audit_events_user_id ON audit_events(user_id);

-- ============================================================================
-- 4. 内容模板
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 4.1 project_templates - 项目模板表
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS project_templates (
    id            UUID              NOT NULL DEFAULT gen_random_uuid(),
    name          VARCHAR(200)      NOT NULL,
    description   TEXT              NOT NULL,
    category      template_category NOT NULL,
    snapshot_data JSONB             NOT NULL,
    icon          VARCHAR(50),
    is_public     BOOLEAN           NOT NULL DEFAULT true,
    created_by    UUID,
    created_at    TIMESTAMPTZ       NOT NULL DEFAULT now(),
    updated_at    TIMESTAMPTZ       NOT NULL DEFAULT now(),

    CONSTRAINT pk_project_templates PRIMARY KEY (id),
    CONSTRAINT fk_templates_user FOREIGN KEY (created_by) REFERENCES users(id)
);

-- ============================================================================
-- 5. 用户配置表
-- ============================================================================

-- ---------------------------------------------------------------------------
-- 5.1 user_api_keys - 用户 LLM API 密钥（加密存储）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_api_keys (
    id                UUID          NOT NULL DEFAULT gen_random_uuid(),
    user_id           UUID          NOT NULL,
    provider          VARCHAR(50)   NOT NULL,   -- anthropic / openai / google / azure
    encrypted_key     TEXT          NOT NULL,
    masked_key        VARCHAR(100)  NOT NULL DEFAULT '***',
    display_label     VARCHAR(100),
    is_active         BOOLEAN       NOT NULL DEFAULT true,
    is_valid          BOOLEAN,                  -- NULL = 尚未验证
    last_validated_at TIMESTAMPTZ,
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT now(),
    updated_at        TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT pk_user_api_keys PRIMARY KEY (id),
    CONSTRAINT fk_user_api_keys_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uq_user_provider UNIQUE (user_id, provider)
);

-- ---------------------------------------------------------------------------
-- 5.2 user_model_preferences - 用户模型偏好（一对一）
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS user_model_preferences (
    id               UUID         NOT NULL DEFAULT gen_random_uuid(),
    user_id          UUID         NOT NULL,
    reasoning_model  VARCHAR(200),          -- 推理模型标识
    generation_model VARCHAR(200),          -- 生成模型标识
    created_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),
    updated_at       TIMESTAMPTZ  NOT NULL DEFAULT now(),

    CONSTRAINT pk_user_model_preferences PRIMARY KEY (id),
    CONSTRAINT fk_model_pref_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT uq_model_pref_user UNIQUE (user_id)
);

-- ---------------------------------------------------------------------------
-- 5.3 usage_records - LLM 用量记录
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS usage_records (
    id                UUID          NOT NULL DEFAULT gen_random_uuid(),
    user_id           UUID          NOT NULL,
    project_id        UUID,
    provider          VARCHAR(50)   NOT NULL,
    model             VARCHAR(200)  NOT NULL,
    prompt_tokens     INTEGER       NOT NULL DEFAULT 0,
    completion_tokens INTEGER       NOT NULL DEFAULT 0,
    total_cost        NUMERIC(12,6) NOT NULL DEFAULT 0,
    key_source        VARCHAR(20)   NOT NULL DEFAULT 'user',  -- user / platform
    created_at        TIMESTAMPTZ   NOT NULL DEFAULT now(),

    CONSTRAINT pk_usage_records PRIMARY KEY (id),
    CONSTRAINT fk_usage_records_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_usage_records_project FOREIGN KEY (project_id)
        REFERENCES projects(id) ON DELETE SET NULL
);

-- ============================================================================
-- 6. Alembic 版本跟踪表（使迁移工具识别当前已应用的版本）
-- ============================================================================

CREATE TABLE IF NOT EXISTS alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

INSERT INTO alembic_version (version_num)
VALUES ('0001_v2_baseline')
ON CONFLICT (version_num) DO NOTHING;

COMMIT;

-- ============================================================================
-- 完成！14 张业务表 + 1 张 Alembic 版本表 + 7 个枚举类型
--
-- 表依赖关系：
--   users
--   ├── projects
--   │   ├── conversations
--   │   │   └── messages
--   │   ├── artifacts (self-ref: parent_id)
--   │   ├── artifact_exports
--   │   ├── job_runs
--   │   │   └── agent_runs
--   │   │       └── cost_ledger
--   │   ├── audit_events
--   │   └── usage_records
--   ├── user_api_keys
--   ├── user_model_preferences
--   └── project_templates
-- ============================================================================
