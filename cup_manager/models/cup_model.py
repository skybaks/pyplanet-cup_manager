from peewee import *
from pyplanet.core.db import TimedModel


class CupInfo(TimedModel):
	cup_start_time = IntegerField(null=False, unique=True)
	"""
	Time the cup was started. Identifies what cup a match belongs to
	"""

	cup_key = CharField(null=False, max_length=150)
	"""
	Key value identifier for the cup. Defined in the local.py
	"""

	cup_name = CharField(null=False, max_length=150)
	"""
	Display name of the cup
	"""

	cup_edition = IntegerField(null=False)
	"""
	Edition number of the cup
	"""

	cup_host_login = CharField(max_length=150, null=True)
	"""
	Login of the cup host for this edition
	"""

	cup_host_nickname = CharField(max_length=150, null=True)
	"""
	Nickname of the cup host for this edition
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
