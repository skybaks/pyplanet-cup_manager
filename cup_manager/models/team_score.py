from peewee import *
from pyplanet.core.db import TimedModel


class TeamScore(TimedModel):
	map_start_time = IntegerField(null=False, index=True)
	"""
	Server start time for a map. Identifies what match a score belongs to
	"""

	team_id = IntegerField(null=False, index=True)
	"""
	Identifier for the team. This matches the field assigned to each player
	"""

	name = CharField(null=False, max_length=150)
	"""
	Name of team this score belongs to
	"""

	score = IntegerField(null=False)
	"""
	Score value for the team
	"""

	class Meta:
		db_table = 'cup_manager_teamscore'