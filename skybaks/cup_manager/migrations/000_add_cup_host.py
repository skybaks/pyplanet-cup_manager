import logging
from peewee import *
from playhouse.migrate import migrate, SchemaMigrator

from ..models.cup_model import CupInfo

logger = logging.getLogger(__name__)


def upgrade(migrator: SchemaMigrator) -> None:
	cup_host_login = CharField(max_length=150, null=True)
	cup_host_nickname = CharField(max_length=150, null=True)
	migrate(
		migrator.add_column(CupInfo._meta.db_table, 'cup_host_login', cup_host_login),
		migrator.add_column(CupInfo._meta.db_table, 'cup_host_nickname', cup_host_nickname)
	)


def downgrade(migrator: SchemaMigrator) -> None:
	pass
