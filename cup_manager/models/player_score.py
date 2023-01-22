from peewee import *
from pyplanet.core.db import TimedModel


class PlayerScore(TimedModel):
	map_start_time = IntegerField(null=False, index=True)
	"""
	Server start time for a map. Identifies what match a score belongs to
	"""

	login = CharField(null=False, max_length=150, index=True)
	"""
	Player login who the score belongs to
	"""

	nickname = CharField(null=False, max_length=150)
	"""
	Player nickname who the score belongs to
	"""

	country = CharField(null=True, max_length=150)
	"""
	The player's country
	"""

	score = IntegerField(null=False)
	"""
	Score value for the player
	"""

	score2 = IntegerField(null=False)
	"""
	Additional score value for the player
	"""

	team = IntegerField(null=False, index=True)
	"""
	Team number for the player
	"""

	score_match = IntegerField(null=False, default=0)
	"""
	Match score value for the player
	"""

	class Meta:
		db_table = 'cup_manager_playerscore'
