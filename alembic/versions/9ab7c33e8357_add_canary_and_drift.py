"""add_canary_and_drift

Revision ID: 9ab7c33e8357
Revises: 8ad6b22e6357
Create Date: 2026-05-20 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ab7c33e8357'
down_revision: Union[str, Sequence[str], None] = '8ad6b22e6357'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table('prompt_deployments',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('namespace_id', sa.UUID(), nullable=False),
    sa.Column('prompt_version_id', sa.UUID(), nullable=False),
    sa.Column('rollout_percentage', sa.Integer(), nullable=False, server_default='0'),
    sa.Column('deployment_state', sa.String(length=50), nullable=False, server_default='candidate'),
    sa.Column('baseline_metrics', sa.JSON(), nullable=True),
    sa.Column('current_metrics', sa.JSON(), nullable=True),
    sa.Column('rollback_reason', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['namespace_id'], ['prompt_namespaces.id'], ),
    sa.ForeignKeyConstraint(['prompt_version_id'], ['prompt_versions.id'], ),
    sa.PrimaryKeyConstraint('id')
    )

    op.create_table('drift_alerts',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('namespace_id', sa.UUID(), nullable=False),
    sa.Column('category', sa.String(length=100), nullable=False),
    sa.Column('drift_type', sa.String(length=100), nullable=False),
    sa.Column('severity', sa.String(length=50), nullable=False),
    sa.Column('recommendation', sa.String(length=50), nullable=False),
    sa.Column('resolved', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
    sa.ForeignKeyConstraint(['namespace_id'], ['prompt_namespaces.id'], ),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('drift_alerts')
    op.drop_table('prompt_deployments')
