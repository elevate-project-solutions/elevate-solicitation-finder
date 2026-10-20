--TABLE 1: Application users
CREATE TABLE IF NOT EXISTS app_users(
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    email TEXT NOT NULL,
    full_name TEXT NOT NULL,

    account_status TEXT NOT NULL DEFAULT 'invited',

    --External authentication provider identity
    auth_provider TEXT,
    auth_subject TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT app_users_status_check
        CHECK (
            account_status IN (
                'invited',
                'active',
                'suspended',
                'deactivated'
            )
        ),
    
    CONSTRAINT app_users_email_not_blank
        CHECK (length(trim(email)) > 0),

    CONSTRAINT app_users_auth_identity_unique
        UNIQUE (auth_provider, auth_subject),

    CONSTRAINT app_users_auth_identity_pair_check
        CHECK (
            (auth_provider IS NULL AND auth_subject IS NULL)
            OR(auth_provider IS NOT NULL AND auth_subject IS NOT NULL)
        )
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_app_users_email
    ON app_users (lower(email));

--TABLE 2: Roles
CREATE TABLE IF NOT EXISTS roles(
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    role_name TEXT NOT NULL UNIQUE,
    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW ()
);

--TABLE 3: User to ruole relationships
CREATE TABLE IF NOT EXISTS user_roles (
    user_id BIGINT NOT NULL
        REFERENCES app_users(id)
        ON DELETE CASCADE,

    role_id BIGINT NOT NULL
        REFERENCES roles(id)
        ON DELETE CASCADE,

    assigned_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    PRIMARY KEY (user_id, role_id)
);

--TABLE 4: Solicitation assignments
CREATE TABLE IF NOT EXISTS solicitation_assignments (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    solicitation_id BIGINT NOT NULL
        REFERENCES solicitations(id)
        ON DELETE CASCADE,

    assigned_to BIGINT NOT NULL
        REFERENCES app_users(id),

    assigned_by BIGINT
        REFERENCES app_users(id)
        ON DELETE SET NULL,

    assignment_type TEXT NOT NULL DEFAULT 'review',
    
    assignment_status TEXT NOT NULL DEFAULT 'pending',

    priority TEXT NOT NULL DEFAULT 'normal',

    due_at TIMESTAMPTZ,
    
    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT solicitation_assignment_type_check
        CHECK (
            assignment_type IN (
                'review',
                'document_analysis',
                'qualification',
                'proposal_preparation',
                'submission',
                'follow-up',
                'other'
            )
        ),

    CONSTRAINT solicitation_assignment_status_check
        CHECK (
            assignment_status IN (
                'pending',
                'in_progress',
                'blocked',
                'completed',
                'cancelled'
            )
        ),

    CONSTRAINT solicitation_assignment_priority_check
        CHECK (
            priority IN (
                'low',
                'normal',
                'high',
                'urgent'
            )
        )
);

--TABLE 5: Assignment activity
CREATE TABLE IF NOT EXISTS assignment_activity (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    assignment_id BIGINT NOT NULL
        REFERENCES solicitation_assigments(id)
        ON DELETE CASCADE,

    user_id BIGINT
        REFERENCES app_users(id)
        ON DELETE SET NULL,

    activity_type TEXT NOT NULL,

    note TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT assignment_activity_type_check
        CHECK (
            activity_type IN (
                'created',
                'status_changed',
                'comment',
                'completed',
                'reassigned',
                'other'
            )
        )
);

--TABLE 6: Audit logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    actor_user_id BIGINT
        REFERENCES app_users(id)
        ON DELETE SET NULL,

    action TEXT NOT NULL,

    entity_type TEXT NOT NULL,
    entity_id BIGINT,

    old_values JSONB,
    new_values JSONB,

    details JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT audit_logs_actions_not_blank
        CHECK (length(trim(action)) > 0),

    CONSTRAINT audit_logs_entity_type_not_blank
        CHECK (length(trim(entity_type)) > 0)
);

--Indexes
CREATE INDEX IF NOT EXISTS idx_user_roles_role
    ON user_roles (role_id);

CREATE INDEX IF NOT EXISTS idx_assignments_solicitation
    ON solicitation_assignments (solicitation_id);

CREATE INDEX IF NOT EXISTS idx_assignments_assigned_to
    ON solicitation_assignments (assigned_to);

CREATE INDEX IF NOT EXISTS idx_assignements_status
    ON solicitation_assignments (assignment_status);

CREATE INDEX IF NOT EXISTS idx_assignments_due_at
    ON solicitation_assignments (due_at);

CREATE INDEX IF NOT EXISTS idx_assignment_activity_assignment
    ON assignment_activity (assignment_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_actor
    ON audit_logs (actor_user_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_entity
    ON audit_logs (entity_type, entity_id);

CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at
    ON audit_logs (created_at DESC);