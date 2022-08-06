import asyncio
import logging
from datetime import datetime
import uuid
from argparse import Namespace

from pyplanet.conf import settings
from pyplanet.apps.core.maniaplanet import callbacks as mp_signals
from pyplanet.apps.core.trackmania import callbacks as tm_signals
from pyplanet.contrib.command import Command
from pyplanet.utils import style

from .views import AddRemoveCupMatchesView, CupView, CupMapsView, CupResultsView
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
		self.cup_host = None
		self._view_cache_cup_info = []	# type: list[CupInfo]
		self._view_cache_cup_maps = {}	# type: list[CupMatch]


	@property
	def cup_name_fmt(self) -> str:
		if self.cup_name:
			return '$<$fff' + self.cup_name + '$>'
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
			map_query = await self.get_data_cup_match_times(self.cup_start_time)
			if selected_match not in map_query:
				try:
					logger.debug(f"adding cup map with id {str(selected_match)}")
					await CupMatch.execute(CupMatch.insert(
						cup_start_time=self.cup_start_time,
						map_start_time=selected_match
					))
				except:
					logger.error(f"Error adding cup map to database with id {str(selected_match)}")
				await self._invalidate_view_cache_cup_maps()
			else:
				logger.debug("map already exists")


	async def remove_selected_match(self, selected_match: int) -> None:
		if self.cup_start_time > 0 and selected_match in self.match_start_times:
			self.match_start_times.remove(selected_match)
			try:
				logger.debug(f"removing cup match with id {str(selected_match)}")
				await CupMatch.execute(CupMatch.delete().where((CupMatch.cup_start_time == self.cup_start_time) & (CupMatch.map_start_time == selected_match)))
			except:
				logger.error(f"Error deleting selected match with id {str(selected_match)} from cup with id {str(self.cup_start_time)}")
			await self._invalidate_view_cache_cup_maps()


	async def _mp_signals_flow_podium_start(self, *args, **kwargs) -> None:
		if await self._current_match_in_cup():
			scores = await self.app.results.get_data_scores(self.match_start_times, self.score_sorting)	# type: list[TeamPlayerScore]
			score_ties = TeamPlayerScore.get_ties(scores)
			podium_text = []
			for player_score in scores[0:10]:
				podium_text.append(f'$0cf{str(player_score.placement)}.$fff{style.style_strip(player_score.nickname)}$fff[$aaa{player_score.relevant_score_str(self.score_sorting)}$fff]$0cf')
			if not self.cup_active:
				podium_prefix = 'Final'
				player_prefix = ''
			else:
				podium_prefix = 'Current'
				player_prefix = 'are '
			await self.instance.chat(f'$z$s$0cf{podium_prefix} {self.cup_name_fmt} standings: ' + ', '.join(podium_text))

			for player_score in scores:
				placed_text = 'placed'
				if player_score.login in score_ties:
					placed_text = 'tied for'
				await self.instance.chat(f"$ff0You {player_prefix}{placed_text} $<$fff{str(player_score.placement)}$> in the {self.cup_name_fmt}", player_score.login)


	async def _tm_signals_warmup_start(self) -> None:
		if self.cup_active or await self._current_match_in_cup():
			await self.instance.chat(f"$z$s$0cfGoing live after warmup")


	async def _tm_signals_warmup_end(self) -> None:
		if self.cup_active or await self._current_match_in_cup():
			await self.instance.chat(f"$z$s$0cfWarmup complete, going live now!")


	async def _notify_match_start(self, match_start_time: int, **kwargs) -> None:
		if self.cup_active and match_start_time not in self.match_start_times:
			logger.debug("Match start from active " + str(match_start_time))
			await self.add_selected_match(match_start_time)
			current_map_num = len(self.match_start_times)
			if self.cup_map_count_target > 1:
				await self.instance.chat(f'$z$s$0cfStarting {self.cup_name_fmt} map $<$fff{str(current_map_num)}$> of $<$fff{str(self.cup_map_count_target)}$>')
			else:
				if current_map_num == 1:
					await self.instance.chat(f'$z$s$0cfStarting {self.cup_name_fmt} with this map')
				else:
					await self.instance.chat(f'$z$s$0cfStarting {self.cup_name_fmt} map $<$fff{str(current_map_num)}$>')

			if current_map_num > 1:
				# If not map 1 then dump out player diffs
				scores = await self.app.results.get_data_scores(self.match_start_times, self.score_sorting)	# type: list[TeamPlayerScore]
				score_ties = TeamPlayerScore.get_ties(scores)
				for score_index in range(0, len(scores)-1):
					current_score = scores[score_index]
					if current_score.login in score_ties and len(score_ties[current_score.login]) > 0:
						await self.instance.chat(
							f"$ff0You are tied with {', '.join([f'$<$fff{style.style_strip(tie_score.nickname)}$>' for tie_score in score_ties[current_score.login]])} in the {self.cup_name_fmt}",
							current_score.login
						)
					elif score_index-1 >= 0:
						ahead_score = scores[score_index-1]
						await self.instance.chat(
							f"$ff0You are behind $<$fff{style.style_strip(ahead_score.nickname)}$> by $<$fff{TeamPlayerScore.diff_scores_str(current_score, ahead_score, self.score_sorting)}$> in the {self.cup_name_fmt}",
							current_score.login
						)
					elif score_index+1 < len(scores):
						behind_score = scores[score_index+1]
						await self.instance.chat(
							f"$ff0You are leading $<$fff{style.style_strip(behind_score.nickname)}$> by $<$fff{TeamPlayerScore.diff_scores_str(current_score, behind_score, self.score_sorting)}$> in the {self.cup_name_fmt}",
							current_score.login
						)

			# End the cup if using a map count target
			if self.cup_map_count_target > 0 and current_map_num >= self.cup_map_count_target:
				await self._command_stop(self.cup_host, None)


	async def _notify_scores_update(self, match_start_time: int, **kwargs) -> None:
		if match_start_time in self.match_start_times:
			async with self.cached_scores_lock:
				new_scores = await self.app.results.get_data_scores(self.match_start_times, self.score_sorting)	# type: list[TeamPlayerScore]
				if self.cached_scores and new_scores != self.cached_scores:
					for new_score in new_scores:
						prev_score = next((s for s in self.cached_scores if s.login == new_score.login), None)	# type: TeamPlayerScore
						if prev_score and new_score.placement < prev_score.placement:
							await self.instance.chat(
								f"$ff0You gained $<$fff{str(prev_score.placement - new_score.placement)}$> positions in the {self.cup_name_fmt}. $fff[{str(prev_score.placement)} ➙ {str(new_score.placement)}]",
								new_score.login
							)
						elif prev_score and new_score.placement > prev_score.placement:
							# Lost placements. Do we really want to rub it in?
							pass
				self.cached_scores = new_scores


	async def _command_start(self, player, data, **kwargs) -> None:
		new_cup_name = None
		new_cup_preset_on = None
		new_cup_map_count_target = 0
		new_cup_key_name = ''

		if data.cup_alias:
			cup_names = await self.get_cup_names()
			for lookup_name in cup_names.keys():
				if lookup_name.lower() == data.cup_alias.lower():
					new_cup_key_name = lookup_name
					new_cup_name = cup_names[new_cup_key_name]['name']
					if 'preset_on' in cup_names[new_cup_key_name]:
						new_cup_preset_on = cup_names[new_cup_key_name]['preset_on']
					if 'map_count' in cup_names[new_cup_key_name]:
						new_cup_map_count_target = cup_names[new_cup_key_name]['map_count']
					break
			else:
				logger.error(f"Cup key name \"{data.cup_alias}\" not found using //cup on command")
				await self.instance.chat(f"$f00Cup key name not found. Configured names are: {', '.join([f'$<$fff{kname}$>' for kname in cup_names.keys()])}", player.login)
				return

		self.cup_host = player

		if not self.cup_active and await self._current_match_in_cup():
			self.cup_active = True
			self.cup_map_count_target = 0
			await self.instance.chat(f'$ff0Cup reactivated and map count reset to $<$fff{str(self.cup_map_count_target)}$>. Use $<$fff//cup edit$> to add/remove maps from scoring, use $<$fff//cup mapcount$> to set the actual map count, and use $<$fff//cup off$> to manually end the cup while the final map is being played', player)

		elif not self.cup_active or new_cup_name:
			self.cup_key_name = new_cup_key_name
			self.cup_name = ''
			if new_cup_name:
				self.cup_name = new_cup_name

			if not self.cup_active:
				self.cup_active = True
				self.match_start_times = []
				self.cup_map_count_target = 0
				self.cup_start_time = int(datetime.now().timestamp())
				async with self.cached_scores_lock:
					self.cached_scores = []
				await self.instance.chat(f'$z$s$0cfThe {self.cup_name_fmt} will start on the next map')

			self.cup_edition_num = await self._lookup_previous_edition() + 1
			await self.instance.chat(f'$ff0Set edition to $<$fff{str(self.cup_edition_num)}$> based on previous cups. Use $<$fff//cup edition$> if this is incorrect', player)

			if new_cup_preset_on:
				await self.app.setup.command_setup(player, Namespace(**{'preset': new_cup_preset_on}))

			if new_cup_map_count_target > 0:
				self.cup_map_count_target = new_cup_map_count_target
				await self.instance.chat(f'$ff0Set map count to $<$fff{str(self.cup_map_count_target)}$>. Use $<$fff//cup mapcount$> if this is incorrect', player)

			await self._save_cup_info()

		else:
			await self.instance.chat(f'$f00A cup is already active. Use $<$fff//cup edit$> to change cup maps or $<$fff//cup on cup_name:str$> to edit cup name', player)


	async def _command_stop(self, player, data, **kwargs) -> None:
		if self.cup_active:
			self.cup_active = False
			if len(self.match_start_times) < 1:
				await self.instance.chat(f'$z$s$0cfThe {self.cup_name_fmt} has been canceled')
				await CupInfo.execute(CupInfo.delete().where(CupInfo.cup_start_time.in_([self.cup_start_time])))
				await self._invalidate_view_cache_cup_info()
			elif len(self.match_start_times) == 1:
				await self.instance.chat(f'$ff0You have designated this as the only map of the {self.cup_name_fmt}', player)
			else:
				await self.instance.chat(f'$z$s$0cfThis is the final map of the {self.cup_name_fmt}')

			cup_names = await self.get_cup_names()
			if self.cup_key_name in cup_names and 'preset_off' in cup_names[self.cup_key_name]:
				await self.app.setup.command_setup(player, Namespace(**{'preset': cup_names[self.cup_key_name]['preset_off']}))


	async def _command_results(self, player, data, **kwargs) -> None:
		await self.open_view_results(player, self.match_start_times, self.cup_start_time)


	async def _command_cups(self, player, data, **kwargs) -> None:
		await self.open_view_cups(player)


	async def _command_edit(self, player, data, **kwargs) -> None:
		view = AddRemoveCupMatchesView(self, player)
		await view.display(player=player.login)


	async def _command_mapcount(self, player, data, **kwargs) -> None:
		if self.cup_active:
			self.cup_map_count_target = data.map_count
			await self.instance.chat(f'$ff0Number of cup maps set to: $<$fff{str(self.cup_map_count_target)}$>', player)
		else:
			await self.instance.chat(f'$f00No cup is currently active. Start a cup using $<$fff//cup on$> and then run this command', player)


	async def _command_edition(self, player, data, **kwargs) -> None:
		if self.cup_active:
			self.cup_edition_num = data.cup_edition
			await self._save_cup_info()
			await self.instance.chat(f'$ff0Cup edition set to: $<$fff{str(self.cup_edition_num)}$>', player)
		else:
			await self.instance.chat(f'$f00No cup is currently active. Start a cup using $<$fff//cup on$> and then run this command', player)


	async def _save_cup_info(self) -> None:
		logger.debug("Saving cup info")
		cup_query = await self.get_data_specific_cup_info(self.cup_start_time)
		save_cup_name = self.cup_name
		save_key_name = self.cup_key_name
		save_edition = self.cup_edition_num
		save_host_login = self.cup_host.login if self.cup_host else ''
		save_host_nickname = self.cup_host.nickname if self.cup_host else ''
		if not self.cup_name:
			save_cup_name = 'Cup'
			# Use a silly key name so we never get overlap on the edition lookup for anonymous cups
			save_key_name = 'unnamed_cup_' + str(uuid.uuid4())
		if cup_query:
			logger.debug("Info already exists, updating")
			await CupInfo.execute(
				CupInfo.update(
					cup_key=save_key_name,
					cup_name=save_cup_name,
					cup_edition=save_edition,
					cup_host_login=save_host_login,
					cup_host_nickname=save_host_nickname
				).where(
					CupInfo.cup_start_time == self.cup_start_time
				)
			)
		else:
			logger.debug("no existing entry, creating")
			await CupInfo.execute(
				CupInfo.insert(
					cup_start_time=self.cup_start_time,
					cup_key=save_key_name,
					cup_name=save_cup_name,
					cup_edition=save_edition,
					cup_host_login=save_host_login,
					cup_host_nickname=save_host_nickname
				)
			)
		await self._invalidate_view_cache_cup_info()


	async def _lookup_previous_edition(self) -> int:
		previous_edition_num = 0
		if self.cup_key_name:
			logger.debug(f"looking up previous edition from key name: {str(self.cup_key_name)}")
			cup_query = await CupInfo.execute(
				CupInfo.select().where(
					(CupInfo.cup_key == self.cup_key_name) & (CupInfo.cup_start_time != self.cup_start_time)
				).order_by(
					CupInfo.cup_start_time.desc()
				)
			)
			if len(cup_query) > 0:
				previous_edition_num =  cup_query[0].cup_edition
		logger.debug(f"found previous edition as {str(previous_edition_num)} for key {str(self.cup_key_name)}")
		return previous_edition_num


	async def _current_match_in_cup(self) -> bool:
		return await self.app.results.get_current_match_start_time() in self.match_start_times


	async def _invalidate_view_cache_cup_info(self) -> None:
		self._view_cache_cup_info = []
		logger.debug("_invalidate_view_cache_cup_info")


	async def _invalidate_view_cache_cup_maps(self) -> None:
		self._view_cache_cup_maps = []
		logger.debug("_invalidate_view_cache_cup_maps")


	async def open_view_cups(self, player) -> None:
		view = CupView(self.app, player)
		await view.display(player=player)


	async def open_view_cup_maps(self, player, cup_start_time: int) -> None:
		view = CupMapsView(self.app, player, cup_start_time)
		await view.display(player=player)


	async def open_view_results(self, player, maps_query: 'list[int]', cup_start_time: int) -> None:
		score_sorting = await self.determine_cup_score_sorting(maps_query)
		view = CupResultsView(self.app, player, maps_query, score_sorting, cup_start_time)
		await view.display(player=player.login)


	async def get_data_cup_info(self) -> 'list[CupInfo]':
		if not self._view_cache_cup_info:
			cups_query = await CupInfo.execute(CupInfo.select().order_by(CupInfo.cup_start_time.desc()))
			if len(cups_query) > 0:
				self._view_cache_cup_info = list(cups_query)
		return self._view_cache_cup_info


	async def get_data_specific_cup_info(self, cup_start_time: int) -> CupInfo:
		all_cups = await self.get_data_cup_info()
		for cup_info in all_cups:
			if cup_info.cup_start_time == cup_start_time:
				return cup_info
		else:
			return None


	async def get_data_cup_match_times(self, cup_start_time: int) -> 'list[int]':
		if not self._view_cache_cup_maps:
			cup_maps_query = await CupMatch.execute(CupMatch.select().order_by(CupMatch.cup_start_time.desc()))
			if len(cup_maps_query) > 0:
				self._view_cache_cup_maps = list(cup_maps_query)
		return [int(map_time.map_start_time) for map_time in self._view_cache_cup_maps if map_time.cup_start_time == cup_start_time]


	async def determine_cup_score_sorting(self, matches: 'list[int]') -> ScoreSortingPresets:
		if not matches:
			return ScoreSortingPresets.UNDEFINED
		matches.sort(reverse=True)
		score_sorting = ScoreSortingPresets.UNDEFINED
		matches_data = await self.app.results.get_data_specific_matches([matches[0]])	# type: list[MatchInfo]
		if len(matches_data) > 0:
			score_sorting = ScoreSortingPresets.get_preset(matches_data[0].mode_script)
			logger.debug(f"score sorting is {str(score_sorting)} from map with id {str(matches[0])}")
		else:
			score_sorting = ScoreSortingPresets.get_preset(await self.instance.mode_manager.get_current_script())
			logger.debug(f"no scores entry for map with id {str(matches[0])}. return sorting based on current script to {str(score_sorting)}")
		return score_sorting
