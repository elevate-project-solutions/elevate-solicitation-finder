--Reviews duplicate candidates
CREATE TABLE IF NOT EXISTS solicitation_duplicate_candidates (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    solicitation_id_1 BIGINT NOT NULL
        REFERENCES solicitations(id)
        ON DELETE CASCADE,

    solicitation_id_2 BIGINT NOT NULL
        REFERENCES solicitations(id)
        ON DELETE CASCADE,

    match_reason TEXT NOT NULL,

    confidence_score NUMERIC(5,4),

    review_status TEXT NOT NULL DEFAULT 'pending',

    reviewed_by BIGINT
        REFERENCES app_users(id)
        ON DELETE SET NULL,

    reviewed_at TIMESTAMPTZ,

    review_notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT duplicate_candidates_different_records
        CHECK (solicitation_id_1 < solicitation_id_2),

    CONSTRAINT duplicate_candidates_unique_pair
        UNIQUE (solicitation_id_1, solicitation_id_2),

    CONSTRAINT duplicate_candidates_confidence_check
        CHECK (
            confidence_score IS NULL
            OR confidence_score BETWEEN 0 AND 1
        ),

    CONSTRAINT duplicate_candidates_status_check
        CHECK (
            review_status IN (
                'pending',
                'confirmed_duplicate',
                'not_duplicate'
            )
        )
);

CREATE INDEX IF NOT EXISTS idx_duplicate_candidates_status
    ON solicitation_duplicate_candidates (review_status);

CREATE INDEX IF NOT EXISTS idx_duplicate_candidates_second
    ON solicitation_duplicate_candidates (solicitation_id_2);