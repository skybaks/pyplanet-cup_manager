from asyncio import iscoroutinefunction
import re
import logging
from enum import Enum

from pyplanet.utils import style

from ..utils import country_codes
from .single_instance_view import SingleInstanceView

logger = logging.getLogger(__name__)

class TextboxView(SingleInstanceView):

	template_name = 'cup_manager/textbox.xml'

	title = 'Textbox'
	icon_style = None
	icon_substyle = None

	def __init__(self, app, player):
		super().__init__(app, 'cup_manager.views.textbox_displayed')
		self.player = player

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
		await self.app.instance.chat(f'Copied to clipboard', player)


	async def get_buttons(self) -> list:
		buttons = []
		return buttons


	async def get_text_data(self) -> str:
		return ''


class TextResultsView(TextboxView):

	class ExportFormat(Enum):
		DISCORD = 1
		MARKDOWN = 2
		CSV = 3

	title = 'Export Results'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'NewTrack'
	_export_format = ExportFormat.DISCORD


	def __init__(self, app, player, input_data, match_data, show_score2=False):
		super().__init__(app, player)
		self._instance_data = input_data
		self._instance_match_data = match_data
		self._show_score2 = show_score2


	async def get_buttons(self) -> list:
		buttons = [
			{
				'title': 'Discord',
				'width': 25,
				'action': self._action_set_discord,
				'selected': self._export_format == self.ExportFormat.DISCORD,
			},
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
			},
		]
		return buttons


	async def get_text_data(self) -> str:
		text = ''
		if self._instance_data:
			if self._export_format in [ self.ExportFormat.MARKDOWN, self.ExportFormat.DISCORD ]:

				indexes = [str(item['index']) for item in self._instance_data]
				scores = [str(item['score_str']) for item in self._instance_data]
				score2s = [str(item['score2_str']) for item in self._instance_data]
				nicknames = [style.style_strip(item['nickname'], style.STRIP_ALL) for item in self._instance_data]
				countries = [str(item['country']) for item in self._instance_data]

				index_justify = min(4, len(max(indexes, key=len)))
				score_justify = min(15, len(max(scores, key=len)))
				score2_justify = min(15, len(max(score2s, key=len)))

				if self._export_format == self.ExportFormat.DISCORD:
					text += f'**$(var.cup_name)** - $(var.cup_edition) - {str(len(self._instance_data))} Players\n'

					sorted_match_info_list = sorted(self._instance_match_data, key=lambda x: x["map_start_time"])
					for match_info in sorted_match_info_list:
						mx_id = match_info["mx_id"]
						mx_base_url = ''
						if 'mx' in self.app.instance.apps.apps:
							try:
								mx_base_url = self.app.instance.apps.apps['mx'].api.base_url()
							except:
								logger.error(f'Error determining (T)MX base url')
						text += f'*{match_info["mode_script"]}* on {style.style_strip(match_info["map_name"])}'
						if mx_id and mx_base_url:
							text += f' <{mx_base_url}/s/tr/{mx_id}>'
						text += '\n'

					if len(self._instance_data) >= 1:
						text += f':first_place: {country_codes.get_discord_flag(countries[0])} {nicknames[0]}\n'
					if len(self._instance_data) >= 2:
						text += f':second_place: {country_codes.get_discord_flag(countries[1])} {nicknames[1]}\n'
					if len(self._instance_data) >= 3:
						text += f':third_place: {country_codes.get_discord_flag(countries[2])} {nicknames[2]}\n'
					if len(self._instance_data) >= 4:
						text += f':four: {country_codes.get_discord_flag(countries[3])} {nicknames[3]}\n'
					text += '\n'
					text += 'Full results:\n'
					text += '\n'

				text += "```\n"
				for index, nickname, score, score2 in zip(indexes, nicknames, scores, score2s):
					text += str(index.rjust(index_justify)) + '  '
					if self._show_score2:
						text += str(score2.rjust(score2_justify)) + '  '
					text += str(score.rjust(score_justify)) + '  '
					text += str(nickname) + '\n'
				text += "```"
			elif self._export_format == self.ExportFormat.CSV:
				for item in self._instance_data:
					text += '"' + str(item['index']) + '",'
					text += '"' + str(item['score_str']) + '",'
					if self._show_score2:
						text += '"' + str(item['score2_str']) + '",'
					text += '"' + style.style_strip(item['nickname'], style.STRIP_ALL) + '",'
					text += '"' + str(item['login']) + '",'
					text += '"' + str(item['country']) + '"\n'
			else:
				text = f"Export format not implemented: {str(self._export_format)}"
				logger.error(text)
		return text


	async def close(self, player, *args, **kwargs):
		await super().close(player, *args, **kwargs)


	async def _action_set_markdown(self, player, *args, **kwargs):
		logger.debug("called _action_set_markdown")
		if self._export_format != self.ExportFormat.MARKDOWN:
			self._export_format = self.ExportFormat.MARKDOWN
			await self.refresh(player=player)


	async def _action_set_csv(self, player, *args, **kwargs):
		logger.debug("called _action_set_csv")
		if self._export_format != self.ExportFormat.CSV:
			self._export_format = self.ExportFormat.CSV
			await self.refresh(player=player)


	async def _action_set_discord(self, player, *args, **kwargs):
		logger.debug("called _action_set_discord")
		if self._export_format != self.ExportFormat.DISCORD:
			self._export_format = self.ExportFormat.DISCORD
			await self.refresh(player=player)

