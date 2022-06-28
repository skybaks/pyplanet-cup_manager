from peewee import *
from pyplanet.core.db import TimedModel


class CupInfo(TimedModel):
	cup_start_time = IntegerField(null=False, unique=True)
	"""
	Time the cup was started. Identifies what cup a match belongs to
	"""

	cup_name = CharField(null=False, max_length=150)
	"""
	Display name of the cup
	"""

	cup_edition = IntegerField(null=False)
	"""
	Edition number of the cup
	"""

	class Meta:
		db_table = 'cup_manager_cupinfo_v1'


class CupMatch(TimedModel):
	cup_start_time = IntegerField(null=False)
	"""
	Server start time for a cup. Used as a unique id
	"""

	map_start_time = IntegerField(null=False)
	"""
	Server start time for a map. Used as a unique id
	"""

	class Meta:
		db_table = 'cup_manager_cupmatch_v1'
