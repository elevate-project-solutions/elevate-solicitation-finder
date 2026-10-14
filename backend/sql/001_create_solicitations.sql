-- creates table only if it doesn't exist
CREATE TABLE IF NOT EXISTS solicitations (
    --gives each solicitation its own id
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    -- required values
    source TEXT NOT NULL,
    agency TEXT NOT NULL,
    title TEXT NOT NULL,
    solicitation_number TEXT,

    published_at TIMESTAMPTZ,
    due_at TIMESTAMPTZ,

    source_url TEXT NOT NULL,

    status TEXT NOT NULL DEFAULT 'unknown',

    --records time row is inserted
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    -- currently does not update automatically when there are changes. Will implement later
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT solicitations_status_check
        --prevents unsupported status values
        CHECK (
            status IN (
                'unknown',
                'open',
                'closed',
                'cancelled',
                'awarded'
            )
        ),

    CONSTRAINT solicitations_source_url_unique
        --prevents repeat URLs
        UNIQUE (source_url)
);

--makes for more efficient searches and filters
CREATE INDEX IF NOT EXISTS idx_solicitations_due_at
    ON solicitations (due_at);

CREATE INDEX IF NOT EXISTS idx_solicitations_status
    ON solicitations (status);

CREATE INDEX IF NOT EXISTS idx_solicitations_source
    ON solicitations (source);