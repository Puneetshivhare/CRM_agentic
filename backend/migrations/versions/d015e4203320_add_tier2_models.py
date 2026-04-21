"""Add Tier 2 models (campaigns, lead_scores, rule_executions)

Revision ID: d015e4203320
Revises: d015e4203319
Create Date: 2026-04-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


revision = 'd015e4203320'
down_revision = 'd015e4203319'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # dim_campaigns table
    op.create_table(
        'dim_campaigns',
        sa.Column('campaign_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('sequence_steps', sa.JSON(), nullable=False),
        sa.Column('target_criteria', sa.JSON(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.literal(True), index=True),
        sa.Column('enrolled_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('opened_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('clicked_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('replied_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('conversion_rate', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('campaign_id')
    )

    # fact_lead_scores table
    op.create_table(
        'fact_lead_scores',
        sa.Column('score_id', sa.Integer(), nullable=False),
        sa.Column('prospect_id', sa.Integer(), nullable=False, index=True),
        sa.Column('company_id', sa.Integer(), nullable=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('fit_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('engagement_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('propensity_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('total_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('grade', sa.String(1), nullable=False, server_default='F'),
        sa.Column('score_breakdown', sa.JSON(), nullable=True),
        sa.Column('signals', sa.JSON(), nullable=True),
        sa.Column('is_hot_lead', sa.Boolean(), nullable=False, server_default=sa.literal(False)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['prospect_id'], ['dim_prospects.prospect_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['company_id'], ['dim_companies.company_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('score_id')
    )

    # fact_rule_executions table
    op.create_table(
        'fact_rule_executions',
        sa.Column('execution_id', sa.Integer(), nullable=False),
        sa.Column('rule_id', sa.Integer(), nullable=False, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('prospect_id', sa.Integer(), nullable=True, index=True),
        sa.Column('company_id', sa.Integer(), nullable=True, index=True),
        sa.Column('trigger_event', sa.String(100), nullable=False),
        sa.Column('triggered', sa.Boolean(), nullable=False, server_default=sa.literal(False)),
        sa.Column('action_taken', sa.String(255), nullable=True),
        sa.Column('result', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('trigger_data', sa.JSON(), nullable=True),
        sa.Column('action_result', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['rule_id'], ['dim_rules.rule_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('execution_id')
    )

    # Create indexes for lead_score queries
    op.create_index('idx_lead_score_user_prospect', 'fact_lead_scores', ['user_id', 'prospect_id'])
    op.create_index('idx_lead_score_total', 'fact_lead_scores', ['total_score'])
    op.create_index('idx_lead_score_grade', 'fact_lead_scores', ['grade'])


def downgrade() -> None:
    op.drop_index('idx_lead_score_grade', table_name='fact_lead_scores')
    op.drop_index('idx_lead_score_total', table_name='fact_lead_scores')
    op.drop_index('idx_lead_score_user_prospect', table_name='fact_lead_scores')
    op.drop_table('fact_rule_executions')
    op.drop_table('fact_lead_scores')
    op.drop_table('dim_campaigns')
