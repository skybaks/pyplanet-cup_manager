from asyncio import iscoroutinefunction
import re
import logging

from pyplanet.views.template import TemplateView

logger = logging.getLogger(__name__)

class TextboxView(TemplateView):

	template_name = 'cup_manager/textbox.xml'

	title = 'Text Match Results'

	def __init__(self, app, player):
		super().__init__(self)
		self.app = app
		self.manager = app.context.ui
		self.player = player
		self.id = 'cup_manager__textbox_textboxview'

		self.subscribe('textbox_button_close', self.close)
		self.subscribe('textbox_button_copy', self._oncopy)


	async def get_context_data(self):
		context = await super().get_context_data()

		buttons = await self.get_buttons()

		right = 107
		for button in buttons:
			button['right'] = (right - (button['width'] / 2))
			right -= button['width'] + 1.5

		context['title'] = self.title
		context['text_body'] = '\n'.join([
			'Markdown example:',
			'```',
			'01  banjee          1000000',
			'02  everyone else   0',
			'```',
			'',
			'Csv example:',
			'1,banjee,1000000',
			'2,everyone else,0',
		])
		context['buttons'] = buttons
		return context


	async def handle_catch_all(self, player, action, values, **kwargs):
		if action.startswith('textbox_buttons_'):
			match = re.search('^textbox_buttons_([0-9]+)$', action)
			if len(match.groups()) != 1:
				return
			try:
				button = int(match.group(1))
				field = (await self.get_buttons())[button]
				action_method = field['action']
			except Exception as e:
				logger.warning(f"Got invalid result in list item click: {str(e)}")
				return
			if iscoroutinefunction(action_method):
				await action_method(player, values, view=self)
			else:
				action_method(player, values, view=self)


	async def close(self, player, *args, **kwargs):
		await self.hide(player_logins=[player.login])


	async def _oncopy(self, player, *args, **kwargs):
		await self.app.instance.chat("Text copied to clipboard", self.player)


	async def get_buttons(self) -> list:
		buttons = [
			{
				'title': 'Markdown',
				'width': 20,
				'action': self._action_set_markdown
			},
			{
				'title': 'CSV',
				'width': 20,
				'action': self._action_set_csv
			}
		]
		return buttons


	async def _action_set_markdown(self, player, *args, **kwargs):
		logger.info("called _action_set_markdown")


	async def _action_set_csv(self, player, *args, **kwargs):
		logger.info("called _action_set_csv")

