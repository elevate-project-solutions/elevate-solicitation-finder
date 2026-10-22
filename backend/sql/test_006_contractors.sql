--Fictional data is removed by ROLLBACK

BEGIN;

--Creates fictional contractor
INSERT INTO contractors (
    company_name,
    city,
    state_code,
    relationship_status,
    minimum_project_value,
    maximum_project_value
)

VALUES (
    'TEST - Lone Star Siteworks',
    'Dallas',
    'TX',
    'prospect',
    10000,
    100000
);

--Creates fictional primary contact
INSERT INTO contractor_contacts (
    contractor_id,
    first_name,
    last_name,
    job_title,
    is_primary
)

SELECT
    id,
    'Alex',
    'Test',
    'Owner',
    TRUE
FROM contractors
WHERE company_name = 'TEST - Lone Star Siteworks';

--Creates fictional trade
INSERT INTO trades (trade_name, description)
VALUES (
    'TEST - Site Preparation',
    'Land clearing, grading, and earthwork'
)
ON CONFLICT (trade_name) DO NOTHING;

--Connects contractor to trade
INSERT INTO contractor_trades (
    contractor_id,
    trade_id,
    capability_notes,
    is_primary_trade
)

SELECT
    c.id,
    t.id,
    'Commercial site preparation and grading',
    TRUE
FROM contractors AS c
CROSS JOIN trades AS t
WHERE c.company_name = 'TEST - Lone Star Siteworks'
AND t.trade_name = 'TEST - Site Preparation';

--Creates a service area
INSERT INTO service_areas (
    area_name,
    area_type,
    state_code
)

VALUES (
    'Dallas County',
    'county',
    'TX'
)

ON CONFLICT DO NOTHING;

--Connects contractor to their service area
INSERT INTO contractor_service_areas (
    contractor_id,
    service_area_id,
    service_priority
)

SELECT
    c.id,
    sa.id,
    'primary'
FROM contractors AS c
CROSS JOIN service_areas AS sa
WHERE c.company_name = 'TEST - Lone Star Siteworks'
AND sa.area_name = 'Dallas County'
AND sa.area_type = 'county'
AND sa.state_code = 'TX';

--Verifies the relationship
SELECT
    c.company_name,
    cc.first_name AS contact,
    t.trade_name,
    sa.area_name AS service_area,
    c.relationship_status
FROM contractors AS c
JOIN contractor_contacts AS cc
    ON cc.contractor_id = c.id
JOIN contractor_trades AS ct
    ON ct.contractor_id = c.id
JOIN trades AS t
    ON t.id = ct.trade_id
JOIN contractor_service_areas AS csa
    ON csa.contractor_id = c.id
JOIN service_areas AS sa
    ON sa.id = csa.service_area_id
WHERE c.company_name = 'TEST - Lone Star Siteworks';

--Removes test data
ROLLBACK;