import logging
import math
import re
from argparse import Namespace
from asyncio import iscoroutinefunction

from pyplanet.views.generics import ask_confirmation

from .single_instance_view import SingleInstanceView
from ..app_types import PaymentScore, TeamPlayerScore
from ..score_mode import ScoreModeBase, SCORE_MODE

logger = logging.getLogger(__name__)

class OptionsView(SingleInstanceView):

	template_name = 'cup_manager/options.xml'

	title = 'Options'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'NewTrack'
	apply_option_button_name = 'Apply'

	def __init__(self, app, tag) -> None:
		super().__init__(app, tag)
		self.option_page = 1
		self.option_count = 0
		self.num_option_per_page = 6
		self.info_data_page = 1
		self.info_data_count = 0
		self.num_info_data_per_page = 11
		self.displayed_option_data = []
		self.selected_option = None

		self.subscribe('options_button_close', self.close)
		self.subscribe('apply_selected_option', self.button_pressed)
		self.subscribe('optionlist_button_first', self._optionlist_first_page)
		self.subscribe('optionlist_button_prev', self._optionlist_prev_page)
		self.subscribe('optionlist_button_next', self._optionlist_next_page)
		self.subscribe('optionlist_button_last', self._optionlist_last_page)
		self.subscribe('info_datalist_button_first', self._info_datalist_first_page)
		self.subscribe('info_datalist_button_prev', self._info_datalist_prev_page)
		self.subscribe('info_datalist_button_next', self._info_datalist_next_page)
		self.subscribe('info_datalist_button_last', self._info_datalist_last_page)


	async def handle_catch_all(self, player, action, values, **kwargs):
		if action.startswith('option_list_body_'):
			match = re.search("^option_list_body_([0-9]+)", action)
			if len(match.groups()) == 1:
				try:
					row = int(match.group(1))
					if len(self.displayed_option_data) > row:
						self.selected_option = self.displayed_option_data[row]
						await self.refresh(player=player)
				except Exception as e:
					logger.error(f"Got unexpected results from option list item action {action}: {e}")


	async def get_context_data(self):
		context = await super().get_context_data()
		context.update({
			'title': self.title,
			'icon_style': self.icon_style,
			'icon_substyle': self.icon_substyle,
		})

		option_fields = await self.get_option_fields()
		options = await self.get_option_data()
		info_header_fields = await self.get_info_header_fields()
		info_header_data = await self.get_info_header_data()
		info_data_fields = await self.get_info_data_fields()
		info_data = await self.get_info_data()

		option_left = -52
		for option_field in option_fields:
			option_field['left'] = option_left
			option_left += option_field['width']
		
		info_data_left = -52
		for info_data_field in info_data_fields:
			info_data_field['left'] = info_data_left
			info_data_left += info_data_field['width']

		context.update({
			'field_renderer': self._render_field,
			'option_fields': option_fields,
			'options': options,
			'info_header_fields': info_header_fields,
			'info_header_data': info_header_data,
			'info_data_fields': info_data_fields,
			'info_data': info_data,
			'option_page': self.option_page,
			'num_option_pages': self.num_option_pages,
			'info_data_page': self.info_data_page,
			'num_info_data_pages': self.num_info_data_pages,
			'option_is_selected': self.selected_option != None,
			'apply_option_button_name': self.apply_option_button_name,
		})
		return context


	async def get_option_fields(self) -> 'list[dict]':
		fields = []
		return fields


	async def get_option_data(self) -> 'list[dict]':
		data = []
		return data


	async def get_info_header_fields(self) -> 'list[dict]':
		fields = []
		return fields


	async def get_info_header_data(self) -> dict:
		data = {}
		return data


	async def get_info_data_fields(self) -> 'list[dict]':
		fields = []
		return fields


	async def get_info_data(self) -> 'list[dict]':
		data = []
		return data


	@staticmethod
	async def apply_pagination(frame, page: int, num_per_page: int) -> any:
		return frame[(page - 1) * num_per_page:page * num_per_page]


	async def button_pressed(self, player, *args, **kwargs):
		pass


	async def _render_field(self, row, field) -> str:
		try:
			if isinstance(row, dict):
				return str(row[field['index']])
			else:
				return str(getattr(row, field['index']))
		except:
			return ''


	@property
	def num_option_pages(self):
		return int(math.ceil(self.option_count / self.num_option_per_page))


	@property
	def num_info_data_pages(self):
		return int(math.ceil(self.info_data_count / self.num_info_data_per_page))


	async def _optionlist_first_page(self, player, *args, **kwargs):
		if self.option_page != 1:
			self.option_page = 1
			await self.refresh(player=player)


	async def _optionlist_prev_page(self, player, *args, **kwargs):
		if self.option_page - 1 > 0:
			self.option_page -= 1
			await self.refresh(player=player)


	async def _optionlist_next_page(self, player, *args, **kwargs):
		if self.option_page + 1 <= self.num_option_pages:
			self.option_page += 1
			await self.refresh(player=player)


	async def _optionlist_last_page(self, player, *args, **kwargs):
		if self.option_page != self.num_option_pages:
			self.option_page = self.num_option_pages
			await self.refresh(player=player)


	async def _info_datalist_first_page(self, player, *args, **kwargs):
		if self.info_data_page != 1:
			self.info_data_page = 1
			await self.refresh(player=player)


	async def _info_datalist_prev_page(self, player, *args, **kwargs):
		if self.info_data_page - 1 > 0:
			self.info_data_page -= 1
			await self.refresh(player=player)


	async def _info_datalist_next_page(self, player, *args, **kwargs):
		if self.info_data_page + 1 <= self.num_info_data_pages:
			self.info_data_page += 1
			await self.refresh(player=player)


	async def _info_datalist_last_page(self, player, *args, **kwargs):
		if self.info_data_page != self.num_info_data_pages:
			self.info_data_page = self.num_info_data_pages
			await self.refresh(player=player)


class PayoutsView(OptionsView):

	title = 'Payouts'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'Coppers'

	def __init__(self, app, score_data: 'list[TeamPlayerScore]', score_sorting: ScoreModeBase) -> None:
		super().__init__(app, 'cup_manager.views.payouts_view_displayed')
		self.score_data = score_data
		self.score_sorting = score_sorting
		self.apply_option_button_name = 'Pay'


	async def get_option_fields(self) -> 'list[dict]':
		fields = [
			{
				'name': 'Name',
				'width': 90,
				'index': 'name',
			},
		]
		return fields


	async def get_info_data_fields(self) -> 'list[dict]':
		fields = [
			{
				'name': '#',
				'width': 10,
				'index': 'place',
			},
			{
				'name': 'Planets',
				'width': 17,
				'index': 'planets',
			},
			{
				'name': 'Nickname',
				'width': 40,
				'index': 'nickname',
			},
			{
				'name': 'Login',
				'width': 37,
				'index': 'login',
			},
		]
		return fields


	async def get_info_header_fields(self) -> 'list[dict]':
		fields = [
			{
				'name': 'Selected Payout:',
				'width': 30,
				'index': 'name'
			}
		]
		return fields


	async def get_option_data(self) -> 'list[dict]':
		payouts = await self.app.get_payouts()
		options = []
		if not self.selected_option and len(payouts) > 0:
			self.selected_option = { 'name': list(payouts.keys())[0] }
		for key, data in payouts.items():
			options.append({
				'name': key,
				'selected': self.selected_option and self.selected_option['name'] == key,
			})
		frame = options
		self.option_count = len(frame)
		frame = await self.apply_pagination(frame, self.option_page, self.num_option_per_page)
		self.displayed_option_data = frame
		return self.displayed_option_data


	async def get_info_header_data(self) -> dict:
		data = {
			'name': self.selected_option['name'] if self.selected_option and 'name' in self.selected_option else ''
		}
		return data


	async def get_info_data(self) -> 'list[dict]':
		info_data = []
		if self.selected_option and 'name' in self.selected_option:
			payout_score = await self.app.get_data_payout_score(self.selected_option['name'], self.score_data, self.score_sorting)	# type: list[PaymentScore]
			for payout_item in payout_score:
				info_data.append({
					'place': payout_item.score.placement,
					'planets': payout_item.payment,
					'login': payout_item.score.login,
					'nickname': payout_item.score.nickname,
				})
		frame = info_data
		self.info_data_count = len(frame)
		frame = await self.apply_pagination(frame, self.info_data_page, self.num_info_data_per_page)
		return frame


	async def button_pressed(self, player, *args, **kwargs):
		if self.selected_option and 'name' in self.selected_option:
			payout_score = await self.app.get_data_payout_score(self.selected_option['name'], self.score_data, self.score_sorting)	# type: list[PaymentScore]
			total_planets = sum([x.payment for x in payout_score])
		cancel = bool(await ask_confirmation(
			player=player,
			message=f'The selected payout "{self.selected_option["name"]}" will pay {str(len(payout_score))} players a total of {str(total_planets)} planets.\nAre you sure?',
			buttons=[{'name': 'Confirm'}, {'name': 'Cancel'}]
		))
		if not cancel:
			await self.close(player=player)
			await self.app.pay_players(player, payout_score)


class PresetsView(OptionsView):

	title = 'Preset Setups'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'NewTrack'

	def __init__(self, app) -> None:
		super().__init__(app, 'cup_manager.views.presets_view_displayed')
		self.apply_option_button_name = 'Apply'


	async def get_option_fields(self) -> 'list[dict]':
		fields = [
			{
				'name': 'Name',
				'width': 30,
				'index': 'name',
			},
			{
				'name': 'Aliases',
				'width': 30,
				'index': 'aliases',
			},
			{
				'name': 'Script',
				'width': 45,
				'index': 'script',
			},
		]
		return fields


	async def get_info_data_fields(self) -> 'list[dict]':
		fields = [
			{
				'name': 'Setting',
				'width': 30,
				'index': 'name',
			},
			{
				'name': 'Value',
				'width': 75,
				'index': 'value',
			},
		]
		return fields


	async def get_info_header_fields(self) -> 'list[dict]':
		fields = [
			{
				'name': 'Preset:',
				'width': 17,
				'index': 'name',
			},
			{
				'name': 'Script:',
				'width': 17,
				'index': 'script',
			},
		]
		return fields


	async def get_option_data(self) -> 'list[dict]':
		presets = await self.app.get_presets()
		options = []
		for key, data in presets.items():
			if 'script' in data and self.app.instance.game.game in data['script']:
				aliases_combined = ''
				if 'aliases' in data and data['aliases']:
					aliases_combined = ', '.join(data['aliases'])
				new_option = {
					'name': key,
					'selected': self.selected_option and self.selected_option['name'] == key,
					'aliases': aliases_combined,
					'script': data['script'][self.app.instance.game.game],
				}

				if not self.selected_option:
					new_option['selected'] = True
					self.selected_option = new_option

				options.append(new_option)

		frame = options
		self.option_count = len(frame)
		frame = await self.apply_pagination(frame, self.option_page, self.num_option_per_page)
		self.displayed_option_data = frame
		return self.displayed_option_data


	async def get_info_header_data(self) -> dict:
		data = {}
		if self.selected_option:
			data.update(self.selected_option)
		return data


	async def get_info_data(self) -> 'list[dict]':
		info_data = []
		if self.selected_option and 'name' in self.selected_option:
			presets = await self.app.get_presets()
			selected_preset = presets[self.selected_option['name']]
			if 'settings' in selected_preset and selected_preset['settings']:
				for key, data in selected_preset['settings'].items():
					info_data.append({'name': key, 'value': data})
		frame = info_data
		self.info_data_count = len(frame)
		frame = await self.apply_pagination(frame, self.info_data_page, self.num_info_data_per_page)
		return frame


	async def button_pressed(self, player, *args, **kwargs):
		if 'name' in self.selected_option and self.selected_option['name']:
			await self.app.command_setup(player=player, data=Namespace(**{'preset': self.selected_option['name']}))
			await self.close(player=player)


class ScoreModeView(OptionsView):

	title = 'Score Modes'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'NewTrack'

	def __init__(self, app, select_button_method) -> None:
		super().__init__(app, 'cup_manager.views.scoremode_view_displayed')
		self.apply_option_button_name = 'Select'
		self.select_button_method = select_button_method


	async def get_option_fields(self) -> 'list[dict]':
		fields = [
			{
				'name': 'Sorting Mode Name',
				'width': 90,
				'index': 'name',
			},
		]
		return fields


	async def get_info_data_fields(self) -> 'list[dict]':
		fields = [
			{
				'name': 'Details',
				'width': 105,
				'index': 'doc',
			}
		]
		return fields


	async def get_info_header_fields(self) -> 'list[dict]':
		fields = [
			{
				'name': 'Selected:',
				'width': 20,
				'index': 'name'
			},
			{
				'name': '',
				'width': 0,
				'index': 'brief',
			},
		]
		return fields


	async def get_option_data(self) -> 'list[dict]':
		options = []
		for score_mode_id, score_mode_class in SCORE_MODE.items():
			class_instance = score_mode_class()
			new_option = {
				'id': score_mode_id,
				'name': class_instance.display_name,
				# for header
				'brief': class_instance.brief,
				# for view
				'selected': self.selected_option and self.selected_option['id'] == score_mode_id,
			}

			if not self.selected_option:
				new_option['selected'] = True
				self.selected_option = new_option

			options.append(new_option)

		self.option_count = len(options)
		options = await self.apply_pagination(options, self.option_page, self.num_option_per_page)
		self.displayed_option_data = options
		return self.displayed_option_data


	async def get_info_data(self) -> 'list[dict]':
		info_data = []
		if self.selected_option and 'id' in self.selected_option:
			doc_str = SCORE_MODE[self.selected_option['id']].__doc__
			doc_str = '\n'.join([line.strip() for line in doc_str.splitlines()]).strip()
			info_data += [
				{
					'doc': doc_str,
				}
			]
		return info_data


	async def get_info_header_data(self) -> dict:
		data = {}
		if self.selected_option:
			data.update(self.selected_option)
		return data


	async def button_pressed(self, player, *args, **kwargs):
		if self.selected_option and 'id' in self.selected_option:
			if iscoroutinefunction(self.select_button_method):
				await self.select_button_method(self.selected_option['id'], player)
			else:
				self.select_button_method(self.selected_option['id'], player)
			await self.close(player=player)
