from peewee import *
from pyplanet.core.db import TimedModel


class MatchInfo(TimedModel):
	map_start_time = IntegerField(null=False, unique=True, index=True)
	"""
	Server start time for a map. Identifies what match a score belongs to
	"""

	mode_script = CharField(null=True, max_length=150, index=True)
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

	class Meta:
		db_table = 'cup_manager_matchinfo_v1'
		indexes = (
			(('map_start_time',), True)
		)

