
"""add player name column

Revision ID: be4c3f2e9a1d
Revises: 
Create Date: 2025-01-14 21:20:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'be4c3f2e9a1d'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Add player_name column
    op.add_column('user', sa.Column('player_name', sa.String(64)))
    # Set existing users' player_name to their username
    op.execute("UPDATE \"user\" SET player_name = username")
    # Make the column not nullable after setting default values
    op.alter_column('user', 'player_name', nullable=False)

def downgrade():
    op.drop_column('user', 'player_name')
