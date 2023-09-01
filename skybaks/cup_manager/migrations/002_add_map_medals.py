import logging
from peewee import *
from playhouse.migrate import migrate, SchemaMigrator

from ..models import MatchInfo

logger = logging.getLogger(__name__)


def upgrade(migrator: SchemaMigrator) -> None:
    medal_author = IntegerField(null=True, default=None)
    medal_gold = IntegerField(null=True, default=None)
    medal_silver = IntegerField(null=True, default=None)
    medal_bronze = IntegerField(null=True, default=None)
    migrate(
        migrator.add_column(MatchInfo._meta.db_table, "medal_author", medal_author),
        migrator.add_column(MatchInfo._meta.db_table, "medal_gold", medal_gold),
        migrator.add_column(MatchInfo._meta.db_table, "medal_silver", medal_silver),
        migrator.add_column(MatchInfo._meta.db_table, "medal_bronze", medal_bronze),
    )


def downgrade(migrator: SchemaMigrator) -> None:
    pass
