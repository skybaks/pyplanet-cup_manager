import asyncio
import logging
from datetime import datetime
import uuid

from pyplanet.conf import settings
from pyplanet.apps.core.maniaplanet import callbacks as mp_signals
from pyplanet.apps.core.trackmania import callbacks as tm_signals
from pyplanet.contrib.command import Command
from pyplanet.utils import style

from .views import MatchesView, CupView, CupMapsView, ResultsView
from .app_types import ScoreSortingPresets, TeamPlayerScore
from .models import CupInfo, CupMatch, MatchInfo

logger = logging.getLogger(__name__)

class ActiveCupManager:
	def __init__(self, app) -> None:
		self.app = app
		self.instance = app.instance
		self.context = app.context
		self.cup_active = False
		self.match_start_times = []
		self.score_sorting = ScoreSortingPresets.UNDEFINED
		self.cached_scores_lock = asyncio.Lock()
		self.cached_scores = []
		self.cup_key_name = ''
		self.cup_name = ''
		self.cup_edition_num = 0
		self.cup_map_count_target = 0
		self.cup_start_time = 0
		self._view_cache_cup_info = {}
		self._view_cache_cup_maps = {}


	@property
	def cup_name_fmt(self) -> str:
		if self.cup_name:
			return '$<$fff' + style.style_strip(self.cup_name) + '$>'
		else:
			return 'cup'


	async def on_start(self) -> None:
		self.context.signals.listen(mp_signals.flow.podium_start, self._mp_signals_flow_podium_start)
		self.context.signals.listen(tm_signals.warmup_start, self._tm_signals_warmup_start)
		self.context.signals.listen(tm_signals.warmup_end, self._tm_signals_warmup_end)

		await self.instance.permission_manager.register('manage_cup', 'Manage an active cup from cup_manager', app=self.app, min_level=2, namespace=self.app.namespace)

		await self.instance.command_manager.register(
			Command(command='on', aliases=['start'], namespace=self.app.namespace, target=self._command_start,
				admin=True, perms='cup:manage_cup', description='Signal to start cup on the next map or edit the name properties of a running cup.').add_param(
					'cup_alias', type=str, required=False),
			Command(command='off', aliases=['stop'], namespace=self.app.namespace, target=self._command_stop,
				admin=True, perms='cup:manage_cup', description='Signals to the server that a cup will end on current map.'),
			Command(command='edit', aliases=[], namespace=self.app.namespace, target=self._command_edit,
				admin=True, perms='cup:manage_cup', description='Edit maps in the current cup.'),
			Command(command='mapcount', aliases=[], namespace=self.app.namespace, target=self._command_mapcount,
				admin=True, perms='cup:manage_cup', description='Set the number of maps to target for the current cup.').add_param(
					'map_count', nargs=1, type=int, default=0, required=True),
			Command(command='edition', aliases=[], namespace=self.app.namespace, target=self._command_edition,
				admin=True, perms='cup:manage_cup', description='Force the edition of the current cup.').add_param(
					'cup_edition', nargs=1, type=int, required=True),
			Command(command='cups', aliases=[], namespace=self.app.namespace, target=self._command_cups,
				admin=True, perms='cup:manage_cup', description='Display current and past cups.'),

			Command(command='results', aliases=['r'], namespace=self.app.namespace, target=self._command_results,
				description='Display the standings of the current cup.'),
			Command(command='cups', aliases=[], namespace=self.app.namespace, target=self._command_cups,
				description='Display current and past cups.'),
		)

		await self.app.results.register_match_start_notify(self._notify_match_start)
		await self.app.results.register_scores_update_notify(self._notify_scores_update)


	async def get_cup_names(self) -> 'dict[str, dict]':
		cup_names = {}
		try:
			cup_names = settings.CUP_MANAGER_NAMES
		except:
			logger.error('Error reading CUP_MANAGER_NAMES from local.py')
		return cup_names


	async def get_selected_matches(self) -> 'list[int]':
		return self.match_start_times


	async def add_selected_match(self, selected_match: int) -> None:
		if self.cup_start_time > 0 and selected_match not in self.match_start_times:
			self.match_start_times.append(selected_match)
			self.score_sorting = await self.determine_cup_score_sorting(self.match_start_times)
			map_query = await CupMatch.execute(CupMatch.select().where((CupMatch.cup_start_time == self.cup_start_time) & (CupMatch.map_start_time == selected_match)))
			if len(map_query) == 0:
				try:
					logger.info(f"adding cup map with id {str(selected_match)}")
					await CupMatch.execute(CupMatch.insert(
						cup_start_time=self.cup_start_time,
						map_start_time=selected_match
					))
				except:
					logger.error(f"Error adding cup map to database with id {str(selected_match)}")
			else:
				logger.info("map already exists")


	async def remove_selected_match(self, selected_match: int) -> None:
		if self.cup_start_time > 0 and selected_match in self.match_start_times:
			self.match_start_times.remove(selected_match)
			try:
				logger.info(f"removing cup match with id {str(selected_match)}")
				await CupMatch.execute(CupMatch.delete().where((CupMatch.cup_start_time == self.cup_start_time) & (CupMatch.map_start_time == selected_match)))
			except:
				logger.error(f"Error deleting selected match with id {str(selected_match)} from cup with id {str(self.cup_start_time)}")


	async def _mp_signals_flow_podium_start(self, *args, **kwargs) -> None:
		if await self._current_match_in_cup():
			scores = await self.app.results.get_data_scores(self.match_start_times, self.score_sorting)	# type: list[TeamPlayerScore]
			podium_text = []
			for player_score in scores[0:10]:
				podium_text.append(f'$0cf{str(player_score.placement)}. $fff{style.style_strip(player_score.nickname)} $fff[$aaa{player_score.relevant_score_str(self.score_sorting)}$fff]$0cf')
			if not self.cup_active:
				podium_prefix = 'Final'
			else:
				podium_prefix = 'Current'
			await self.instance.chat(f'$z$s$0cf{podium_prefix} {self.cup_name_fmt} standings: ' + ', '.join(podium_text))

			for player_score in scores:
				await self.instance.chat(f"$z$s$i$0cfYou are placed $fff{str(player_score.placement)}$0cf in the {self.cup_name_fmt}", player_score.login)


	async def _tm_signals_warmup_start(self) -> None:
		if self.cup_active or await self._current_match_in_cup():
			await self.instance.chat(f"$z$s$0cfGoing live after warmup")


	async def _tm_signals_warmup_end(self) -> None:
		if self.cup_active or await self._current_match_in_cup():
			await self.instance.chat(f"$z$s$0cfWarmup complete, going live now!")


	async def _notify_match_start(self, match_start_time: int, **kwargs) -> None:
		if self.cup_active and match_start_time not in self.match_start_times:
			logger.info("Match start from active " + str(match_start_time))
			await self.add_selected_match(match_start_time)
			current_map_num = len(self.match_start_times)
			if self.cup_map_count_target > 0:
				await self.instance.chat(f'$z$s$0cfStarting {self.cup_name_fmt} map $fff{str(current_map_num)}$0cf of $fff{str(self.cup_map_count_target)}$0cf')
			else:
				if current_map_num == 1:
					await self.instance.chat(f'$z$s$0cfStarting {self.cup_name_fmt} with this map')
				else:
					await self.instance.chat(f'$z$s$0cfStarting {self.cup_name_fmt} map $fff{str(current_map_num)}$0cf')

				# If not map 1 then dump out player diffs
				scores = await self.app.results.get_data_scores(self.match_start_times, self.score_sorting)	# type: list[TeamPlayerScore]
				for score_index in range(0, len(scores)-1):
					current_score = scores[score_index]
					if score_index-1 >= 0:
						ahead_score = scores[score_index-1]
						await self.instance.chat(
							f"$z$s$i$0cfYou are behind $fff{style.style_strip(ahead_score.nickname)}$0cf by $fff{TeamPlayerScore.diff_scores_str(current_score, ahead_score, self.score_sorting)}$0cf in the {self.cup_name_fmt}",
							current_score.login
						)
					elif score_index+1 < len(scores):
						behind_score = scores[score_index+1]
						await self.instance.chat(
							f"$z$s$i$0cfYou are leading $fff{style.style_strip(behind_score.nickname)}$0cf by $fff{TeamPlayerScore.diff_scores_str(current_score, behind_score, self.score_sorting)}$0cf in the {self.cup_name_fmt}",
							current_score.login
						)


	async def _notify_scores_update(self, match_start_time: int, **kwargs) -> None:
		if match_start_time in self.match_start_times:
			async with self.cached_scores_lock:
				new_scores = await self.app.results.get_data_scores(self.match_start_times, self.score_sorting)	# type: list[TeamPlayerScore]
				if self.cached_scores and new_scores != self.cached_scores:
					# Compare scores to find if players gained placement positions
					for new_index in range(0, len(new_scores)):
						current_login = new_scores[new_index].login
						for old_index in range(0, len(self.cached_scores)):
							if current_login == self.cached_scores[old_index].login:
								# Gained placements
								if new_index < old_index:
									await self.instance.chat(f"$z$s$i$0cfYou gained $fff{str(old_index - new_index)}$0cf positions in the {self.cup_name_fmt}. $fff[{str(old_index + 1)} ➙ {str(new_index + 1)}]", current_login)
								# Lost placements. Do we really want to rub it in?
								elif new_index > old_index:
									pass
								break
				self.cached_scores = new_scores


	async def _command_start(self, player, data, **kwargs) -> None:
		new_cup_name = None

		if data.cup_alias:
			cup_names = await self.get_cup_names()
			if data.cup_alias in cup_names:
				new_cup_name = cup_names[data.cup_alias]['name']

		if not self.cup_active:
			self.cup_active = True
			self.match_start_times = []
			self.cup_map_count_target = 0
			self.cup_start_time = int(datetime.now().timestamp())

			self.cup_name = ''
			if new_cup_name:
				self.cup_key_name = data.cup_alias
				self.cup_name = new_cup_name

			self.cup_edition_num = await self._lookup_previous_edition() + 1
			await self.instance.chat(f'$z$s$i$0cfSet edition to $<$fff{str(self.cup_edition_num)}$> based on previous cups. Use "//cup edition" if this is incorrect', player)

			await self._save_cup_info()
			await self.instance.chat(f'$z$s$0cfThe {self.cup_name_fmt} will start on the next map')
		elif new_cup_name:
			self.cup_name = ''
			if new_cup_name:
				self.cup_key_name = data.cup_alias
				self.cup_name = new_cup_name

			self.cup_edition_num = await self._lookup_previous_edition() + 1

			await self._save_cup_info()
			await self.instance.chat(f'$z$s$i$0cfUpdated cup name and edition to Name: $<$fff{str(self.cup_name)}$> Edition: $<$fff{str(self.cup_edition_num)}$>', player)
		else:
			await self.instance.chat(f'$z$s$i$f00A cup is already active. Use "//cup edit" to change cup maps or "//cup on cup_name:str" to edit cup name', player)


	async def _command_stop(self, player, data, **kwargs) -> None:
		if self.cup_active:
			self.cup_active = False
			if len(self.match_start_times) < 1:
				await self.instance.chat(f'$z$s$0cfThe {self.cup_name_fmt} has been canceled')
				await CupInfo.execute(CupInfo.delete().where(CupInfo.cup_start_time.in_([self.cup_start_time])))
			elif len(self.match_start_times) == 1:
				await self.instance.chat(f'$z$s$i$0cfYou have designated this as the only map of the {self.cup_name_fmt}', player)
			else:
				await self.instance.chat(f'$z$s$0cfThis is the final map of the {self.cup_name_fmt}')


	async def _command_results(self, player, data, **kwargs) -> None:
		await self.open_view_results(player, self.match_start_times, self.cup_start_time)


	async def _command_cups(self, player, data, **kwargs) -> None:
		await self.open_view_cups(player)


	async def _command_edit(self, player, data, **kwargs) -> None:
		view = MatchesView(self, player)
		await view.display(player=player.login)


	async def _command_mapcount(self, player, data, **kwargs) -> None:
		if self.cup_active:
			self.cup_map_count_target = data.map_count
			await self.instance.chat(f'$z$s$i$0cfNumber of cup maps set to: $<$fff{str(self.cup_map_count_target)}$>', player)
		else:
			await self.instance.chat(f'$z$s$i$f00No cup is currently active. Start a cup using "//cup on" and then run this command', player)


	async def _command_edition(self, player, data, **kwargs) -> None:
		if self.cup_active:
			self.cup_edition_num = data.cup_edition
			await self._save_cup_info()
			await self.instance.chat(f'$z$s$i$0cfCup edition set to: $<$fff{str(self.cup_edition_num)}$>', player)
		else:
			await self.instance.chat(f'$z$s$i$f00No cup is currently active. Start a cup using "//cup on" and then run this command', player)


	async def _save_cup_info(self) -> None:
		logger.info("Saving cup info")
		cup_query = await CupInfo.execute(CupInfo.select().where(CupInfo.cup_start_time.in_([self.cup_start_time])))
		save_cup_name = self.cup_name
		save_key_name = self.cup_key_name
		save_edition = self.cup_edition_num
		if not self.cup_name:
			save_cup_name = 'Cup'
			# Use a silly key name so we never get overlap on the edition lookup for anonymous cups
			save_key_name = 'unnamed_cup_' + str(uuid.uuid4())
		if len(cup_query) > 0:
			logger.info("Info already exists, updating")
			await CupInfo.execute(
				CupInfo.update(
					cup_key=save_key_name,
					cup_name=save_cup_name,
					cup_edition=save_edition
				).where(
					CupInfo.cup_start_time == self.cup_start_time
				)
			)
		else:
			logger.info("no existing entry, creating")
			await CupInfo.execute(
				CupInfo.insert(
					cup_start_time=self.cup_start_time,
					cup_key=save_key_name,
					cup_name=save_cup_name,
					cup_edition=save_edition
				)
			)


	async def _lookup_previous_edition(self) -> int:
		previous_edition_num = 0
		if self.cup_key_name:
			logger.info(f"looking up previous edition from key name: {str(self.cup_key_name)}")
			cup_query = await CupInfo.execute(
				CupInfo.select().where(
					(CupInfo.cup_key == self.cup_key_name) & (CupInfo.cup_start_time == self.cup_start_time)
				).order_by(
					CupInfo.cup_start_time.desc()
				)
			)
			if len(cup_query) > 0:
				previous_edition_num =  cup_query[0].cup_edition
		logger.info(f"found previous edition as {str(previous_edition_num)} for key {str(self.cup_key_name)}")
		return previous_edition_num


	async def _current_match_in_cup(self) -> bool:
		return await self.app.results.get_current_match_start_time() in self.match_start_times


	async def open_view_cups(self, player) -> None:
		view = CupView(self.app, player)
		await view.display(player=player)


	async def open_view_cup_maps(self, player, cup_start_time: int) -> None:
		view = CupMapsView(self.app, player, cup_start_time)
		await view.display(player=player)


	async def open_view_results(self, player, maps_query: 'list[int]', cup_start_time: int) -> None:
		score_sorting = await self.determine_cup_score_sorting(maps_query)
		view = ResultsView(self.app, player, maps_query, score_sorting, cup_start_time)
		await view.display(player=player.login)


	async def get_data_cup_infos(self) -> 'list[CupInfo]':
		# TODO: Add view cache
		cups_query = await CupInfo.execute(CupInfo.select().order_by(CupInfo.cup_start_time.desc()))
		return list(cups_query)


	async def get_data_cup_info(self, cup_start_time: int) -> CupInfo:
		# TODO: Add view cache
		cups_query = await CupInfo.execute(CupInfo.select().where(CupInfo.cup_start_time.in_([cup_start_time])))
		if len(cups_query) > 0:
			return cups_query[0]
		return None


	async def get_data_cup_match_times(self, cup_start_time: int) -> 'list[int]':
		# TODO: Add view cache
		cup_maps_query = await CupMatch.execute(CupMatch.select().where(CupMatch.cup_start_time.in_([cup_start_time])))
		return [int(map_time.map_start_time) for map_time in list(cup_maps_query)]


	async def determine_cup_score_sorting(self, matches: 'list[int]') -> ScoreSortingPresets:
		matches.sort(reverse=True)
		score_sorting = ScoreSortingPresets.UNDEFINED
		all_match_data = await self.app.results.get_data_matches()	# type: list[MatchInfo]
		for match_data in all_match_data:
			if match_data.map_start_time == matches[0]:
				score_sorting = ScoreSortingPresets.get_preset(match_data.mode_script)
				logger.info(f"update score sorting to {str(score_sorting)} from map with id {str(matches[0])}")
				break
		else:
			score_sorting = ScoreSortingPresets.get_preset(await self.instance.mode_manager.get_current_script())
			logger.info(f"no scores entry for map with id {str(matches[0])}. update sorting based on current script to {str(score_sorting)}")
		return score_sorting
