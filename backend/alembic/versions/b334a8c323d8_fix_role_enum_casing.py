"""Fix role enum casing

Revision ID: b334a8c323d8
Revises: 86c411915709
Create Date: 2026-09-07 17:15:42.922077

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b334a8c323d8'
down_revision: Union[str, None] = '86c411915709'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop the lowercase constraint first to avoid conflicts during UPDATE
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

    # Update to uppercase to match SQLAlchemy enum name defaults
    op.execute("UPDATE organization_membership SET role = UPPER(role)")

    # Recreate the check constraint with uppercase values
    op.create_check_constraint(
        'roleenum_upper',
        'organization_membership',
        "role IN ('DEVELOPER', 'REVIEWER', 'TEAM_LEAD', 'ORG_ADMIN')"
    )


def downgrade() -> None:
    pass
