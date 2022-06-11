import logging

from pyplanet.apps.core.maniaplanet import callbacks as mp_signals
from pyplanet.contrib.command import Command

from .views import ResultsView

logger = logging.getLogger(__name__)

class ActiveCupManager:
	def __init__(self, app) -> None:
		self.app = app
		self.instance = app.instance
		self.context = app.context
		self._cup_active = False
		self._display_podium_results = False
		self._match_start_times = []


	async def on_start(self) -> None:
		self.context.signals.listen(mp_signals.flow.podium_start, self._mp_signals_flow_podium_start)

		await self.instance.permission_manager.register('manage_cup', 'Manage an active cup from cup_manager', app=self.app, min_level=2, namespace=self.app.namespace)

		await self.instance.command_manager.register(
			Command(command='start', aliases=['st'], namespace=self.app.namespace, target=self._command_start,
				admin=True, perms='cup:manage_cup', description='Signals to the server that a cup will begin on the next map.'),
			Command(command='end', aliases=['e'], namespace=self.app.namespace, target=self._command_end,
				admin=True, perms='cup:manage_cup', description='Signals to the server that a cup will end on current map.'),
			Command(command='results', aliases=['r'], namespace=self.app.namespace, target=self._command_results,
				description='Display the standings of the current cup.'),
		)

		await self.app.results.register_match_start_notify(self._notify_match_start)


	async def _mp_signals_flow_podium_start(self, *args, **kwargs) -> None:
		if self._display_podium_results:
			scores = await self.app.results.get_data_scores(self._match_start_times, '')
			logger.info("TODO:")
			logger.info(str(scores))
			self._display_podium_results = False


	async def _notify_match_start(self, match_start_time: int, **kwargs) -> None:
		logger.info("Match start from active " + str(match_start_time))
		if self._cup_active and match_start_time not in self._match_start_times:
			self._match_start_times.append(match_start_time)
			self._display_podium_results = True


	async def _command_start(self, player, data, **kwargs) -> None:
		if not self._cup_active:
			await self.instance.chat(f'$z$s$0cfThe cup will start on the next map.')
			self._cup_active = True
			self._match_start_times = []


	async def _command_end(self, player, data, **kwargs) -> None:
		if self._cup_active:
			self._cup_active = False
			if len(self._match_start_times) < 1:
				await self.instance.chat(f'$z$s$0cfThe cup has been canceled.')
			elif len(self._match_start_times) == 1:
				# Dont print a message. If the cup lasts one map its implied that the single map is also the last map.
				pass
			else:
				await self.instance.chat(f'$z$s$0cfThis is the final map of the cup.')


	async def _command_results(self, player, data, **kwargs) -> None:
		# TODO: Hardcoded ids for testing only  ＜（＾－＾）＞
		view = ResultsView(self, player, [1659377650,1649585755,1659377651,1651977625,1659379651,1659379752])
		await view.display(player=player.login)
