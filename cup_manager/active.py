import asyncio
import logging

from pyplanet.apps.core.maniaplanet import callbacks as mp_signals
from pyplanet.contrib.command import Command
from pyplanet.utils import style

from .views import ResultsView, MatchesView
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


	async def on_start(self) -> None:
		self.context.signals.listen(mp_signals.flow.podium_start, self._mp_signals_flow_podium_start)

		await self.instance.permission_manager.register('manage_cup', 'Manage an active cup from cup_manager', app=self.app, min_level=2, namespace=self.app.namespace)

		await self.instance.command_manager.register(
			Command(command='start', aliases=['st', 'begin', 'on'], namespace=self.app.namespace, target=self._command_start,
				admin=True, perms='cup:manage_cup', description='Signals to the server that a cup will begin on the next map.'),
			Command(command='end', aliases=['e', 'stop', 'off'], namespace=self.app.namespace, target=self._command_end,
				admin=True, perms='cup:manage_cup', description='Signals to the server that a cup will end on current map.'),
			Command(command='edit', aliases=[], namespace=self.app.namespace, target=self._command_edit,
				admin=True, perms='cup:manage_cup', description='Edit maps in the current cup.'),
			Command(command='name', aliases=[], namespace=self.app.namespace, target=self._command_name,
				admin=True, perms='cup:manage_cup', description='Manage the cup name and edition.'),

			Command(command='results', aliases=['r'], namespace=self.app.namespace, target=self._command_results,
				description='Display the standings of the current cup.'),
		)

		await self.app.results.register_match_start_notify(self._notify_match_start)
		await self.app.results.register_scores_update_notify(self._notify_scores_update)


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
			scores = await self.app.results.get_data_scores(self.match_start_times, self.score_sorting)	# type: list[TeamPlayerScore]
			index = 1
			podium_text = []
			for player_score in scores[0:10]:
				podium_text.append(f'$0cf{str(index)}. $fff{style.style_strip(player_score.nickname)} $fff[$999{player_score.relevant_score_str(self.score_sorting)}$fff]$0cf')
				index += 1
			await self.instance.chat('$z$s$0cfCurrent cup standings: ' + ', '.join(podium_text))
			self.display_podium_results = False


	async def _notify_match_start(self, match_start_time: int, **kwargs) -> None:
		if self.cup_active and match_start_time not in self.match_start_times:
			logger.info("Match start from active " + str(match_start_time))
			self.match_start_times.append(match_start_time)
			self.display_podium_results = True
			self.score_sorting = ScoreSortingPresets.get_preset(await self.instance.mode_manager.get_current_script())
			current_map_num = len(self.match_start_times)
			if current_map_num == 1:
				await self.instance.chat(f'$z$s$0cfStarting cup with this map.')
			else:
				await self.instance.chat(f'$z$s$0cfStarting cup map $fff{str(current_map_num)}$0cf.')


	async def _notify_scores_update(self, match_start_time: int, **kwargs) -> None:
		if match_start_time in self.match_start_times:
			logger.info("Signaled new scores update for cup")
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
									await self.instance.chat(f"$z$s$0cfYou gained $fff{str(old_index - new_index)}$0cf positions in the overall cup. $fff[{str(old_index + 1)} ➙ {str(new_index + 1)}]", current_login)
								# Lost placements. Do we really want to rub it in?
								elif new_index > old_index:
									pass
								break
				self.cached_scores = new_scores


	async def _command_start(self, player, data, **kwargs) -> None:
		if not self.cup_active:
			await self.instance.chat(f'$z$s$0cfThe cup will start on the next map.')
			self.cup_active = True
			self.match_start_times = []
		else:
			await self.instance.chat(f'$z$s$i$f00A cup is already active. Use "//cup edit" to change cup maps.', player)


	async def _command_end(self, player, data, **kwargs) -> None:
		if self.cup_active:
			self.cup_active = False
			if len(self.match_start_times) < 1:
				await self.instance.chat(f'$z$s$0cfThe cup has been canceled.')
			elif len(self.match_start_times) == 1:
				# Dont print a message. If the cup lasts one map its implied that the single map is also the last map.
				pass
			else:
				await self.instance.chat(f'$z$s$0cfThis is the final map of the cup.')


	async def _command_results(self, player, data, **kwargs) -> None:
		view = ResultsView(self, player, self.match_start_times, self.score_sorting)
		await view.display(player=player.login)


	async def _command_edit(self, player, data, **kwargs) -> None:
		view = MatchesView(self, player)
		await view.display(player=player.login)


	async def _command_name(self, player, data, **kwargs) -> None:
		logger.error("TODO: Implement this method")
