"""Agrupa sensores por el segmento anterior al fallo en tag_id.

Se añade después de la primera propuesta para admitir bases donde ya se aplicó.
El seed crea los grupos y reasigna las definiciones de forma controlada.
"""
from alembic import op
import sqlalchemy as sa

revision = "e83b6a912d04"
down_revision = "d71c9a0e5f42"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sensors", sa.Column("sensor_type", sa.String(), nullable=True))
    op.create_unique_constraint(
        "uq_sensors_plc_type", "sensors", ["owner_id", "sensor_type"],
    )


def downgrade():
    op.drop_constraint("uq_sensors_plc_type", "sensors", type_="unique")
    op.drop_column("sensors", "sensor_type")
