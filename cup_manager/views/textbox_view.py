from asyncio import iscoroutinefunction
import re
import logging
import datetime
from enum import Enum

from pyplanet.utils import style

from ..utils import country_codes, markdown
from ..app_types import TeamPlayerScore
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
		self.cup_name = '$(var.cup_name)'
		self.cup_edition = '$(var.cup_edition)'
		self.payout_key = ''

		self.subscribe('textbox_button_close', self.close)
		self.subscribe('textbox_copy_success', self.copy_success)
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
		context['cup_name'] = self.cup_name
		context['cup_edition'] = self.cup_edition
		context['payout_key'] = self.payout_key
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
		await self.app.instance.chat(f'$ff0Copied to clipboard', player)


	async def entry_submit(self, player, action, values, *args, **kwargs):
		self.cup_name = values['textbox_cupname']
		self.cup_edition = values['textbox_cupedition']
		self.payout_key = values['textbox_payoutkey']
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


	def __init__(self, app, player, input_data: 'list[TeamPlayerScore]', match_data, show_score2=False, show_team_score=False):
		super().__init__(app, player)
		self._instance_data = input_data
		self._instance_match_data = match_data
		self._show_score2 = show_score2
		self._show_team_score = show_team_score
		self.exclude_zero_points = True
		self.exclude_zero_points_as_spec = True
		self.include_match_info = True

		self.subscribe('textbox_checkbox_include_match_info', self.toggle_include_match_info)
		self.subscribe('textbox_checkbox_excludeplayers', self.toggle_excludeplayers)
		self.subscribe('textbox_checkbox_excludeplayers_asspec', self.toggle_excludeplayers_as_spec)


	async def get_context_data(self):
		context = await super().get_context_data()
		context.update({
			'export_format_discord': self._export_format == self.ExportFormat.DISCORD,
			'export_format_markdown': self._export_format == self.ExportFormat.MARKDOWN,
			'export_format_csv': self._export_format == self.ExportFormat.CSV,
			'exclude_zero_points': self.exclude_zero_points,
			'exclude_zero_points_as_spec': self.exclude_zero_points_as_spec,
			'include_match_info': self.include_match_info,
		})
		return context


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
			instance_data = [item for item in self._instance_data if item.team_score > 0 or item.player_score > 0 or item.player_score2 > 0] if self.exclude_zero_points else self._instance_data
			if instance_data:

				payout_scores = await self.app.payout.get_data_payout_score(self.payout_key, instance_data)	#type: list[tuple[TeamPlayerScore, int]]

				if self._export_format in [ self.ExportFormat.MARKDOWN, self.ExportFormat.DISCORD ]:

					placements = [str(item.placement) for item in instance_data]
					team_scores = [str(item.team_score_str) for item in instance_data]
					scores = [str(item.player_score_str) for item in instance_data]
					score2s = [str(item.player_score2_str) for item in instance_data]
					nicknames = [style.style_strip(item.nickname, style.STRIP_ALL) for item in instance_data]
					countries = [str(item.country) for item in instance_data]
					payouts = []
					if len(payout_scores) > 0:
						payouts = [str(payout_item[1]) for payout_item in payout_scores]
					while len(payouts) < len(instance_data):
						payouts.append('')

					index_justify = min(4, len(max(placements, key=len)))
					team_score_justify = min(15, len(max(team_scores, key=len)))
					score_justify = min(15, len(max(scores, key=len)))
					score2_justify = min(15, len(max(score2s, key=len)))
					nickname_payout_justify = min(30, len(max(nicknames[0:min(len(payout_scores), len(nicknames))], key=len))) if len(payout_scores) > 0 else 0

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
							text += f'*{markdown.escape_discord(match_info.mode_script)}* on {markdown.escape_discord(style.style_strip(match_info.map_name))}'
							if mx_id and mx_base_url:
								text += f' <{mx_base_url}/s/tr/{mx_id}>'
							text += '\n'

						placement_emotes = [
							':first_place:',
							':second_place:',
							':third_place:',
							':four:',
						]

						for place, nickname, country in zip(placements, nicknames, countries):
							if int(place)-1 < len(placement_emotes):
								text += f'{placement_emotes[int(place)-1]} {country_codes.get_discord_flag(country)} {markdown.escape_discord(nickname)}\n'
							else:
								break

						text += '\n'
						text += 'Full results:\n'

					text += "```\n"
					for placement, nickname, team_score, score, score2, payout in zip(placements, nicknames, team_scores, scores, score2s, payouts):
						text += str(placement.rjust(index_justify)) + '  '
						if self._show_team_score:
							text += str(team_score.rjust(team_score_justify)) + '  '
						if self._show_score2:
							text += str(score2.rjust(score2_justify)) + '  '
						text += str(score.rjust(score_justify)) + '  '
						text += str(nickname)
						if payout:
							text += str(' ' * max(nickname_payout_justify - len(nickname), 0)) + '  ' + str(payout)
						text += '\n'

					if self.exclude_zero_points and self.exclude_zero_points_as_spec:
						excluded_players = [item for item in self._instance_data if item.team_score <= 0 and item.player_score <= 0 and item.player_score2 <= 0]
						spec_justify = index_justify + score_justify + 4
						if self._show_team_score:
							spec_justify += team_score_justify + 2
						if self._show_score2:
							spec_justify += score2_justify + 2
						for excluded_player in excluded_players:
							text += str('Spec'.ljust(spec_justify))
							text += str(style.style_strip(excluded_player.nickname, style.STRIP_ALL)) + '\n'

					text += "```"
				elif self._export_format == self.ExportFormat.CSV:
					csv_lines = []
					if self.include_match_info:
						sorted_match_info_list = sorted(self._instance_match_data, key=lambda x: x.map_start_time)
						for match_info in sorted_match_info_list:
							csv_match = [
								str(datetime.datetime.fromtimestamp(match_info.map_start_time).strftime("%c")),
								str(match_info.mode_script),
								str(style.style_strip(match_info.map_name, style.STRIP_ALL)),
								str(match_info.map_uid),
								str(match_info.mx_id),
							]
							csv_lines.append(','.join([f'"{x}"' for x in csv_match]))
					for item in instance_data:
						csv_item = []
						csv_item.append(str(item.placement))
						if self._show_team_score:
							csv_item.append(str(item.team_score_str))
						csv_item.append(str(item.player_score_str))
						if self._show_score2:
							csv_item.append(str(item.player_score2_str))
						csv_item.append(style.style_strip(item.nickname, style.STRIP_ALL))
						csv_item.append(str(item.login))
						csv_item.append(str(item.country))
						if len(payout_scores) > 0:
							payout_item = next((pay_item for pay_item in payout_scores if pay_item[0].login == item.login), None)
							if payout_item:
								csv_item.append(str(payout_item[1]))
							else:
								csv_item.append("0")
						csv_lines.append(','.join([f'"{x}"' for x in csv_item]))
					text = '\n'.join(csv_lines)
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


	async def toggle_excludeplayers(self, player, *args, **kwargs):
		self.exclude_zero_points = not self.exclude_zero_points
		await self.refresh(player=player)


	async def toggle_excludeplayers_as_spec(self, player, *args, **kwargs):
		self.exclude_zero_points_as_spec = not self.exclude_zero_points_as_spec
		await self.refresh(player=player)


	async def toggle_include_match_info(self, player, *args, **kwargs):
		self.include_match_info = not self.include_match_info
		await self.refresh(player=player)
