import logging
import os
from pathlib import Path

from src.config.logger import setup_logging
from src.storage.connectors.postgresql import SessionLocal
from src.storage.importers.alarm_catalog_importer import (
    import_alarm_catalogs,
)

logger = logging.getLogger(__name__)


def seed_database() -> None:
    """Importa el catalogo real de maquinas y alarmas desde CSV."""
    catalog_directory = Path(
        os.getenv(
            "ALARM_CATALOG_DIR",
            "data/alarm_catalogs",
        )
    )

    session = SessionLocal()

    try:
        result = import_alarm_catalogs(
            session=session,
            directory=catalog_directory,
        )

        session.commit()

        logger.info(
            "Catálogo importado: %s",
            result,
        )
    except Exception:
        session.rollback()
        logger.exception(
            "No se pudo importar el catálogo de alarmas"
        )
        raise
    finally:
        session.close()


if __name__ == "__main__":
    setup_logging()
    seed_database()
