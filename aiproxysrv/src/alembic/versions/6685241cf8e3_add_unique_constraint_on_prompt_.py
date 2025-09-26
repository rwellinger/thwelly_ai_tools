"""Add unique constraint on prompt_templates category_action

Revision ID: 6685241cf8e3
Revises: f441e59d721f
Create Date: 2025-09-26 18:43:33.327775

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6685241cf8e3'
down_revision: Union[str, Sequence[str], None] = 'f441e59d721f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add unique constraint on prompt_templates (category, action)."""
    op.create_unique_constraint(
        'uq_prompt_templates_category_action',
        'prompt_templates',
        ['category', 'action']
    )


def downgrade() -> None:
    """Remove unique constraint on prompt_templates (category, action)."""
    op.drop_constraint(
        'uq_prompt_templates_category_action',
        'prompt_templates',
        type_='unique'
    )
