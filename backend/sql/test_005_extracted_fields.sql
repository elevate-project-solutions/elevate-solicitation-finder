--Temp test
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
    'TEST - Extraction Workflow',
    'TEST-EXTRACT-001',
    'https://example.com/test-extract-001',
    'open'
);

--Creates fictional document
INSERT INTO solicitation_documents (
    solicitation_id,
    title,
    document_type
)

SELECT
    id,
    'Test Solicitation PDF',
    'solicitation'

FROM solicitations
WHERE solicitation_number = 'TEST-EXTRACT-001';

--Creates first version of document
INSERT INTO document_versions (
    document_id,
    version_number,
    file_name,
    mime_type
)
SELECT
    d.id,
    1,
    'test-solicitation.pdf',
    'application/pdf'
FROM solicitation_documents AS d
JOIN solicitations AS s
    ON s.id = d.solicitation_id
WHERE s.solicitation_number = 'TEST-EXTRACT-001'
AND d.title = 'Test Solicitation PDF';


--Records extraction run
INSERT INTO extraction_runs (
    solicitation_id,
    document_version_id,
    extractor_name,
    extractor_version,
    run_status,
    completed_at
)

SELECT
    s.id,
    dv.id,
    'test_extractor',
    '1.0',
    'completed',
    NOW()

FROM solicitations AS s
JOIN solicitation_documents AS d
    ON d.solicitation_id = s.id
JOIN document_versions AS dv
    ON dv.document_id = d.id
WHERE s.solicitation_number = 'TEST-EXTRACT-001';

--Records extracted field
INSERT INTO extracted_fields (
    extraction_run_id,
    field_name,
    extracted_value,
    confidence_score
)

SELECT
    id,
    'mandatory-site-visit',
    'true'::jsonb,
    0.9200

FROM extraction_runs
WHERE solicitation_id = (
    SELECT id
    FROM solicitations 
    WHERE solicitation_number = 'TEST-EXTRACT-001'
);

--Records source evidence
INSERT INTO extracted_field_evidence (
    extracted_field_id,
    document_version_id,
    page_number,
    evidence_text
)

SELECT
    ef.id,
    er.document_version_id,
    12,
    'Attendance at the site visit is mandatory.'

FROM extracted_fields AS ef
JOIN extraction_runs AS er
    ON er.id = ef.extraction_run_id
JOIN solicitations AS s
    ON s.id = er.solicitation_id
WHERE s.solicitation_number = 'TEST-EXTRACT-001';

--Simulates human approval
UPDATE extracted_fields
SET
    review_status = 'approved',
    reviewed_by = 'Test Reviewer',
    reviewed_at = NOW(),
    review_notes = 'Verified against page 12.'
WHERE field_name = 'mandatory_site_visit'
AND extraction_run_id IN (
    SELECT er.id
    FROM extraction_runs AS er
    JOIN solicitations AS s
        ON s.id = er.solicitation_id
    WHERE s.solicitation_number = 'TEST-EXTRACT-001'
);

--Verifies result
SELECT
    ef.field_name,
    ef.extracted_value,
    ef.confidence_score,
    ef.review_status,
    ev.page_number,
    ev.evidence_text

FROM extracted_fields AS ef
JOIN extracted_field_evidence AS ev
    ON ev.extracted_field_id = ef.id
JOIN extraction_runs AS er
    ON er.id = ef.extraction_run_id
JOIN solicitations AS s
    ON s.id = er.solicitation_id
WHERE s.solicitation_number = 'TEST-EXTRACT-001';

--Removes fictional records
ROLLBACK;