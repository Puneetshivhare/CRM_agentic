"""initial_schema - Create all core tables

Revision ID: d015e4203319
Revises:
Create Date: 2026-04-19 14:20:26.975906

"""
from alembic import op
import sqlalchemy as sa


revision = 'd015e4203319'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # auth_users
    op.create_table(
        'auth_users',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('user_id')
    )

    # dim_companies
    op.create_table(
        'dim_companies',
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('name', sa.String(500), nullable=False, unique=True),
        sa.Column('domain', sa.String(255), nullable=True, index=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('headcount', sa.Integer(), nullable=True),
        sa.Column('headcount_range', sa.String(50), nullable=True),
        sa.Column('revenue_annual', sa.Numeric(15, 2), nullable=True),
        sa.Column('funding_stage', sa.String(100), nullable=True, index=True),
        sa.Column('latest_funding_date', sa.Date(), nullable=True),
        sa.Column('headquarters_city', sa.String(255), nullable=True),
        sa.Column('headquarters_country', sa.String(255), nullable=True),
        sa.Column('industry', sa.String(255), nullable=True),
        sa.Column('tech_stack', sa.JSON(), nullable=True),
        sa.Column('monitoring_enabled', sa.Boolean(), nullable=False, server_default=sa.literal(False)),
        sa.Column('last_monitoring_run_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('company_id')
    )

    # dim_prospects
    op.create_table(
        'dim_prospects',
        sa.Column('prospect_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('company_id', sa.Integer(), nullable=True),
        sa.Column('email', sa.String(255), nullable=True),
        sa.Column('first_name', sa.String(100), nullable=True),
        sa.Column('last_name', sa.String(100), nullable=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('phone', sa.String(20), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('linkedin_url', sa.String(500), nullable=True),
        sa.Column('website_url', sa.String(500), nullable=True),
        sa.Column('enrichment_status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('enrichment_confidence', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('last_contacted_at', sa.DateTime(), nullable=True),
        sa.Column('email_opens', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('email_clicks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['dim_companies.company_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('prospect_id'),
        sa.CheckConstraint('enrichment_confidence >= 0.0 AND enrichment_confidence <= 1.0')
    )

    # fact_interactions
    op.create_table(
        'fact_interactions',
        sa.Column('interaction_id', sa.Integer(), nullable=False),
        sa.Column('prospect_id', sa.Integer(), nullable=False, index=True),
        sa.Column('interaction_type', sa.String(50), nullable=False),
        sa.Column('subject', sa.String(500), nullable=True),
        sa.Column('body', sa.Text(), nullable=True),
        sa.Column('initiated_by', sa.String(100), nullable=True),
        sa.Column('interaction_date', sa.DateTime(), nullable=False),
        sa.Column('duration_seconds', sa.Integer(), nullable=True),
        sa.Column('email_opened', sa.Boolean(), nullable=False, server_default=sa.literal(False)),
        sa.Column('email_clicked', sa.Boolean(), nullable=False, server_default=sa.literal(False)),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['prospect_id'], ['dim_prospects.prospect_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('interaction_id')
    )

    # dim_documents
    op.create_table(
        'dim_documents',
        sa.Column('document_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('file_path', sa.String(1000), nullable=False),
        sa.Column('file_name', sa.String(500), nullable=False),
        sa.Column('document_type', sa.String(50), nullable=False),
        sa.Column('num_pages', sa.Integer(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('associated_company_id', sa.Integer(), nullable=True),
        sa.Column('upload_date', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['associated_company_id'], ['dim_companies.company_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('document_id')
    )

    # fact_enrichment_events
    op.create_table(
        'fact_enrichment_events',
        sa.Column('event_id', sa.Integer(), nullable=False),
        sa.Column('prospect_id', sa.Integer(), nullable=False, index=True),
        sa.Column('field_name', sa.String(255), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('agent_name', sa.String(100), nullable=False, index=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('source', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['prospect_id'], ['dim_prospects.prospect_id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('event_id')
    )

    # fact_agent_executions
    op.create_table(
        'fact_agent_executions',
        sa.Column('execution_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('agent_type', sa.String(100), nullable=False),
        sa.Column('agent_name', sa.String(255), nullable=False),
        sa.Column('task_id', sa.String(100), nullable=True),
        sa.Column('prospect_id', sa.Integer(), nullable=True, index=True),
        sa.Column('company_id', sa.Integer(), nullable=True, index=True),
        sa.Column('status', sa.String(50), nullable=False),
        sa.Column('input_data', sa.JSON(), nullable=True),
        sa.Column('output_data', sa.JSON(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('duration_ms', sa.Integer(), nullable=True),
        sa.Column('tokens_used', sa.Integer(), nullable=True, index=True),
        sa.Column('api_cost_cents', sa.Numeric(10, 2), nullable=True),
        sa.Column('decision_description', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('memory_hits', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['prospect_id'], ['dim_prospects.prospect_id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['company_id'], ['dim_companies.company_id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('execution_id')
    )

    # memory_store
    op.create_table(
        'memory_store',
        sa.Column('memory_key', sa.String(500), nullable=False),
        sa.Column('memory_value', sa.JSON(), nullable=False),
        sa.Column('ttl_seconds', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('accessed_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('memory_key')
    )

    # memory_vector
    op.create_table(
        'memory_vector',
        sa.Column('vector_id', sa.Integer(), nullable=False),
        sa.Column('embedding_key', sa.String(500), nullable=False),
        sa.Column('embedding', sa.Text(), nullable=False),
        sa.Column('embedding_text', sa.Text(), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False, index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('vector_id')
    )

    # dim_rules
    op.create_table(
        'dim_rules',
        sa.Column('rule_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('rule_name', sa.String(255), nullable=False),
        sa.Column('rule_type', sa.String(50), nullable=False),
        sa.Column('rule_definition', sa.JSON(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.literal(True)),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('execution_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('match_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('rule_id')
    )

    # dim_skills
    op.create_table(
        'dim_skills',
        sa.Column('skill_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('skill_name', sa.String(255), nullable=False),
        sa.Column('skill_type', sa.String(50), nullable=False),
        sa.Column('skill_definition', sa.JSON(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.literal(True)),
        sa.Column('execution_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('success_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('avg_execution_time_ms', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('skill_id')
    )


def downgrade() -> None:
    op.drop_table('dim_skills')
    op.drop_table('dim_rules')
    op.drop_table('memory_vector')
    op.drop_table('memory_store')
    op.drop_table('fact_agent_executions')
    op.drop_table('fact_enrichment_events')
    op.drop_table('dim_documents')
    op.drop_table('fact_interactions')
    op.drop_table('dim_prospects')
    op.drop_table('dim_companies')
    op.drop_table('auth_users')
