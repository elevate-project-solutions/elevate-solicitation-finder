--Temp test for event requirement tables
--fictional records. Automatically rolled back.

BEGIN;

--Creates a fictional solicitation
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
    'TEST - Municipal Roof Replacement Events',
    'TEST-EVENTS-001',
    'https://example.com/test-events-001',
    'open'
);

--Creates a mandatory pre bid conference
WITH test_solicitation AS (
    SELECT id
    FROM solicitations
    WHERE solicitation_number = 'TEST-EVENTS-001'
)

INSERT INTO solicitation_events (
    solicitation_id,
    event_type,
    title,
    starts_at,
    timezone_name,
    location
)

SELECT
    id,
    'pre_bid_conference',
    'Mandatory Pre-Bid Conference',
    '2026-11-09 10:00:00-06',
    'American/Chicago',
    'Test City Hall'
FROM test_solicitation;

--Marks the event as mandatory
INSERT INTO solicitation_event_requirements (
    event_id,
    attendance_requirement,
    registration_required,
    requirement_notes
)

SELECT
    e.id,
    'mandatory',
    FALSE,
    'Contractors must attend to remain eligible to bid.'
FROM solicitation_events AS e
JOIN solicitations AS s
    ON s.id = e.solicitation_id
WHERE s.solicitation_number = 'TEST-EVENTS-001';

--Verifies the relationship
SELECT 
    s.title AS solicitation,
    e.title AS event,
    e.starts_at,
    r.attendance_requirement,
    r.registration_required
FROM solicitation_events AS e
JOIN solicitations AS s
    ON s.id = e.solicitation_id
JOIN solicitation_event_requirements AS r
    ON r.event_id = e.id
WHERE s.solicitation_number = 'TEST-EVENTS-001';

ROLLBACK;