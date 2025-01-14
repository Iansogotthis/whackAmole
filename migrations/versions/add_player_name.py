
"""add player name column

Revision ID: add_player_name
Create Date: 2025-01-14 21:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_player_name'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add player_name column
    op.add_column('user', sa.Column('player_name', sa.String(64)))
    # Set player_name equal to username for existing users
    op.execute("UPDATE \"user\" SET player_name = username WHERE player_name IS NULL")
    # Make player_name not nullable
    op.alter_column('user', 'player_name', nullable=False)

def downgrade():
    op.drop_column('user', 'player_name')
