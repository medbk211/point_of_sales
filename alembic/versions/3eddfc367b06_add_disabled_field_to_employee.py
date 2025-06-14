"""add disabled field to employee

Revision ID: 3eddfc367b06
Revises: 3b187f67fafc
Create Date: 2025-06-14 13:24:01.246166

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3eddfc367b06'
down_revision: Union[str, None] = '3b187f67fafc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('employee', sa.Column('disabled', sa.Boolean(), nullable=True))

    # op.alter_column('employee', 'phone_number',
    #           existing_type=sa.VARCHAR(length=20),
    #           type_=sa.String(length=11),
    #           existing_nullable=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('employee', 'disabled')
    
