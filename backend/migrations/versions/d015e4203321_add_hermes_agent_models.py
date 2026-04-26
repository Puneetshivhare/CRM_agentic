"""Add Hermes Agent models

Revision ID: d015e4203321
Revises: d015e4203320
Create Date: 2026-04-26 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd015e4203321'
down_revision = 'd015e4203320'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create hermes_tenants table
    op.create_table(
        'hermes_tenants',
        sa.Column('tenant_id', sa.String(64), nullable=False),
        sa.Column('tenant_name', sa.String(255), nullable=False),
        sa.Column('container_name', sa.String(255), nullable=True),
        sa.Column('api_endpoint', sa.String(500), nullable=True),
        sa.Column('allowed_actions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('blocked_actions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('allowed_mcp_servers', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default='provisioning'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('tenant_id')
    )
    
    # Create hermes_executions table
    op.create_table(
        'hermes_executions',
        sa.Column('execution_id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('tenant_id', sa.String(64), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('hermes_task_id', sa.String(64), nullable=False, index=True),
        sa.Column('task_type', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='running'),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('input_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('output_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('memory_hits', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        # CRM linkage - simple integer fields without FK constraints to avoid issues
        sa.Column('prospect_id', sa.Integer(), nullable=True, index=True),
        sa.Column('company_id', sa.Integer(), nullable=True, index=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['hermes_tenants.tenant_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['auth_users.user_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('execution_id')
    )
    
    # Create hermes_skills table
    op.create_table(
        'hermes_skills',
        sa.Column('skill_id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('tenant_id', sa.String(64), nullable=False, index=True),
        sa.Column('skill_name', sa.String(255), nullable=False),
        sa.Column('skill_type', sa.String(100), nullable=False),
        sa.Column('skill_definition', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.Column('usage_count', sa.Integer(), nullable=True, server_default='0'),
        sa.Column('success_rate', sa.String(10), nullable=True, server_default='0%'),
        sa.ForeignKeyConstraint(['tenant_id'], ['hermes_tenants.tenant_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('skill_id')
    )
    
    # Create indexes for performance
    op.create_index('idx_hermes_execution_tenant_status', 'hermes_executions', ['tenant_id', 'status'])
    op.create_index('idx_hermes_execution_start_time', 'hermes_executions', ['start_time'])
    op.create_index('idx_hermes_skill_tenant_type', 'hermes_skills', ['tenant_id', 'skill_type'])


def downgrade() -> None:
    op.drop_index('idx_hermes_skill_tenant_type', table_name='hermes_skills')
    op.drop_index('idx_hermes_execution_start_time', table_name='hermes_executions')
    op.drop_index('idx_hermes_execution_tenant_status', table_name='hermes_executions')
    op.drop_table('hermes_skills')
    op.drop_table('hermes_executions')
    op.drop_table('hermes_tenants')
