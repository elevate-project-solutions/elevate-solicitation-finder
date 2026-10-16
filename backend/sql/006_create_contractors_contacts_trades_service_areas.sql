--Table 1: Contractors
CREATE TABLE IF NOT EXISTS contractors (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    company_name TEXT NOT NULL,
    website TEXT,
    phone TEXT,
    email TEXT,

    city TEXT,
    state_code TEXT,
    country_code TEXT NOT NULL DEFAULT 'US',

    relationship_status TEXT NOT NULL DEFAULT 'lead',

    minimum_project_value NUMERIC(15,2),
    maximum_project_value NUMERIC(15,2),

    bonding_capacity NUMERIC(15,2),

    notes TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT contractors_relationship_status_check
        CHECK (
            relationship_status IN (
                'lead',
                'prospect',
                'active_client',
                'inactive',
                'archived'
            )
        ),

    CONSTRAINT contractors_project_value_check
        CHECK (
            minimum_project_value IS NULL
            OR maximum_project_value IS NULL
            OR minimum_project_value <= maximum_project_value
        ),

    CONSTRAINT contractors_nonnegative_values_check
        CHECK (
            (minimum_project_value IS NULL OR minimum_project_value >= 0)
            AND (maximum_project_value IS NULL OR maximum_project_value >= 0)
            AND (bonding_capacity IS NULL OR bonding_capacity >= 0)
        )
);

--TABLE 2: COntractor contacts
CREATE TABLE IF NOT EXISTS contractor_contacts (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    contractor_id BIGINT NOT NULL
        REFERENCES contractors(id)
        ON DELETE CASCADE,

    first_name TEXT NOT NULL,
    last_name TEXT,

    job_title TEXT,
    email TEXT,
    phone TEXT,

    is_primary BOOLEAN NOT NULL DEFAULT FALSE,

    notes TEXT,
    
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--Allows one primary contact per contractor.
CREATE UNIQUE INDEX IF NOT EXISTS
    idx_contractor_contacts_one_primary
ON contractor_contacts (contractor_id)
WHERE is_primary = TRUE;

--TABLE 3: Trades
CREATE TABLE IF NOT EXISTS trades (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    
    trade_name TEXT NOT NULL UNIQUE,
    description TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

--TABLE 4: Contractor-to-trade relationships
CREATE TABLE IF NOT EXISTS contractor_trades (
    contractor_id BIGINT NOT NULL
        REFERENCES contractors(id)
        ON DELETE CASCADE,

    trade_id BIGINT NOT NULL
        REFERENCES trades(id),

    capability_notes TEXT,

    is_primary_trade BOOLEAN NOT NULL DEFAULT FALSE,

    PRIMARY KEY (contractor_id, trade_id)
);

--TABLE 5: Geographic service areas
CREATE TABLE IF NOT EXISTS service_areas (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    area_name TEXT NOT NULL,

    area_type TEXT NOT NULL,

    state_code TEXT,
    country_code TEXT NOT NULL DEFAULT 'US',

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT service_areas_type_check
        CHECK (
            area_type IN (
                'city',
                'county',
                'metro',
                'region',
                'state',
                'nationwide'
            )
        ),

    CONSTRAINT service_areas_unique
        UNIQUE (area_name, area_type, state_code)
);

--TABLE 6: Contractor to service area relationships
CREATE TABLE IF NOT EXISTS contractor_service_areas (
    contractor_id BIGINT NOT NULL
        REFERENCES contractors(id)
        ON DELETE CASCADE,

    service_area_id BIGINT NOT NULL
        REFERENCES service_areas(id),

    service_priority TEXT NOT NULL DEFAULT 'primary',

    travel_notes TEXT,

    PRIMARY KEY (contractor_id, service_area_id),

    CONSTRAINT contractor_service_priority_check
        CHECK (
            service_priority IN (
                'primary',
                'secondary',
                'opportunistic'
            )
        )
);

--Indexes
CREATE INDEX IF NOT EXISTS idx_contractors_relationship_status
    ON contractors (relationship_status);

CREATE INDEX IF NOT EXISTS idx_contractor_contacts_contractor
    ON contractor_contacts (contractor_id);

CREATE INDEX IF NOT EXISTS idx_contractor_trades_trade
    ON contractor_trades (trade_id);

CREATE INDEX IF NOT EXISTS idx_service_areas_type_state
    ON service_areas (area_type, state_code);

CREATE INDEX IF NOT EXISTS idx_contractor_service_areas_area
    ON contractor_service_areas (service_area_id);