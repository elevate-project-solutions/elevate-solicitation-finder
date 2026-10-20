--App roles
INSERT INTO roles(
    role_name,
    description
)

VALUES
    (
        'admin',
        'Full administrative access'
    ),
    (
        'coordinator',
        'Manage assigned solicitation work'
    ),
    (
        'viewer',
        'Read only application access'
    )

ON CONFLICT (role_name) DO NOTHING;