import logging

from pyplanet.apps.core.maniaplanet import callbacks as mp_signals
from pyplanet.contrib.command import Command
from pyplanet.utils import style

from .views import ResultsView
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


	async def on_start(self) -> None:
		self.context.signals.listen(mp_signals.flow.podium_start, self._mp_signals_flow_podium_start)

		await self.instance.permission_manager.register('manage_cup', 'Manage an active cup from cup_manager', app=self.app, min_level=2, namespace=self.app.namespace)

		await self.instance.command_manager.register(
			Command(command='start', aliases=['st', 'begin'], namespace=self.app.namespace, target=self._command_start,
				admin=True, perms='cup:manage_cup', description='Signals to the server that a cup will begin on the next map.'),
			Command(command='end', aliases=['e', 'stop'], namespace=self.app.namespace, target=self._command_end,
				admin=True, perms='cup:manage_cup', description='Signals to the server that a cup will end on current map.'),
			Command(command='edit', aliases=[], namespace=self.app.namespace, target=self._command_edit,
				admin=True, perms='cup:manage_cup', description='Edit maps in the current cup.'),
			Command(command='results', aliases=['r'], namespace=self.app.namespace, target=self._command_results,
				description='Display the standings of the current cup.'),
		)

		await self.app.results.register_match_start_notify(self._notify_match_start)


	async def _mp_signals_flow_podium_start(self, *args, **kwargs) -> None:
		if self.display_podium_results:
			scores = await self.app.results.get_data_scores(self.match_start_times, self.score_sorting)	# type: list[TeamPlayerScore]
			index = 1
			podium_text = []
			for player_score in scores[0:10]:
				podium_text.append(f'$0cf{str(index)}. $fff{style.style_strip(player_score.nickname)} [{player_score.relevant_score_str(self.score_sorting)}]$0cf')
				index += 1
			await self.instance.chat('$z$s$0cf' + ', '.join(podium_text))
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
				await self.instance.chat(f'$z$s$0cfStarting cup map {str(current_map_num)}.')


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
		logger.error("TODO: Implement this method")
