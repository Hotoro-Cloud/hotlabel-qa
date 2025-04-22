"""Initial migration

Revision ID: initial_migration
Revises: 
Create Date: 2025-04-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'initial_migration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum types if they do not exist
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'validationmethod') THEN
            CREATE TYPE validationmethod AS ENUM ('golden_set', 'consensus', 'statistical', 'bot_detection', 'threshold', 'manual');
        END IF;
    END$$;
    """)
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'validationstatus') THEN
            CREATE TYPE validationstatus AS ENUM ('pending', 'validated', 'rejected', 'needs_review');
        END IF;
    END$$;
    """)
    op.execute("""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'consensusstatus') THEN
            CREATE TYPE consensusstatus AS ENUM ('pending', 'in_progress', 'completed', 'failed');
        END IF;
    END$$;
    """)
    
    # Create tables
    op.create_table('consensus_groups',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('task_id', sa.String(), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'in_progress', 'completed', 'failed', name='consensusstatus', create_type=False), nullable=True),
        sa.Column('required_validations', sa.Integer(), nullable=True),
        sa.Column('agreement_threshold', sa.Float(), nullable=True),
        sa.Column('consensus_result', sa.JSON(), nullable=True),
        sa.Column('agreement_level', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_consensus_groups_id'), 'consensus_groups', ['id'], unique=False)
    op.create_index(op.f('ix_consensus_groups_task_id'), 'consensus_groups', ['task_id'], unique=False)
    
    op.create_table('golden_sets',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('task_id', sa.String(), nullable=False),
        sa.Column('validation_id', sa.String(), nullable=True),
        sa.Column('expected_response', sa.JSON(), nullable=False),
        sa.Column('allowed_variation', sa.Float(), nullable=True),
        sa.Column('hints', sa.JSON(), nullable=True),
        sa.Column('difficulty_level', sa.Integer(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('tags', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('task_id')
    )
    op.create_index(op.f('ix_golden_sets_category'), 'golden_sets', ['category'], unique=False)
    op.create_index(op.f('ix_golden_sets_id'), 'golden_sets', ['id'], unique=False)
    op.create_index(op.f('ix_golden_sets_task_id'), 'golden_sets', ['task_id'], unique=False)
    
    op.create_table('validations',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('task_id', sa.String(), nullable=True),
        sa.Column('result_id', sa.String(), nullable=True),
        sa.Column('session_id', sa.String(), nullable=True),
        sa.Column('publisher_id', sa.String(), nullable=True),
        sa.Column('validation_method', postgresql.ENUM('golden_set', 'consensus', 'statistical', 'bot_detection', 'threshold', 'manual', name='validationmethod', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'validated', 'rejected', 'needs_review', name='validationstatus', create_type=False), nullable=True),
        sa.Column('quality_score', sa.Float(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('issues_detected', sa.JSON(), nullable=True),
        sa.Column('feedback', sa.String(), nullable=True),
        sa.Column('task_type', sa.String(), nullable=True),
        sa.Column('response', sa.JSON(), nullable=True),
        sa.Column('time_spent_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('consensus_group_id', sa.String(), nullable=True),
        sa.ForeignKeyConstraint(['consensus_group_id'], ['consensus_groups.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_validations_id'), 'validations', ['id'], unique=False)
    op.create_index(op.f('ix_validations_publisher_id'), 'validations', ['publisher_id'], unique=False)
    op.create_index(op.f('ix_validations_result_id'), 'validations', ['result_id'], unique=False)
    op.create_index(op.f('ix_validations_session_id'), 'validations', ['session_id'], unique=False)
    op.create_index(op.f('ix_validations_task_id'), 'validations', ['task_id'], unique=False)
    op.create_index(op.f('ix_validations_task_type'), 'validations', ['task_type'], unique=False)
    
    op.create_table('quality_metrics',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('validation_id', sa.String(), nullable=False),
        sa.Column('metric_type', sa.String(), nullable=False),
        sa.Column('value', sa.Float(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['validation_id'], ['validations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_quality_metrics_id'), 'quality_metrics', ['id'], unique=False)
    op.create_index(op.f('ix_quality_metrics_metric_type'), 'quality_metrics', ['metric_type'], unique=False)
    
    # Add Foreign Key from golden_sets to validations
    op.create_foreign_key(None, 'golden_sets', 'validations', ['validation_id'], ['id'])


def downgrade() -> None:
    # Drop tables
    op.drop_constraint(None, 'golden_sets', type_='foreignkey')
    op.drop_table('quality_metrics')
    op.drop_index(op.f('ix_validations_task_type'), table_name='validations')
    op.drop_index(op.f('ix_validations_task_id'), table_name='validations')
    op.drop_index(op.f('ix_validations_session_id'), table_name='validations')
    op.drop_index(op.f('ix_validations_result_id'), table_name='validations')
    op.drop_index(op.f('ix_validations_publisher_id'), table_name='validations')
    op.drop_index(op.f('ix_validations_id'), table_name='validations')
    op.drop_table('validations')
    op.drop_index(op.f('ix_golden_sets_task_id'), table_name='golden_sets')
    op.drop_index(op.f('ix_golden_sets_id'), table_name='golden_sets')
    op.drop_index(op.f('ix_golden_sets_category'), table_name='golden_sets')
    op.drop_table('golden_sets')
    op.drop_index(op.f('ix_consensus_groups_task_id'), table_name='consensus_groups')
    op.drop_index(op.f('ix_consensus_groups_id'), table_name='consensus_groups')
    op.drop_table('consensus_groups')
    
    # Drop enum types
    op.execute("DROP TYPE validationmethod")
    op.execute("DROP TYPE validationstatus")
    op.execute("DROP TYPE consensusstatus")
