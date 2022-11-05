from asyncio import iscoroutinefunction
import re
import logging
import datetime
from enum import Enum

from pyplanet.utils import style

from ..utils import country_codes, markdown
from ..app_types import TeamPlayerScore, PaymentScore
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

		output_options = await self.get_output_options()

		context['title'] = self.title
		context['icon_style'] = self.icon_style
		context['icon_substyle'] = self.icon_substyle
		context['text_body'] = await self.get_text_data()
		context['buttons'] = buttons
		context['output_options'] = output_options
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


	async def get_output_options(self) -> list:
		options = []
		return options


	async def get_text_data(self) -> str:
		return ''


class ExportFormat(Enum):
	DISCORD = 1
	MARKDOWN = 2
	CSV = 3


class CsvExportInformation(Enum):
	BOTH_MAP_AND_MATCH = 0
	MATCH_ONLY = 1
	MAP_ONLY = 2


class TextResultsView(TextboxView):


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
		self.csv_export_info = CsvExportInformation.BOTH_MAP_AND_MATCH
		self.include_table_header = False

		self.subscribe('textbox_checkbox_excludeplayers', self.toggle_excludeplayers)
		self.subscribe('textbox_checkbox_excludeplayers_asspec', self.toggle_excludeplayers_as_spec)
		self.subscribe('textbox_checkbox_include_tableheader', self.toggle_include_tableheader)
		self.subscribe('textbox_checkbox_include_bothmatchmap', self.toggle_include_bothmatchmap)
		self.subscribe('textbox_checkbox_include_onlymatch', self.toggle_include_onlymatch)
		self.subscribe('textbox_checkbox_include_onlymap', self.toggle_include_onlymap)


	async def get_buttons(self) -> list:
		buttons = [
			{
				'title': 'Discord',
				'width': 20,
				'action': self._action_set_discord,
				'selected': self._export_format == ExportFormat.DISCORD,
			},
			{
				'title': 'Markdown',
				'width': 20,
				'action': self._action_set_markdown,
				'selected': self._export_format == ExportFormat.MARKDOWN,
			},
			{
				'title': 'CSV',
				'width': 20,
				'action': self._action_set_csv,
				'selected': self._export_format == ExportFormat.CSV,
			},
		]
		return buttons


	async def get_output_options(self) -> list:
		options = await super().get_output_options()
		options.append({
			'title': 'Name',
			'id': 'cupname',
			'type': 'textbox',
			'enabled': True,
			'value': self.cup_name,
		})
		options.append({
			'title': 'Edition',
			'id': 'cupedition',
			'type': 'textbox',
			'enabled': True,
			'value': self.cup_edition,
		})
		options.append({
			'title': 'Payout Key',
			'id': 'payoutkey',
			'type': 'textbox',
			'enabled': True,
			'value': self.payout_key,
		})
		options.append({
			'title': 'Exclude players with zero points',
			'id': 'excludeplayers',
			'type': 'checkbox',
			'enabled': True,
			'value': self.exclude_zero_points,
		})

		if self._export_format in [ ExportFormat.DISCORD, ExportFormat.MARKDOWN ]:
			options.append({
				'title': 'Show excluded players as "Spec"',
				'id': 'excludeplayers_asspec',
				'type': 'checkbox',
				'enabled': self.exclude_zero_points,
				'value': self.exclude_zero_points_as_spec,
			})
			options.append({
				'title': 'Score table header',
				'id': 'include_tableheader',
				'type': 'checkbox',
				'enabled': True,
				'value': self.include_table_header,
			})

		if self._export_format == ExportFormat.CSV:
			options.append({
				'title': 'Both match and map information',
				'id': 'include_bothmatchmap',
				'type': 'checkbox',
				'enabled': True,
				'value': self.csv_export_info == CsvExportInformation.BOTH_MAP_AND_MATCH,
			})
			options.append({
				'title': 'Only match information',
				'id': 'include_onlymatch',
				'type': 'checkbox',
				'enabled': True,
				'value': self.csv_export_info == CsvExportInformation.MATCH_ONLY,
			})
			options.append({
				'title': 'Only map information',
				'id': 'include_onlymap',
				'type': 'checkbox',
				'enabled': True,
				'value': self.csv_export_info == CsvExportInformation.MAP_ONLY,
			})
		return options


	async def get_text_data(self) -> str:
		text = ''
		if self._instance_data:
			instance_data = [item for item in self._instance_data if item.team_score > 0 or item.player_score > 0 or item.player_score2 > 0] if self.exclude_zero_points else self._instance_data
			if instance_data:

				payout_scores = await self.app.payout.get_data_payout_score(self.payout_key, instance_data)	#type: list[PaymentScore]
				payouts = []
				if len(payout_scores) > 0:
					payouts = [str(payout_item.payment) for payout_item in payout_scores]
				show_payouts = len(payouts) > 0

				if self._export_format in [ ExportFormat.MARKDOWN, ExportFormat.DISCORD ]:

					placements = []	# type: list[str]
					team_scores = []	# type: list[str]
					scores = []	# type: list[str]
					score2s = []	# type: list[str]
					nicknames = []	# type: list[str]
					countries = []	# type: list[str]
					for item in instance_data:
						placements.append(str(item.placement))
						team_scores.append(str(item.team_score_str))
						scores.append(str(item.player_score_str))
						score2s.append(str(item.player_score2_str))
						nicknames.append(style.style_strip(item.nickname, style.STRIP_ALL))
						countries.append(str(item.country))

					if self.exclude_zero_points and self.exclude_zero_points_as_spec:
						excluded_players = [item for item in self._instance_data if item.team_score <= 0 and item.player_score <= 0 and item.player_score2 <= 0]
						for excluded_player in excluded_players:
							placements.append('Spec')
							nicknames.append(style.style_strip(excluded_player.nickname, style.STRIP_ALL))

					table_data = []	# type: list[list[str]]
					table_header = []	# type: list[dict[str,str]]

					table_data.append(placements)
					table_header.append({
						'name': 'Place',
					})
					if self._show_team_score:
						table_data.append(team_scores)
						table_header.append({
							'name': 'Team Score',
						})
					if self._show_score2:
						table_data.append(score2s)
						table_header.append({
							'name': 'Score 2',
						})
					table_data.append(scores)
					table_header.append({
						'name': 'Score',
					})
					table_data.append(nicknames)
					table_header.append({
						'name': 'Player',
						'data_just': 'left',
					})
					if show_payouts:
						table_data.append(payouts)
						table_header.append({
							'name': 'Payout'
						})

					if self._export_format == ExportFormat.DISCORD:
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

					text += markdown.create_table(table_data, table_header, include_header=self.include_table_header)

				elif self._export_format == ExportFormat.CSV:
					csv_lines = []

					if self.csv_export_info in [ CsvExportInformation.BOTH_MAP_AND_MATCH, CsvExportInformation.MAP_ONLY ]:
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

					if self.csv_export_info in [ CsvExportInformation.BOTH_MAP_AND_MATCH, CsvExportInformation.MATCH_ONLY ]:
						filled_payouts = list(payouts)
						if len(filled_payouts) < len(instance_data):
							filled_payouts += [ "0" ] * (len(instance_data) - len(filled_payouts))
						for item, payout in zip(instance_data, filled_payouts):
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
							if show_payouts:
								csv_item.append(payout)
							csv_lines.append(','.join([f'"{x}"' for x in csv_item]))
					text = '\n'.join(csv_lines)
				else:
					text = f"Export format not implemented: {str(self._export_format)}"
					logger.error(text)
		return text


	async def _action_set_markdown(self, player, *args, **kwargs):
		if self._export_format != ExportFormat.MARKDOWN:
			self._export_format = ExportFormat.MARKDOWN
			await self.refresh(player=player)


	async def _action_set_csv(self, player, *args, **kwargs):
		if self._export_format != ExportFormat.CSV:
			self._export_format = ExportFormat.CSV
			await self.refresh(player=player)


	async def _action_set_discord(self, player, *args, **kwargs):
		if self._export_format != ExportFormat.DISCORD:
			self._export_format = ExportFormat.DISCORD
			await self.refresh(player=player)


	async def toggle_excludeplayers(self, player, *args, **kwargs):
		self.exclude_zero_points = not self.exclude_zero_points
		await self.refresh(player=player)


	async def toggle_excludeplayers_as_spec(self, player, *args, **kwargs):
		self.exclude_zero_points_as_spec = not self.exclude_zero_points_as_spec
		await self.refresh(player=player)


	async def toggle_include_tableheader(self, player, *args, **kwargs):
		self.include_table_header = not self.include_table_header
		await self.refresh(player=player)


	async def toggle_include_bothmatchmap(self, player, *args, **kwargs):
		if self.csv_export_info != CsvExportInformation.BOTH_MAP_AND_MATCH:
			self.csv_export_info = CsvExportInformation.BOTH_MAP_AND_MATCH
			await self.refresh(player=player)


	async def toggle_include_onlymatch(self, player, *args, **kwargs):
		if self.csv_export_info != CsvExportInformation.MATCH_ONLY:
			self.csv_export_info = CsvExportInformation.MATCH_ONLY
			await self.refresh(player=player)


	async def toggle_include_onlymap(self, player, *args, **kwargs):
		if self.csv_export_info != CsvExportInformation.MAP_ONLY:
			self.csv_export_info = CsvExportInformation.MAP_ONLY
			await self.refresh(player=player)
