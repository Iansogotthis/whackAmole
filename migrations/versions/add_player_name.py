
"""add player name

Revision ID: add_player_name
Revises: d642883f60f2
Create Date: 2025-01-14 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_player_name'
down_revision = 'd642883f60f2'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('user', sa.Column('player_name', sa.String(length=64)))
    op.execute("UPDATE \"user\" SET player_name = username")
    op.alter_column('user', 'player_name', nullable=False)

def downgrade():
    op.drop_column('user', 'player_name')
