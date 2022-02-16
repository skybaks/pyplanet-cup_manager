import logging
import math
import re

from .single_instance_view import SingleInstanceView

logger = logging.getLogger(__name__)

class OptionsView(SingleInstanceView):

	template_name = 'cup_manager/options.xml'

	title = 'Options'
	icon_style = 'Icons128x128_1'
	icon_substyle = 'NewTrack'

	def __init__(self, app, tag) -> None:
		super().__init__(app, tag)
		self.option_page = 1
		self.option_count = 0
		self.num_option_per_page = 6
		self.info_data_page = 1
		self.info_data_count = 0
		self.num_info_data_per_page = 11

		self.subscribe('options_button_close', self.close)
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
					# TODO: Use row to execute a function
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

		option_left = -53
		for option_field in option_fields:
			option_field['left'] = option_left
			option_left += option_field['width']
		
		info_data_left = -53
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

	def __init__(self, app, tag) -> None:
		super().__init__(app, tag)


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
				'width': 30,
				'index': 'planets',
			},
			{
				'name': 'Login',
				'width': 30,
				'index': 'login',
			},
			{
				'name': 'Nickname',
				'width': 30,
				'index': 'nickname',
			},
		]
		return fields


	async def get_info_header_fields(self) -> 'list[dict]':
		fields = [
			{
				'name': 'Selected Schema:',
				'width': 30,
				'index': 'name'
			}
		]
		return fields


	async def get_option_data(self) -> 'list[dict]':
		return await super().get_option_data()


	async def get_info_header_data(self) -> dict:
		data = {
			'name': 'TODO'
		}
		return data


	async def get_info_data(self) -> 'list[dict]':
		return await super().get_info_data()
