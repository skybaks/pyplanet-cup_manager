import logging

from pyplanet.contrib.command import Command

logger = logging.getLogger(__name__)

class CupCupManager:
	def __init__(self, app) -> None:
		self.app = app
		self.instance = app.instance
		self.context = app.context


	async def on_start(self) -> None:
		await self.instance.permission_manager.register('manage_cup', 'Start/Stop/Modify active cups from cup_manager', app=self.app, min_level=2, namespace=self.app.namespace)

		await self.instance.command_manager.register(
			Command(command='begin', aliases=['b'], namespace=self.app.namespace, target=self._command_begin,
			admin=True, perms='cup:manage_cup', description='Start the cup'),
			Command(command='end', aliases=['e'], namespace=self.app.namespace, target=self._command_end,
			admin=True, perms='cup:manage_cup', description='End the cup'),
		)


	async def _command_begin(self, player, data, **kwargs) -> None:
		pass


	async def _command_end(self, player, data, **kwargs) -> None:
		pass
