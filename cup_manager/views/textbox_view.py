from asyncio import iscoroutinefunction
import re
import logging
from enum import Enum

from pyplanet.utils import style
from pyplanet.views.template import TemplateView

logger = logging.getLogger(__name__)

class TextboxView(TemplateView):

	template_name = 'cup_manager/textbox.xml'

	title = 'Textbox'

	def __init__(self, app, player):
		super().__init__(self)
		self.app = app
		self.manager = app.context.ui
		self.player = player
		self.id = 'cup_manager__textbox_textboxview'

		self.subscribe('textbox_button_close', self.close)


	async def get_context_data(self):
		context = await super().get_context_data()

		buttons = await self.get_buttons()

		right = 107
		for button in buttons:
			button['right'] = (right - (button['width'] / 2))
			right -= button['width'] + 1.5

		context['title'] = self.title
		context['text_body'] = await self.get_text_data()
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


	async def get_buttons(self) -> list:
		buttons = []
		return buttons


	async def get_text_data(self) -> str:
		return ''


class TextResultsView(TextboxView):

	class ExportFormat(Enum):
		MARKDOWN = 1
		CSV = 2

	title = 'Export Results'
	_export_format = ExportFormat.MARKDOWN


	def __init__(self, app, player):
		super().__init__(app, player)
		self._instance_data = []


	async def set_data(self, player, input_data: list) -> None:
		self._instance_data = input_data


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


	async def get_text_data(self) -> str:
		text = ''
		if self._instance_data:
			if self._export_format == self.ExportFormat.MARKDOWN:
				indexes = [str(item['index']) for item in self._instance_data]
				scores = [str(item['score']) for item in self._instance_data]
				nicknames = [style.style_strip(item['nickname'], style.STRIP_ALL) for item in self._instance_data]

				index_justify = min(4, len(max(indexes, key=len)))
				score_justify = min(5, len(max(scores, key=len)))

				text += "```\n"
				for index, nickname, score in zip(indexes, nicknames, scores):
					text += f"{index.rjust(index_justify)}  {score.rjust(score_justify)}  {nickname}\n"
				text += "```"
			elif self._export_format == self.ExportFormat.CSV:
				for item in self._instance_data:
					text += f"{item['index']},{item['score']},{style.style_strip(item['nickname'], style.STRIP_ALL)},{item['login']}\n"
			else:
				text = f"Export format not implemented: {str(self._export_format)}"
				logger.error(text)
		return text


	async def _action_set_markdown(self, player, *args, **kwargs):
		logger.info("called _action_set_markdown")
		if self._export_format != self.ExportFormat.MARKDOWN:
			self._export_format = self.ExportFormat.MARKDOWN
			await self.display(player=[self.player.login])


	async def _action_set_csv(self, player, *args, **kwargs):
		logger.info("called _action_set_csv")
		if self._export_format != self.ExportFormat.CSV:
			self._export_format = self.ExportFormat.CSV
			await self.display(player=[self.player.login])

