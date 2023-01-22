import logging
from peewee import *
from playhouse.migrate import migrate, SchemaMigrator

from ..models import PlayerScore

logger = logging.getLogger(__name__)


def upgrade(migrator: SchemaMigrator) -> None:
	score_match = IntegerField(null=False, default=0)
	migrate(
		migrator.add_column(PlayerScore._meta.db_table, 'score_match', score_match),
	)


def downgrade(migrator: SchemaMigrator) -> None:
	pass
