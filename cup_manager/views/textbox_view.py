from asyncio import iscoroutinefunction, Future
import re
import logging
from enum import Enum

from pyplanet.utils import style
from pyplanet.views.template import TemplateView
from pyplanet.apps.core.maniaplanet.models.player import Player

logger = logging.getLogger(__name__)

class TextboxView(TemplateView):

	template_name = 'cup_manager/textbox.xml'

	title = 'Textbox'
	icon_style = None
	icon_substyle = None

	def __init__(self, app, player):
		super().__init__(self)
		self.app = app
		self.manager = app.context.ui
		self.player = player
		self.id = 'cup_manager__textbox_textboxview'

		self.subscribe('textbox_button_close', self.close)
		self.subscribe('textbox_copy_success', self.copy_success)


	async def get_context_data(self):
		context = await super().get_context_data()

		buttons = await self.get_buttons()

		right = 107
		for button in buttons:
			button['right'] = (right - (button['width'] / 2))
			right -= button['width'] + 1.5

		context['title'] = self.title
		context['icon_style'] = self.icon_style
		context['icon_substyle'] = self.icon_substyle
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


	async def copy_success(self, player, *args, **kwargs):
		await self.app.instance.chat(f'Copied to clipboard', player=player)


	async def get_buttons(self) -> list:
		buttons = []
		return buttons


	async def get_text_data(self) -> str:
		return ''


	async def refresh(self, player, *args, **kwargs):
		await self.display(player=player)


	async def display(self, player=None):
		login = player.login if isinstance(player, Player) else player
		if not player:
			raise Exception('No player/login given to display textbox to')

		player = player if isinstance(player, Player) else await self.manager.player_manager.get_player(login=login, lock=False)
		other_list = player.attributes.get('cup_manager.views.textbox_displayed', None)
		if other_list and isinstance(other_list, list):
			other_manialink = self.manager.instance.ui_manager.get_manialink_by_id(other_list)
			if isinstance(other_manialink, TextboxView):
				await other_manialink.close(player)
			player.attributes.set('cup_manager.views.textbox_displayed', self.id)
		return await super().display(player_logins=[login])


	async def close(self, player, *args, **kwargs):
		if self.player_data and player.login in self.player_data:
			del self.player_data[player.login]
		await self.hide(player_logins=[player.login])
		player.attributes.set('cup_manager.views.textbox_displayed', None)


class TextResultsView(TextboxView):

	class ExportFormat(Enum):
		MARKDOWN = 1
		CSV = 2

	title = 'Export Results'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'NewTrack'
	_export_format = ExportFormat.MARKDOWN


	def __init__(self, app, player, input_data):
		super().__init__(app, player)
		self._instance_data = input_data
		self._response_future = Future()


	async def get_buttons(self) -> list:
		buttons = [
			{
				'title': 'Markdown',
				'width': 25,
				'action': self._action_set_markdown,
				'selected': self._export_format == self.ExportFormat.MARKDOWN,
			},
			{
				'title': 'CSV',
				'width': 25,
				'action': self._action_set_csv,
				'selected': self._export_format == self.ExportFormat.CSV,
			}
		]
		return buttons


	async def get_text_data(self) -> str:
		text = ''
		if self._instance_data:
			if self._export_format == self.ExportFormat.MARKDOWN:
				indexes = [str(item['index']) for item in self._instance_data]
				scores = [str(item['score_str']) for item in self._instance_data]
				nicknames = [style.style_strip(item['nickname'], style.STRIP_ALL) for item in self._instance_data]

				index_justify = min(4, len(max(indexes, key=len)))
				score_justify = min(15, len(max(scores, key=len)))

				text += "```\n"
				for index, nickname, score in zip(indexes, nicknames, scores):
					text += f"{index.rjust(index_justify)}  {score.rjust(score_justify)}  {nickname}\n"
				text += "```"
			elif self._export_format == self.ExportFormat.CSV:
				for item in self._instance_data:
					text += f"\"{item['index']}\",\"{item['score_str']}\",\"{style.style_strip(item['nickname'], style.STRIP_ALL)}\",\"{item['login']}\",\"{item['country']}\"\n"
			else:
				text = f"Export format not implemented: {str(self._export_format)}"
				logger.error(text)
		return text


	async def close(self, player, *args, **kwargs):
		await super().close(player, *args, **kwargs)
		if self._instance_data:
			del self._instance_data

		self._response_future.set_result(None)
		self._response_future.done()


	async def wait_for_response(self):
		return await self._response_future


	async def _action_set_markdown(self, player, *args, **kwargs):
		logger.info("called _action_set_markdown")
		if self._export_format != self.ExportFormat.MARKDOWN:
			self._export_format = self.ExportFormat.MARKDOWN
			await self.refresh(player=player)


	async def _action_set_csv(self, player, *args, **kwargs):
		logger.info("called _action_set_csv")
		if self._export_format != self.ExportFormat.CSV:
			self._export_format = self.ExportFormat.CSV
			await self.refresh(player=player)

