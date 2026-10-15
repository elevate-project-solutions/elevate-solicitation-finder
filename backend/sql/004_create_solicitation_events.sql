--TABLE 1: Events and procurement milestones
CREATE TABLE IF NOT EXISTS solicitation_events (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    solicitation_id BIGINT NOT NULL
        REFERENCES solicitations(id)
        ON DELETE CASCADE,

    event_type TEXT NOT NULL,
    title TEXT NOT NULL,

    starts_at TIMESTAMPTZ,
    ends_at TIMESTAMPTZ,

    timezone_name TEXT,
    location TEXT,

    event_status TEXT NOT NULL DEFAULT 'scheduled',

    source_addendum_id BIGINT
        REFERENCES solicitation_addenda(id)
        ON DELETE SET NULL,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT solicitation_events_type_check
        CHECK (
            event_type IN (
                'publication',
                'pre_bid_conference',
                'site_visit',
                'questions_deadline',
                'registration_deadline',
                'submission_deadline',
                'bid_opening',
                'award',
                'other'
            )
        ),

    CONSTRAINT solicitation_events_status_check
        CHECK (
            event_status IN (
                'scheduled',
                'rescheduled',
                'cancelled',
                'completed'
            )
        ),
    CONSTRAINT solicitation_events_time_check
        CHECK (
            ends_at IS NULL
            OR starts_at IS NULL
            OR ends_at >= starts_at
        )
);

--TABLE 2: Attendance and registration requirements
CREATE TABLE IF NOT EXISTS solicitation_event_requirements (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    event_id BIGINT NOT NULL UNIQUE
        REFERENCES solicitation_events(id)
        ON DELETE CASCADE,

    attendance_requirement TEXT NOT NULL DEFAULT 'unknown',

    registration_required BOOLEAN,
    registration_deadline TIMESTAMPTZ,

    attendance_confirmed BOOLEAN,

    requirement_notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT event_attendance_requirement_check
        CHECK (
            attendance_requirement IN (
                'mandatory',
                'optional',
                'unknown',
                'not_applicable'
            )
        )
);

--Indexes for event searches and deadline filtering
CREATE INDEX IF NOT EXISTS idx_events_solicitation
    ON solicitation_events (solicitation_id);

CREATE INDEX IF NOT EXISTS idx_events_starts_at
    ON solicitation_events (starts_at);

CREATE INDEX IF NOT EXISTS idx_events_type
    ON solicitation_events (event_type);

CREATE INDEX IF NOT EXISTS idx_event_requirements_attendance
    ON solicitation_event_requirements (attendance_requirement);