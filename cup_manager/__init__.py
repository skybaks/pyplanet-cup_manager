from pyplanet.apps.config import AppConfig


class CupManagerApp(AppConfig):

	game_dependencies = ['trackmania_next', 'trackmania', 'shootmania']
	app_dependencies = ['core.maniaplanet', 'core.trackmania', 'core.shootmania']

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	async def on_init(self):
		await super().on_init()

	async def on_start(self):
		await super().on_start()

	async def on_stop(self):
		await super().on_stop()

	async def on_destroy(self):
		await super().on_destroy()