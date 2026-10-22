--Test records to be rolled back
BEGIN;

--Creates a fictional app user

INSERT INTO app_users (
    email,
    full_name,
    account_status
)

VALUES (
    'test-coordinator@example.com',
    'Test Coordinator',
    'active'
);

--Creates a fictional test role
INSERT INTO roles(
    role_name,
    description
)

VALUES (
    'test_coordinator',
    'Temporary test role'
)

ON CONFLICT (role_name) DO NOTHING;

--Assigns fictional role to fictional user
INSERT INTO user_roles (
    user_id,
    role_id
)

SELECT
    u.id,
    r.id
FROM app_users AS u 
CROSS JOIN roles AS r
WHERE u.email = 'test-coordinator@example.com'
AND r.role_name = 'test_coordinator';

--Creates fictional solicitation
INSERT INTO solicitations (
    source,
    agency,
    title,
    solicitation_number,
    source_url,
    status
)

VALUES(
    'test',
    'Test City',
    'TEST - Municipal Construction',
    'TEST-ASSIGN-001',
    'https://example.com/test-assign-001',
    'open'
);

--Assigns fictional solicitation to fictional user
INSERT INTO solicitation_assignments (
    solicitation_id,
    assigned_to,
    assignment_type,
    assignment_status,
    priority
)

SELECT
    s.id,
    u.id,
    'review',
    'pending',
    'high'
FROM solicitations AS s
CROSS JOIN app_users AS u
WHERE s.solicitation_number = 'TEST-ASSIGN-001'
AND u.email = 'test-coordinator@example.com';

--Records fictional assignment activity
INSERT INTO assignment_activity (
    assignment_id,
    user_id,
    activity_type,
    note
)

SELECT
    a.id,
    a.assigned_to,
    'created',
    'Assigned for document review.'
FROM solicitation_assignments AS a
JOIN solicitations AS s
    ON s.id = a.solicitation_id
WHERE s.solicitation_number = 'TEST-ASSIGN-001';

--Records a fictional audit event
INSERT INTO audit_logs (
    actor_user_id,
    action,
    entity_type,
    entity_id,
    details
)

SELECT
    a.assigned_to,
    'assignment.created',
    'solicitation_assignment',
    a.id,
    '{"source": "step_18_test"}'::jsonb
FROM solicitation_assignments AS a
JOIN solicitations AS s
    ON s.id = a.solicitation_id
WHERE s.solicitation_number = 'TEST-ASSIGN-001';

--Verifies fictional relationships
SELECT
    u.full_name,
    r.role_name,
    s.title AS solicitation,
    a.assignment_type,
    a.assignment_status,
    a.priority,
    al.action AS audit_action
FROM solicitation_assignments AS a
JOIN app_users AS u
    ON u.id = a.assigned_to
JOIN user_roles AS ur
    ON ur.user_id = u.id
JOIN roles AS r
    ON r.id = ur.role_id
JOIN solicitations AS s
    ON s.id = a.solicitation_id
JOIN audit_logs AS al
    ON al.entity_type = 'solicitation_assignment'
    AND al.entity_id = a.id
WHERE s.solicitation_number = 'TEST-ASSIGN-001';

--Removes fictional data
ROLLBACK;