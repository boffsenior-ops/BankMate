"""Add was_failover to llm_usage

Revision ID: b2e3f4a5c6d7
Revises: a0f1a702900c
Create Date: 2026-06-01 21:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2e3f4a5c6d7'
down_revision: Union[str, Sequence[str], None] = 'a0f1a702900c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add was_failover boolean column to llm_usage table."""
    op.add_column(
        'llm_usage',
        sa.Column('was_failover', sa.Boolean(), nullable=False, server_default='false')
    )


def downgrade() -> None:
    """Remove was_failover column."""
    op.drop_column('llm_usage', 'was_failover')
