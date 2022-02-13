import logging
from pandas import DataFrame

from .single_instance_view import SingleInstanceView

logger = logging.getLogger(__name__)

class PresetsView(SingleInstanceView):

	template_name = 'cup_manager/presets.xml'

	title = 'Preset Setups'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'NewTrack'

	def __init__(self, app) -> None:
		super().__init__(app, 'cup_manager.views.presets_view_displayed')
		self.preset_page = 1
		self.num_presets_per_page = 5

		self.subscribe('presets_button_close', self.close)


	async def handle_catch_all(self, player, action, values, **kwargs):
		logger.info(f"called handle_catch_all for action '{action}'")
		return await super().handle_catch_all(player, action, values, **kwargs)


	async def get_context_data(self):
		context = await super().get_context_data()

		context['presets'] = (await self.get_preset_data())
		context['title'] = self.title
		context['icon_style'] = self.icon_style
		context['icon_substyle'] = self.icon_substyle
		return context


	async def get_preset_data(self):
		preset_dict = await self.app.get_presets()
		preset_data = []
		for key, data in preset_dict.items():
			if 'script' in data and self.app.instance.game.game in data['script']:
				script_name = data['script'][self.app.instance.game.game]
				aliases_combined = ''
				if 'aliases' in data and data['aliases']:
					aliases_combined = ', '.join(data['aliases'])
				preset_data.append({
					'name': key,
					'aliases': aliases_combined,
					'script': script_name
				})
		frame = DataFrame(preset_data)
		frame = await self.apply_pagination(frame)
		return frame.to_dict('records')


	async def apply_pagination(self, frame: DataFrame) -> DataFrame:
		return frame[(self.preset_page - 1) * self.num_presets_per_page:self.preset_page * self.num_presets_per_page]

