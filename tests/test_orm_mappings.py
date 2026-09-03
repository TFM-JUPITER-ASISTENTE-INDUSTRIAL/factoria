from sqlalchemy.orm import configure_mappers

import src.storage.entities  # noqa: F401


def test_all_orm_relationships_can_be_configured():
    configure_mappers()
