from peewee import *
from pyplanet.core.db import TimedModel


class MatchInfo(TimedModel):
    map_start_time = IntegerField(null=False, unique=True, index=True)
    """
	Server start time for a map. Identifies what match a score belongs to
	"""

    mode_script = CharField(null=True, max_length=150)
    """
	Name of the mode script this score was recorded in
	"""

    map_name = CharField(null=True, max_length=150)
    """
	Name of the map this score was recorded on
	"""

    map_uid = CharField(null=False, max_length=50)
    """
	The unique UID of the map file
	"""

    mx_id = CharField(null=True, max_length=50)
    """
	The unique UID of the map file
	"""

    medal_author = IntegerField(null=True, default=None)
    """
	The time of the author medal in milliseconds
	"""

    medal_gold = IntegerField(null=True, default=None)
    """
	The time of the gold medal in milliseconds
	"""

    medal_silver = IntegerField(null=True, default=None)
    """
	The time of the silver medal in milliseconds
	"""

    medal_bronze = IntegerField(null=True, default=None)
    """
	The time of the bronze medal in milliseconds
	"""

    class Meta:
        db_table = "cup_manager_matchinfo"
