-- TABLE 1: Procurement platforms
CREATE TABLE IF NOT EXISTS solicitation_sources (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    name TEXT NOT NULL,
    source_key TEXT NOT NULL UNIQUE,
    base_url TEXT NOT NULL,

    is_active BOOLEAN NOT NULL DEFAULT TRUE,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- TABLE 2: References to external procurement listings
CREATE TABLE IF NOT EXISTS solicitation_external_refs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    --Only accepts IDs in solicitations table
    solicitation_id BIGINT NOT NULL
        REFERENCES solicitations(id)
        --If deleted, will not lose procurement history accidentally
        ON DELETE CASCADE,

    source_id BIGINT NOT NULL
        REFERENCES solicitation_sources(id),

    external_id TEXT,
    external_url TEXT NOT NULL,

    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW (),

    CONSTRAINT external_refs_source_url_unique
        UNIQUE (source_id, external_url)
);

--Prevents duplicate portal IDs when and external ID exists
CREATE UNIQUE INDEX IF NOT EXISTS idx_external_refs_source_external_id
    ON solicitation_external_refs (source_id, external_id)
    WHERE external_id IS NOT NULL;

-- Efficiently finds all references for a solicitation
CREATE INDEX IF NOT EXISTS idx_external_refs_solicitation
    ON solicitation_external_refs (solicitation_id);

-- Efficiently finds all references from a source
CREATE INDEX IF NOT EXISTS idx_external_refs_sources
    ON solicitation_external_refs (source_id);