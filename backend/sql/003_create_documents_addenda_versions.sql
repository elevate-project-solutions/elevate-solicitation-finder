-- TABLE 1; Logical solicitation documents
CREATE TABLE IF NOT EXISTS solicitation_documents (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    solicitation_id BIGINT NOT NULL
        REFERENCES solicitations(id)
        ON DELETE CASCADE,

    title TEXT NOT NULL,

    document_type TEXT NOT NULL DEFAULT 'other',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT solicitation_documents_type_check
        CHECK (
            document_type IN (
                'solicitation',
                'specifications',
                'drawings',
                'form',
                'addendum',
                'other'
            )
        )
);

--TABLE 2: Agency issued addenda
CREATE TABLE IF NOT EXISTS solicitation_addenda (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    solicitation_id BIGINT NOT NULL
        REFERENCES solicitations(id)
        ON DELETE CASCADE,

    addendum_number TEXT NOT NULL,
    title TEXT NOT NULL,

    issued_at TIMESTAMPTZ,
    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    
    CONSTRAINT solicitation_addenda_number_unique
        UNIQUE (solicitation_id, addendum_number),

    CONSTRAINT solicitation_addenda_id_solicitation_unique
        UNIQUE (id, solicitation_id)
);

--TABLE 3: File versions
CREATE TABLE IF NOT EXISTS document_versions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    document_id BIGINT NOT NULL
        REFERENCES solicitation_documents(id)
        ON DELETE CASCADE,

    version_number INTEGER NOT NULL,

    file_name TEXT NOT NULL,
    source_url TEXT,
    storage_key TEXT,
    sha256_hash TEXT,
    mime_type TEXT,
    file_size_bytes BIGINT,

    retrieved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT document_versions_number_positive
        CHECK (version_number > 0),

    CONSTRAINT document_versions_unique
        UNIQUE (document_id, version_number),

    CONSTRAINT document_versions_sha256_format
        CHECK (
            sha256_hash IS NULL
            OR sha256_hash ~ '^[0-9a-fA-F]{64}$'
        )
);

--TABLE 4: Connect addenda to the docs they affect
-- One addenda might affect more than one doc
CREATE TABLE IF NOT EXISTS addendum_documents (
    addendum_id BIGINT NOT NULL
        REFERENCES solicitation_addenda(id)
        ON DELETE CASCADE,

        document_id BIGINT NOT NULL
            REFERENCES solicitation_documents(id)
            ON DELETE CASCADE,

        PRIMARY KEY (addendum_id, document_id)
);

--Indexes for common lookups
CREATE INDEX IF NOT EXISTS idx_documents_solicitation
    ON solicitation_documents (solicitation_id);

CREATE INDEX IF NOT EXISTS idx_addenda_solicitation
    ON solicitation_addenda (solicitation_id);

CREATE INDEX IF NOT EXISTS idx_versions_document
    ON document_versions (document_id);

CREATE INDEX IF NOT EXISTS idx_addendum_documents_document
    ON addendum_documents (document_id);