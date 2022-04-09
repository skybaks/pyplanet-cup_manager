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
		self.exclude_zero_points = True
		self.exclude_zero_points_as_spec = True
		self.display_ties = True
		self.cup_name = '$(var.cup_name)'
		self.cup_edition = '$(var.cup_edition)'

		self.subscribe('textbox_button_close', self.close)
		self.subscribe('textbox_copy_success', self.copy_success)
		self.subscribe('textbox_checkbox_excludeplayers', self.toggle_excludeplayers)
		self.subscribe('textbox_checkbox_excludeplayers_asspec', self.toggle_excludeplayers_as_spec)
		self.subscribe('textbox_checkbox_displayties', self.toggle_displayties)
		self.subscribe('textbox_entry_submit', self.entry_submit)


	async def get_context_data(self):
		context = await super().get_context_data()

		buttons = await self.get_buttons()

		left = 15
		for button in buttons:
			button['left'] = (left + (button['width'] / 2))
			left += button['width'] + 1.5

		context['title'] = self.title
		context['icon_style'] = self.icon_style
		context['icon_substyle'] = self.icon_substyle
		context['text_body'] = await self.get_text_data()
		context['buttons'] = buttons
		context['exclude_zero_points'] = self.exclude_zero_points
		context['exclude_zero_points_as_spec'] = self.exclude_zero_points_as_spec
		context['display_ties'] = self.display_ties
		context['cup_name'] = self.cup_name
		context['cup_edition'] = self.cup_edition
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


	async def toggle_excludeplayers(self, player, *args, **kwargs):
		self.exclude_zero_points = not self.exclude_zero_points
		await self.refresh(player=player)


	async def toggle_excludeplayers_as_spec(self, player, *args, **kwargs):
		self.exclude_zero_points_as_spec = not self.exclude_zero_points_as_spec
		await self.refresh(player=player)


	async def toggle_displayties(self, player, *args, **kwargs):
		self.display_ties = not self.display_ties
		await self.refresh(player=player)


	async def entry_submit(self, player, action, values, *args, **kwargs):
		self.cup_name = values['textbox_cupname']
		self.cup_edition = values['textbox_cupedition']
		await self.refresh(player=player)


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
				'width': 20,
				'action': self._action_set_discord,
				'selected': self._export_format == self.ExportFormat.DISCORD,
			},
			{
				'title': 'Markdown',
				'width': 20,
				'action': self._action_set_markdown,
				'selected': self._export_format == self.ExportFormat.MARKDOWN,
			},
			{
				'title': 'CSV',
				'width': 20,
				'action': self._action_set_csv,
				'selected': self._export_format == self.ExportFormat.CSV,
			},
		]
		return buttons


	async def get_text_data(self) -> str:
		text = ''
		if self._instance_data:
			instance_data = [item for item in self._instance_data if item.score != 0] if self.exclude_zero_points else self._instance_data
			if instance_data:
				if self._export_format in [ self.ExportFormat.MARKDOWN, self.ExportFormat.DISCORD ]:

					indexes = [str(item) for item in range(1, len(instance_data) + 1)]
					scores = [str(item.score_str) for item in instance_data]
					score2s = [str(item.score2_str) for item in instance_data]
					nicknames = [style.style_strip(item.nickname, style.STRIP_ALL) for item in instance_data]
					countries = [str(item.country) for item in instance_data]

					index_justify = min(4, len(max(indexes, key=len)))
					score_justify = min(15, len(max(scores, key=len)))
					score2_justify = min(15, len(max(score2s, key=len)))

					if self._export_format == self.ExportFormat.DISCORD:
						text += f'**{self.cup_name}** - {self.cup_edition} - {str(len(instance_data))} Players\n'

						sorted_match_info_list = sorted(self._instance_match_data, key=lambda x: x.map_start_time)
						for match_info in sorted_match_info_list:
							mx_id = match_info.mx_id
							mx_base_url = ''
							if 'mx' in self.app.instance.apps.apps:
								try:
									mx_base_url = self.app.instance.apps.apps['mx'].api.base_url()
								except:
									logger.error(f'Error determining (T)MX base url')
							text += f'*{match_info.mode_script}* on {style.style_strip(match_info.map_name)}'
							if mx_id and mx_base_url:
								text += f' <{mx_base_url}/s/tr/{mx_id}>'
							text += '\n'

						score_prev = ()
						placement_emotes = [
							':first_place:',
							':second_place:',
							':third_place:',
							':four:',
						]
						placement_emote_index = 0
						prev_placement_emote_index = 0
						placement_index = 0

						for nickname, country, score, score2 in zip(nicknames, countries, scores, score2s):
							if self.display_ties and score_prev == (score, score2):
								placement_emote_index = prev_placement_emote_index
							if placement_emote_index >= len(placement_emotes) or (placement_index > len(placement_emotes) and placement_emote_index != prev_placement_emote_index):
								break
							text += f'{placement_emotes[placement_emote_index]} {country_codes.get_discord_flag(country)} {nickname}\n'
							prev_placement_emote_index = placement_emote_index
							score_prev = (score, score2)
							placement_index += 1
							placement_emote_index = placement_index

						text += '\n'
						text += 'Full results:\n'

					score_prev = ()
					index_prev = ''

					text += "```\n"
					for index, nickname, score, score2 in zip(indexes, nicknames, scores, score2s):
						display_index = index

						if self.display_ties and score_prev == (score, score2):
							display_index = index_prev
						index_prev = display_index
						score_prev = (score, score2)

						text += str(display_index.rjust(index_justify)) + '  '
						if self._show_score2:
							text += str(score2.rjust(score2_justify)) + '  '
						text += str(score.rjust(score_justify)) + '  '
						text += str(nickname) + '\n'

					if self.exclude_zero_points and self.exclude_zero_points_as_spec:
						excluded_players = [item for item in self._instance_data if item.score == 0]
						spec_justify = index_justify + score_justify + 4
						if self._show_score2:
							spec_justify += score2_justify + 2
						for excluded_player in excluded_players:
							text += str('Spec'.ljust(spec_justify))
							text += str(style.style_strip(excluded_player.nickname, style.STRIP_ALL)) + '\n'

					text += "```"
				elif self._export_format == self.ExportFormat.CSV:
					indexes = [str(item) for item in range(1, len(instance_data) + 1)]
					for item, index in zip(instance_data, indexes):
						text += '"' + str(index) + '",'
						text += '"' + str(item.score_str) + '",'
						if self._show_score2:
							text += '"' + str(item.score2_str) + '",'
						text += '"' + style.style_strip(item.nickname, style.STRIP_ALL) + '",'
						text += '"' + str(item.login) + '",'
						text += '"' + str(item.country) + '"\n'
				else:
					text = f"Export format not implemented: {str(self._export_format)}"
					logger.error(text)
		return text


	async def _action_set_markdown(self, player, *args, **kwargs):
		if self._export_format != self.ExportFormat.MARKDOWN:
			self._export_format = self.ExportFormat.MARKDOWN
			await self.refresh(player=player)


	async def _action_set_csv(self, player, *args, **kwargs):
		if self._export_format != self.ExportFormat.CSV:
			self._export_format = self.ExportFormat.CSV
			await self.refresh(player=player)


	async def _action_set_discord(self, player, *args, **kwargs):
		if self._export_format != self.ExportFormat.DISCORD:
			self._export_format = self.ExportFormat.DISCORD
			await self.refresh(player=player)

