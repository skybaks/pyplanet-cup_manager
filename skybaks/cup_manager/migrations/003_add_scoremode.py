import logging
from peewee import *
from playhouse.migrate import migrate, SchemaMigrator

from ..models import CupInfo

logger = logging.getLogger(__name__)


def upgrade(migrator: SchemaMigrator) -> None:
    cup_scoremode = CharField(max_length=150, null=True)
    migrate(
        migrator.add_column(CupInfo._meta.db_table, "cup_scoremode", cup_scoremode),
    )


def downgrade(migrator: SchemaMigrator) -> None:
    pass
