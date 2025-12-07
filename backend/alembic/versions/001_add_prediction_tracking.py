"""Add prediction tracking tables

Revision ID: 001_add_prediction_tracking
Revises: 
Create Date: 2024-12-05 12:00:00.000000

Creates tables for tracking model predictions and learning from outcomes:
- model_predictions: Stores every prediction made
- prediction_outcomes: Links predictions to actual results
- team_calibrations: Per-team bias adjustments
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_add_prediction_tracking'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create model_predictions table
    op.create_table(
        'model_predictions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('game_id', sa.UUID(), nullable=True),
        sa.Column('external_game_id', sa.String(), nullable=True),
        sa.Column('sport', sa.String(), nullable=False),
        sa.Column('home_team', sa.String(), nullable=False),
        sa.Column('away_team', sa.String(), nullable=False),
        sa.Column('game_time', sa.DateTime(timezone=True), nullable=True),
        sa.Column('market_type', sa.String(), nullable=False),
        sa.Column('team_side', sa.String(), nullable=False),
        sa.Column('predicted_prob', sa.Float(), nullable=False),
        sa.Column('implied_prob', sa.Float(), nullable=True),
        sa.Column('edge', sa.Float(), nullable=True),
        sa.Column('model_version', sa.String(), nullable=False, server_default='pg-1.0.0'),
        sa.Column('calculation_method', sa.String(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('feature_snapshot', sa.JSON(), nullable=True),
        sa.Column('is_resolved', sa.String(), server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for model_predictions
    op.create_index('idx_predictions_game_id', 'model_predictions', ['game_id'])
    op.create_index('idx_predictions_external_game_id', 'model_predictions', ['external_game_id'])
    op.create_index('idx_predictions_sport', 'model_predictions', ['sport'])
    op.create_index('idx_predictions_sport_date', 'model_predictions', ['sport', 'created_at'])
    op.create_index('idx_predictions_model_version', 'model_predictions', ['model_version'])
    op.create_index('idx_predictions_resolved', 'model_predictions', ['is_resolved'])
    op.create_index('idx_predictions_team_side', 'model_predictions', ['team_side', 'sport'])
    op.create_index('idx_predictions_game_market', 'model_predictions', ['game_id', 'market_type'])
    
    # Create prediction_outcomes table
    op.create_table(
        'prediction_outcomes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('prediction_id', sa.UUID(), nullable=False),
        sa.Column('was_correct', sa.Boolean(), nullable=False),
        sa.Column('error_magnitude', sa.Float(), nullable=False),
        sa.Column('signed_error', sa.Float(), nullable=False),
        sa.Column('actual_result', sa.String(), nullable=True),
        sa.Column('actual_score_home', sa.Float(), nullable=True),
        sa.Column('actual_score_away', sa.Float(), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['prediction_id'], ['model_predictions.id']),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for prediction_outcomes
    op.create_index('idx_outcomes_prediction', 'prediction_outcomes', ['prediction_id'])
    op.create_index('idx_outcomes_correct', 'prediction_outcomes', ['was_correct'])
    op.create_index('idx_outcomes_resolved', 'prediction_outcomes', ['resolved_at'])
    
    # Create team_calibrations table
    op.create_table(
        'team_calibrations',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('team_name', sa.String(), nullable=False),
        sa.Column('sport', sa.String(), nullable=False),
        sa.Column('bias_adjustment', sa.Float(), server_default='0.0'),
        sa.Column('avg_signed_error', sa.Float(), server_default='0.0'),
        sa.Column('sample_size', sa.Float(), server_default='0'),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('brier_score', sa.Float(), nullable=True),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create unique index for team_calibrations
    op.create_index('idx_calibration_team_sport', 'team_calibrations', ['team_name', 'sport'], unique=True)


def downgrade() -> None:
    # Drop team_calibrations
    op.drop_index('idx_calibration_team_sport', table_name='team_calibrations')
    op.drop_table('team_calibrations')
    
    # Drop prediction_outcomes
    op.drop_index('idx_outcomes_resolved', table_name='prediction_outcomes')
    op.drop_index('idx_outcomes_correct', table_name='prediction_outcomes')
    op.drop_index('idx_outcomes_prediction', table_name='prediction_outcomes')
    op.drop_table('prediction_outcomes')
    
    # Drop model_predictions
    op.drop_index('idx_predictions_game_market', table_name='model_predictions')
    op.drop_index('idx_predictions_team_side', table_name='model_predictions')
    op.drop_index('idx_predictions_resolved', table_name='model_predictions')
    op.drop_index('idx_predictions_model_version', table_name='model_predictions')
    op.drop_index('idx_predictions_sport_date', table_name='model_predictions')
    op.drop_index('idx_predictions_sport', table_name='model_predictions')
    op.drop_index('idx_predictions_external_game_id', table_name='model_predictions')
    op.drop_index('idx_predictions_game_id', table_name='model_predictions')
    op.drop_table('model_predictions')

