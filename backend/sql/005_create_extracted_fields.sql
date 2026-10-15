--TABLE 1: Extraction runs
-- When and how a document was processed
CREATE TABLE IF NOT EXISTS extraction_runs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    solicitation_id BIGINT NOT NULL
        REFERENCES solicitations(id)
        ON DELETE CASCADE,

    document_version_id BIGINT
        REFERENCES document_versions(id)
        ON DELETE SET NULL,

    extractor_name TEXT NOT NULL,
    extractor_version TEXT,

    run_status TEXT NOT NULL DEFAULT 'pending',

    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,

    error_message TEXT,

    CONSTRAINT extraction_runs_status_check
        CHECK (
            run_status IN (
                'pending',
                'running',
                'completed',
                'failed'
            )
        ),

    CONSTRAINT extraction_runs_time_check
        CHECK (
            completed_at IS NULL
            OR completed_at >= started_at
        )
);

--TABLE 2: Extracted fields
-- Stores AI's original answer and human review results
CREATE TABLE IF NOT EXISTS extracted_fields (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    extraction_run_id BIGINT NOT NULL
        REFERENCES extraction_runs(id)
        ON DELETE CASCADE,

    field_name TEXT NOT NULL,

    --Supports strings, numbers, string dates, booleans, arrays, structured objects
    extracted_value JSONB NOT NULL,

    --Stored between 0 and 1
    confidence_score NUMERIC(5,4),

    review_status TEXT NOT NULL DEFAULT 'pending',

    --Human reviewed value, if corrected
    reviewed_value JSONB,

    reviewed_by TEXT,
    reviewed_at TIMESTAMPTZ,
    review_notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT extracted_fields_confidence_check
        CHECK (
            confidence_score IS NULL
            OR confidence_score BETWEEN 0 AND 1
        ),
    CONSTRAINT extracted_fields_review_status_check
        CHECK (
            review_status IN (
                'pending',
                'approved',
                'corrected',
                'rejected'
            )
        ),
    
    CONSTRAINT extracted_fields_review_consistency_check
        CHECK (
            review_status = 'pending'
            OR (reviewed_by IS NOT NULL AND reviewed_at IS NOT NULL)
        ),

    CONSTRAINT extracted_fields_correction_check
        CHECK (
            review_status <> 'corrected'
            OR reviewed_value IS NOT NULL
        )
);

--TABLE 3: Evidence supporting extracted fields
--Can have multiple supporting passages
CREATE TABLE IF NOT EXISTS extracted_field_evidence (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    extracted_field_id BIGINT NOT NULL
        REFERENCES extracted_fields(id)
        ON DELETE CASCADE,

    document_version_id BIGINT NOT NULL
        REFERENCES document_versions(id),

    page_number INTEGER,

    evidence_text TEXT NOT NULL,

    --Location info for highlighting purposes
    location_metadata JSONB,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT extracted_evidence_page_check
        CHECK (
            page_number IS NULL
            OR page_number > 0
        )
);

--Indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_extraction_runs_solicitation
    ON extraction_runs (solicitation_id);

CREATE INDEX IF NOT EXISTS idx_extractions_runs_document_version
    ON extraction_runs (document_version_id);

CREATE INDEX IF NOT EXISTS idx_extracted_fields_run
    ON extracted_fields (extraction_run_id);

CREATE INDEX IF NOT EXISTS idx_extracted_fields_name
    ON extracted_fields (field_name);

CREATE INDEX IF NOT EXISTS idx_extracted_fields_review_status
    ON extracted_fields (review_status);

CREATE INDEX IF NOT EXISTS idx_extracted_evidence_field
    ON extracted_field_evidence (extracted_field_id);

CREATE INDEX IF NOT EXISTS idx_extracted_evidence_document_version
    ON extracted_field_evidence (document_version_id);