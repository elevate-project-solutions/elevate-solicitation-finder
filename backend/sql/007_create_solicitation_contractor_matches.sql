--TABLE 1: Solicitation to contractor matches
CREATE TABLE IF NOT EXISTS solicitation_contractor_matches (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    solicitation_id BIGINT NOT NULL
        REFERENCES solicitations(id)
        ON DELETE CASCADE,

    contractor_id BIGINT NOT NULL
        REFERENCES contractors(id)
        ON DELETE CASCADE,

    match_score NUMERIC(5,4),

    match_status TEXT NOT NULL DEFAULT 'pending',

    review_status TEXT NOT NULL DEFAULT 'pending',

    match_summary TEXT,

    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,

    matched_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT solicitation_contractor_match_unique
        UNIQUE (solicitation_id, contractor_id),

    CONSTRAINT solicitation_contractor_match_score_check
        CHECK (
            match_score IS NULL
            OR match_score BETWEEN 0 AND 1
        ),

    CONSTRAINT solicitation_contractor_match_status_check
        CHECK (
            match_status IN (
                'pending',
                'strong_match',
                'possible_match',
                'poor_match',
                'disqualified'
            )
        ),

    CONSTRAINT solicitation_contractor_review_status_check
        CHECK(
            review_status IN (
                'pending',
                'approved',
                'rejected',
                'needs_information'
            )
        ),

    CONSTRAINT solicitation_contractor_review_consistency_check
        CHECK (
            review_status = 'pending'
            OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL)
        )
);

--TABLE 2: Individual match factors
CREATE TABLE IF NOT EXISTS solicitation_match_factors (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    match_id BIGINT NOT NULL
        REFERENCES solicitation_contractor_matches(id)
        ON DELETE CASCADE,

    factor_type TEXT NOT NULL,

    factor_status TEXT NOT NULL DEFAULT 'unknown',

    factor_score NUMERIC(5,4),

    explanation TEXT,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT solicitation_match_factor_unique
        UNIQUE (match_id, factor_type),

    CONSTRAINT solicitation_match_factor_type_check
        CHECK (
            factor_type IN (
                'trade',
                'project_size',
                'service_area',
                'bonding',
                'mandatory_event',
                'experience',
                'certification',
                'other'
            )
        ),

    CONSTRAINT solicitation_match_factor_status_check
        CHECK (
            factor_status IN (
                'match',
                'partial_match',
                'no_match',
                'unknown'
            )
        ),

    CONSTRAINT solicitation_match_factor_score_check
        CHECK (
            factor_score IS NULL
            OR factor_score BETWEEN 0 AND 1
        )
);

--Creates indexes for queries

CREATE INDEX IF NOT EXISTS idx_matches_solicitation
    ON solicitation_contractor_matches (solicitation_id);

CREATE INDEX IF NOT EXISTS idx_matches_contractor
    ON solicitation_contractor_matches(contractor_id);

CREATE INDEX IF NOT EXISTS idx_matches_status
    ON solicitation_contractor_matches (match_status);

CREATE INDEX IF NOT EXISTS idx_matches_score
    ON solicitation_contractor_matches (match_score DESC);

CREATE INDEX IF NOT EXISTS idx_match_factors_match
    ON solicitation_match_factors (match_id);

CREATE INDEX IF NOT EXISTS idx_match_factors_type
    ON solicitation_match_factors (factor_type);