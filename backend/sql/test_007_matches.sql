--These fictional records are removed later with ROLLBACK.

BEGIN;

--Creates fictional solicitation
INSERT INTO solicitations (
    source,
    agency,
    title,
    solicitation_number,
    source_url,
    status
)

VALUES (
    'test',
    'Test City',
    'TEST - Municipal Site Preparation',
    'TEST-MATCH-001',
    'https://example.com/test-match-001',
    'open'
);

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

--Creates a match record
INSERT INTO solicitation_contractor_matches (
    solicitation_id,
    contractor_id,
    match_score,
    match_status,
    match_summary
)

SELECT
    s.id,
    c.id,
    0.8800,
    'strong_match',
    'Strong trade, project size, and service area fit.'
FROM solicitations AS s
CROSS JOIN contractors AS c
WHERE s.solicitation_number = 'TEST-MATCH-001'
AND c.company_name = 'TEST - Lone Star Siteworks';

--Adds a trade match factor
INSERT INTO solicitation_match_factors (
    match_id,
    factor_type,
    factor_status,
    factor_score,
    explanation
)

SELECT
    m.id,
    'trade',
    'match',
    1.0000,
    'Contractor performs commercial site preparation.'
FROM solicitation_contractor_matches AS m
JOIN solicitations AS s
    ON s.id = m.solicitation_id
WHERE s.solicitation_number = 'TEST-MATCH-001';

--Add a project size factor
INSERT INTO solicitation_match_factors (
    match_id,
    factor_type,
    factor_status,
    factor_score,
    explanation
)

SELECT
    m.id,
    'project_size',
    'match',
    1.0000,
    'Project value falls within contractor preferred range.'
FROM solicitation_contractor_matches AS m
JOIN solicitations AS s
    ON s.id = m.solicitation_id
WHERE s.solicitation_number = 'TEST-MATCH-001';

--Adds a unresolved bonding factor
INSERT INTO solicitation_match_factors (
    match_id,
    factor_type,
    factor_status,
    explanation
)

SELECT
    m.id,
    'bonding',
    'unknown',
    'Bonding capacity needs verification.'
FROM solicitation_contractor_matches AS m
JOIN solicitations AS s
    ON s.id = m.solicitation_id 
WHERE s.solicitation_number = 'TEST-MATCH-001';

--Verifies the match and its factors
SELECT
    c.company_name,
    s.title AS solicitation,
    m.match_score,
    m.match_status,
    f.factor_type,
    f.factor_status
FROM solicitation_contractor_matches AS m
JOIN contractors AS c 
    ON c.id = m.contractor_id
JOIN solicitations AS s
    ON s.id = m.solicitation_id
JOIN solicitation_match_factors AS f
    ON f.match_id = m.id
WHERE s.solicitation_number = 'TEST-MATCH-001'
ORDER BY f.factor_type;

--Removes fictional data
ROLLBACK;