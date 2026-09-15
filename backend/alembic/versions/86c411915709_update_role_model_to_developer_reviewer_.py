"""Update role model to developer, reviewer, team_lead, org_admin

Revision ID: 86c411915709
Revises: e3a7f2d63e43
Create Date: 2026-09-07 17:07:30.603797

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '86c411915709'
down_revision: Union[str, None] = 'e3a7f2d63e43'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Update existing 'member' or 'MEMBER' records to 'developer'
    op.execute("UPDATE organization_membership SET role = 'developer' WHERE role = 'member' OR role = 'MEMBER'")
    op.execute("UPDATE organization_membership SET role = 'team_lead' WHERE role = 'TEAM_LEAD'")
    op.execute("UPDATE organization_membership SET role = 'org_admin' WHERE role = 'ORG_ADMIN'")

    # Try dropping the old check constraint if it exists. SQLAlchemy usually names it after the enum name 'roleenum'
    # or creates it anonymously. In PostgreSQL, we can use a DO block to drop it if it exists.
    op.execute("""
        DO $$
        DECLARE
            constraint_name text;
        BEGIN
            SELECT conname INTO constraint_name
            FROM pg_constraint
            WHERE conrelid = 'organization_membership'::regclass AND contype = 'c' AND conname LIKE '%roleenum%';
            
            IF constraint_name IS NOT NULL THEN
                EXECUTE 'ALTER TABLE organization_membership DROP CONSTRAINT ' || constraint_name;
            END IF;
        END $$;
    """)

    # Add the new check constraint
    op.create_check_constraint(
        'roleenum_new',
        'organization_membership',
        "role IN ('developer', 'reviewer', 'team_lead', 'org_admin')"
    )


def downgrade() -> None:
    op.execute("UPDATE organization_membership SET role = 'member' WHERE role = 'developer' OR role = 'reviewer'")

    op.execute("""
        DO $$
        DECLARE
            constraint_name text;
        BEGIN
            SELECT conname INTO constraint_name
            FROM pg_constraint
            WHERE conrelid = 'organization_membership'::regclass AND contype = 'c' AND conname = 'roleenum_new';
            
            IF constraint_name IS NOT NULL THEN
                EXECUTE 'ALTER TABLE organization_membership DROP CONSTRAINT ' || constraint_name;
            END IF;
        END $$;
    """)

    op.create_check_constraint(
        'roleenum',
        'organization_membership',
        "role IN ('MEMBER', 'TEAM_LEAD', 'ORG_ADMIN')"
    )
