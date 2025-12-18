"""Update Hall of Fame first-subscription commission rate to 40%

Revision ID: 010_update_hof_first_sub_rate
Revises: 009_tax_info_affiliates
Create Date: 2025-12-17

This is a data-only migration:
- Existing affiliates already at tier=hall_of_fame should immediately receive the updated
  first-subscription commission rate (0.40).
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "010_update_hof_first_sub_rate"
down_revision = "009_tax_info_affiliates"
branch_labels = None
depends_on = None


def upgrade():
    op.execute(
        """
        UPDATE affiliates
        SET commission_rate_sub_first = 0.40
        WHERE tier = 'hall_of_fame'
          AND commission_rate_sub_first <> 0.40
        """
    )


def downgrade():
    # Revert to the previous Hall of Fame first-sub commission rate.
    op.execute(
        """
        UPDATE affiliates
        SET commission_rate_sub_first = 0.20
        WHERE tier = 'hall_of_fame'
          AND commission_rate_sub_first <> 0.20
        """
    )



