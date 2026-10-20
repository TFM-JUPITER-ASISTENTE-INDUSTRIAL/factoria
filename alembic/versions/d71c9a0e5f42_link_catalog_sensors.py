#Vincula el catálogo con sensores lógicos, conservando el histórico.


from alembic import op
import sqlalchemy as sa

revision = "d71c9a0e5f42"
down_revision = "324cbf6bcaee"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("sensors", sa.Column("tag_id", sa.String(), nullable=True))
    op.create_unique_constraint("uq_sensors_plc_tag", "sensors", ["owner_id", "tag_id"])
    op.add_column("alarm_definitions", sa.Column("component", sa.String(), nullable=True))
    op.add_column("alarm_definitions", sa.Column("sensor_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_alarm_definitions_sensor_id",
        "alarm_definitions", "sensors", ["sensor_id"], ["id"],
    )
    # El seed posterior crea los sensores y completa los enlaces.
    # La migración no inventa asociaciones para alarmas antiguas.


def downgrade():
    op.drop_constraint("fk_alarm_definitions_sensor_id", "alarm_definitions", type_="foreignkey")
    op.drop_column("alarm_definitions", "sensor_id")
    op.drop_column("alarm_definitions", "component")
    op.drop_constraint("uq_sensors_plc_tag", "sensors", type_="unique")
    op.drop_column("sensors", "tag_id")