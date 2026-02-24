"""create tbd field in tiesheet player

Revision ID: 20030657cb23
Revises: 6184d481ac47
Create Date: 2026-02-24 13:39:59.002649

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '20030657cb23'
down_revision: Union[str, Sequence[str], None] = '6184d481ac47'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Drop the existing primary key
    op.execute("ALTER TABLE tiesheet_players DROP CONSTRAINT tiesheet_players_pkey;")
    
    # Add a new primary key on the `id` column
    op.execute("ALTER TABLE tiesheet_players ADD PRIMARY KEY (id);")
    
    # Now you can safely make `user_id` nullable
    op.alter_column(
        'tiesheet_players',
        'user_id',
        existing_type=sa.UUID(),
        nullable=True,
        existing_nullable=False
    )
    
    # Add your new column `is_tbd`
    op.add_column(
        'tiesheet_players',
        sa.Column('is_tbd', sa.Boolean(), server_default=sa.text('false'), nullable=False)
    )


def downgrade() -> None:
    # Reverse operations if needed
    op.drop_column('tiesheet_players', 'is_tbd')
    
    # Make user_id NOT NULL again
    op.alter_column(
        'tiesheet_players',
        'user_id',
        existing_type=sa.UUID(),
        nullable=False
    )
    
    # Restore the old primary key if needed
    # (adjust if the original PK was composite)
    op.execute("ALTER TABLE tiesheet_players DROP CONSTRAINT tiesheet_players_pkey;")
    op.execute("ALTER TABLE tiesheet_players ADD PRIMARY KEY (tiesheet_id, user_id);")
