import logging

from pyplanet.apps.config import AppConfig

from .results import ResultsCupManager
from .setup import SetupCupManager

logger = logging.getLogger(__name__)

class CupManagerApp(AppConfig):
	game_dependencies = ['trackmania_next', 'trackmania', 'shootmania']
	app_dependencies = ['core.maniaplanet', 'core.trackmania', 'core.shootmania']
	namespace = 'cup'


	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

		self.results = ResultsCupManager(self)
		self.setup = SetupCupManager(self)


	async def on_start(self):
		await self.results.on_start()
		await self.setup.on_start()

