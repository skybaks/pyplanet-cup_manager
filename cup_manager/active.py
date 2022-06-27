import asyncio
import logging

from pyplanet.conf import settings
from pyplanet.apps.core.maniaplanet import callbacks as mp_signals
from pyplanet.apps.core.trackmania import callbacks as tm_signals
from pyplanet.contrib.command import Command
from pyplanet.utils import style

from .views import MatchesView, MatchHistoryView
from .app_types import ScoreSortingPresets, TeamPlayerScore

logger = logging.getLogger(__name__)

class ActiveCupManager:
	def __init__(self, app) -> None:
		self.app = app
		self.instance = app.instance
		self.context = app.context
		self.cup_active = False
		self.display_podium_results = False
		self.match_start_times = []
		self.score_sorting = ScoreSortingPresets.UNDEFINED
		self.cached_scores_lock = asyncio.Lock()
		self.cached_scores = []
		self.cup_name = ''
		self.cup_edition_num = 0
		self.cup_map_count_target = 0


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
				admin=True, perms='cup:manage_cup', description='Signal to start cup on the next map or edit the name properties of a running cup. Usage //cup start cup_alias:str cup_edition:int').add_param(
					'config', nargs='*', required=False),
			Command(command='off', aliases=['stop'], namespace=self.app.namespace, target=self._command_stop,
				admin=True, perms='cup:manage_cup', description='Signals to the server that a cup will end on current map.'),
			Command(command='edit', aliases=[], namespace=self.app.namespace, target=self._command_edit,
				admin=True, perms='cup:manage_cup', description='Edit maps in the current cup.'),
			Command(command='mapcount', aliases=[], namespace=self.app.namespace, target=self._command_mapcount,
				admin=True, perms='cup:manage_cup', description='Set the number of maps to target for the current cup.').add_param(
					'map_count', nargs=1, type=int, default=0, required=True),

			Command(command='results', aliases=['r'], namespace=self.app.namespace, target=self._command_results,
				description='Display the standings of the current cup.'),
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
		if selected_match not in self.match_start_times:
			self.match_start_times.append(selected_match)


	async def remove_selected_match(self, selected_match: int) -> None:
		if selected_match in self.match_start_times:
			self.match_start_times.remove(selected_match)


	async def _mp_signals_flow_podium_start(self, *args, **kwargs) -> None:
		if self.display_podium_results:
			self.display_podium_results = False
			scores = await self.app.results.get_data_scores(self.match_start_times, self.score_sorting)	# type: list[TeamPlayerScore]
			index = 1
			podium_text = []
			for player_score in scores[0:10]:
				podium_text.append(f'$0cf{str(index)}. $fff{style.style_strip(player_score.nickname)} $fff[$aaa{player_score.relevant_score_str(self.score_sorting)}$fff]$0cf')
				index += 1
			if not self.cup_active:
				podium_prefix = 'Final'
			else:
				podium_prefix = 'Current'
			await self.instance.chat(f'$z$s$0cf{podium_prefix} {self.cup_name_fmt} standings: ' + ', '.join(podium_text))

			index = 1
			for player_score in scores:
				await self.instance.chat(f"$z$s$i$0cfYou are placed $fff{str(index)}$0cf in the {self.cup_name_fmt}", player_score.login)
				index += 1


	async def _tm_signals_warmup_start(self) -> None:
		if self.cup_active or self.display_podium_results:
			await self.instance.chat(f"$z$s$0cfGoing live after warmup")


	async def _tm_signals_warmup_end(self) -> None:
		if self.cup_active or self.display_podium_results:
			await self.instance.chat(f"$z$s$0cfWarmup complete, going live now!")


	async def _notify_match_start(self, match_start_time: int, **kwargs) -> None:
		if self.cup_active and match_start_time not in self.match_start_times:
			logger.info("Match start from active " + str(match_start_time))
			self.match_start_times.append(match_start_time)
			self.display_podium_results = True
			self.score_sorting = ScoreSortingPresets.get_preset(await self.instance.mode_manager.get_current_script())
			current_map_num = len(self.match_start_times)
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
		new_cup_edition = None

		if data.config and isinstance(data.config, list):
			if len(data.config) > 0:
				alias = data.config[0]
				cup_names = await self.get_cup_names()
				if alias in cup_names:
					new_cup_name = cup_names[alias]['name']
			if len(data.config) > 1:
				try:
					new_cup_edition = int(data.config[1])
				except:
					await self.instance.chat(f'$z$s$i$f00The input argument for cup_edition must be an integer', player)
					return

		if not self.cup_active:
			self.cup_active = True
			self.match_start_times = []
			self.cup_map_count_target = 0

			self.cup_name = ''
			if new_cup_name:
				self.cup_name = new_cup_name

			self.cup_edition_num = 0
			if new_cup_edition:
				self.cup_edition_num = new_cup_edition

			await self.instance.chat(f'$z$s$0cfThe {self.cup_name_fmt} will start on the next map')
		elif new_cup_name or new_cup_edition:
			self.cup_name = ''
			if new_cup_name:
				self.cup_name = new_cup_name

			self.cup_edition_num = 0
			if new_cup_edition:
				self.cup_edition_num = new_cup_edition

			await self.instance.chat(f'$z$s$i$0cfUpdated cup name and edition to: {str(self.cup_name)}, {str(self.cup_edition_num)}', player)
		else:
			await self.instance.chat(f'$z$s$i$f00A cup is already active. Use "//cup edit" to change cup maps or "//cup on cup_name:str cup_edition:int" to edit cup name and edition', player)


	async def _command_stop(self, player, data, **kwargs) -> None:
		if self.cup_active:
			self.cup_active = False
			if len(self.match_start_times) < 1:
				await self.instance.chat(f'$z$s$0cfThe {self.cup_name_fmt} has been canceled')
			elif len(self.match_start_times) == 1:
				await self.instance.chat(f'$z$s$i$0cfYou have designated this as the only map of the {self.cup_name_fmt}', player)
			else:
				await self.instance.chat(f'$z$s$0cfThis is the final map of the {self.cup_name_fmt}')


	async def _command_results(self, player, data, **kwargs) -> None:
		view = MatchHistoryView(self.app, player, init_query=self.match_start_times, init_results_view=True, init_sorting=self.score_sorting, init_title='Cup Results')
		await view.display(player=player.login)


	async def _command_edit(self, player, data, **kwargs) -> None:
		view = MatchesView(self, player)
		await view.display(player=player.login)


	async def _command_mapcount(self, player, data, **kwargs) -> None:
		self.cup_map_count_target = data.map_count
		await self.instance.chat(f'$z$s$i$0cfNumber of cup maps set to: {str(self.cup_map_count_target)}', player)
