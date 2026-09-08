"""fix_role_values_to_lowercase

Correction: previous migration b334a8c323d8 uppercased role values to
DEVELOPER/REVIEWER/TEAM_LEAD/ORG_ADMIN in the DB, but the application
RoleEnum uses lowercase values (developer/reviewer/team_lead/org_admin).
This migration normalises the DB to lowercase to match the documented
role names (see Docs/05-security/authentication-authorization.md) and
replaces the roleenum_upper check constraint.

Revision ID: 09cc8a4080e0
Revises: cab03f32deec
Create Date: 2026-09-08 15:22:43.103614

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '09cc8a4080e0'
down_revision: Union[str, None] = 'cab03f32deec'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the uppercase check constraint added by b334a8c323d8
    op.execute("""
        DO $$
        DECLARE
            constraint_name text;
        BEGIN
            SELECT conname INTO constraint_name
            FROM pg_constraint
            WHERE conrelid = 'organization_membership'::regclass
              AND contype = 'c'
              AND conname = 'roleenum_upper';
            IF constraint_name IS NOT NULL THEN
                EXECUTE 'ALTER TABLE organization_membership DROP CONSTRAINT ' || constraint_name;
            END IF;
        END $$;
    """)

    # Normalise all role values to lowercase (matching application RoleEnum)
    op.execute("UPDATE organization_membership SET role = LOWER(role)")

    # Add correct lowercase check constraint
    op.create_check_constraint(
        'ck_organization_membership_role',
        'organization_membership',
        "role IN ('developer', 'reviewer', 'team_lead', 'org_admin')"
    )


def downgrade() -> None:
    # Reverse: drop lowercase constraint, uppercase values, restore uppercase constraint
    op.execute("""
        DO $$
        DECLARE
            constraint_name text;
        BEGIN
            SELECT conname INTO constraint_name
            FROM pg_constraint
            WHERE conrelid = 'organization_membership'::regclass
              AND contype = 'c'
              AND conname = 'ck_organization_membership_role';
            IF constraint_name IS NOT NULL THEN
                EXECUTE 'ALTER TABLE organization_membership DROP CONSTRAINT ' || constraint_name;
            END IF;
        END $$;
    """)
    op.execute("UPDATE organization_membership SET role = UPPER(role)")
    op.create_check_constraint(
        'roleenum_upper',
        'organization_membership',
        "role IN ('DEVELOPER', 'REVIEWER', 'TEAM_LEAD', 'ORG_ADMIN')"
    )
