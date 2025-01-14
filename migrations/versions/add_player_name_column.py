
"""add player_name column

Revision ID: add_player_name_column
Revises: d642883f60f2
Create Date: 2025-01-14 21:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_player_name_column'
down_revision = 'd642883f60f2'
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
