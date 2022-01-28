from peewee import *
from pyplanet.core.db import TimedModel


class PlayerScore(TimedModel):
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

	map_start_time = IntegerField(null=False, index=True)
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

	class Meta:
		db_table = 'cup_manager_player_score'
		indexes = (
			(('login', 'map_start_time'), True),
		)
