
"""add player_name field

Revision ID: 19ccab0482d2
Revises: 777ed8523638
Create Date: 2025-01-14 20:30:33.428116

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '19ccab0482d2'
down_revision = '777ed8523638'
branch_labels = None
depends_on = None


def upgrade():
    # Add the column as nullable first
    op.add_column('user', sa.Column('player_name', sa.String(length=64), nullable=True))
    
    # Update existing records to use username as player_name
    op.execute("UPDATE \"user\" SET player_name = username")
    
    # Now make the column non-nullable
    op.alter_column('user', 'player_name',
                    existing_type=sa.String(length=64),
                    nullable=False)


def downgrade():
    op.drop_column('user', 'player_name')
