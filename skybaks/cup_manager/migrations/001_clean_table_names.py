import logging
from peewee import *
from playhouse.migrate import migrate, SchemaMigrator
from pyplanet.core.db import TimedModel

from ..models import CupInfo, CupMatch, MatchInfo, PlayerScore

logger = logging.getLogger(__name__)


def upgrade(migrator: SchemaMigrator) -> None:
    try:
        current_tables = TimedModel._meta.database.get_tables()

        # The renamed tables are created before we can migrate. need to drop them
        # so we can rename existing ones.

        if "cup_manager_cupinfo_v1" in current_tables:
            if (
                "cup_manager_cupinfo" in current_tables
                and "cup_manager_cupinfo" == CupInfo._meta.db_table
            ):
                CupInfo.drop_table()
            migrate(
                migrator.rename_table("cup_manager_cupinfo_v1", "cup_manager_cupinfo")
            )

        if "cup_manager_cupmatch_v1" in current_tables:
            if (
                "cup_manager_cupmatch" in current_tables
                and "cup_manager_cupmatch" == CupMatch._meta.db_table
            ):
                CupMatch.drop_table()
            migrate(
                migrator.rename_table("cup_manager_cupmatch_v1", "cup_manager_cupmatch")
            )

        if "cup_manager_matchinfo_v1" in current_tables:
            if (
                "cup_manager_matchinfo" in current_tables
                and "cup_manager_matchinfo" == MatchInfo._meta.db_table
            ):
                MatchInfo.drop_table()
            migrate(
                migrator.rename_table(
                    "cup_manager_matchinfo_v1", "cup_manager_matchinfo"
                )
            )

        if "cup_manager_playerscore_v2" in current_tables:
            if (
                "cup_manager_playerscore" in current_tables
                and "cup_manager_playerscore" == PlayerScore._meta.db_table
            ):
                PlayerScore.drop_table()
            migrate(
                migrator.rename_table(
                    "cup_manager_playerscore_v2", "cup_manager_playerscore"
                )
            )
    except Exception as e:
        logger.exception(e)
        logger.error("Migration failed!")


def downgrade(migrator: SchemaMigrator) -> None:
    pass
