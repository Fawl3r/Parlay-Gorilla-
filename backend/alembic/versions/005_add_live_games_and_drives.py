"""Add live games and drives tables

Revision ID: 005
Revises: 004
Create Date: 2024-12-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create live_games table
    op.create_table(
        'live_games',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('external_game_id', sa.String(255), unique=True, nullable=False, index=True),
        sa.Column('sport', sa.String(50), nullable=False, index=True),
        sa.Column('home_team', sa.String(100), nullable=False),
        sa.Column('away_team', sa.String(100), nullable=False),
        sa.Column('home_team_id', sa.String(100), nullable=True),
        sa.Column('away_team_id', sa.String(100), nullable=True),
        sa.Column('status', sa.String(50), default='scheduled', nullable=False, index=True),
        sa.Column('quarter', sa.Integer(), nullable=True),
        sa.Column('period_name', sa.String(50), nullable=True),
        sa.Column('time_remaining', sa.String(20), nullable=True),
        sa.Column('home_score', sa.Integer(), default=0, nullable=False),
        sa.Column('away_score', sa.Integer(), default=0, nullable=False),
        sa.Column('scheduled_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('actual_start', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create indexes for live_games
    op.create_index('idx_live_game_status_sport', 'live_games', ['status', 'sport'])
    op.create_index('idx_live_game_last_updated', 'live_games', ['last_updated_at'])
    op.create_index('idx_live_game_scheduled_start', 'live_games', ['scheduled_start'])
    
    # Create drives table
    op.create_table(
        'drives',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('game_id', sa.String(36), sa.ForeignKey('live_games.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('drive_number', sa.Integer(), nullable=False),
        sa.Column('external_drive_id', sa.String(255), unique=True, nullable=True),
        sa.Column('team', sa.String(100), nullable=False),
        sa.Column('team_id', sa.String(100), nullable=True),
        sa.Column('is_home_team', sa.Integer(), default=0),
        sa.Column('quarter', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.String(20), nullable=True),
        sa.Column('end_time', sa.String(20), nullable=True),
        sa.Column('start_yard_line', sa.Integer(), nullable=True),
        sa.Column('end_yard_line', sa.Integer(), nullable=True),
        sa.Column('yards_gained', sa.Integer(), nullable=True),
        sa.Column('plays_count', sa.Integer(), nullable=True),
        sa.Column('result', sa.String(50), nullable=True),
        sa.Column('points_scored', sa.Integer(), default=0),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('home_score_after', sa.Integer(), nullable=True),
        sa.Column('away_score_after', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    
    # Create indexes for drives
    op.create_index('idx_drive_game_number', 'drives', ['game_id', 'drive_number'])
    op.create_index('idx_drive_created', 'drives', ['created_at'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_drive_created', table_name='drives')
    op.drop_index('idx_drive_game_number', table_name='drives')
    
    op.drop_index('idx_live_game_scheduled_start', table_name='live_games')
    op.drop_index('idx_live_game_last_updated', table_name='live_games')
    op.drop_index('idx_live_game_status_sport', table_name='live_games')
    
    # Drop tables
    op.drop_table('drives')
    op.drop_table('live_games')

