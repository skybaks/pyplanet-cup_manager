import logging
from multiprocessing import context
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
		fields.append({
			'name': 'col1',
			'index': 'data1',
			'width': 30,
		})
		fields.append({
			'name': 'col2',
			'index': 'data2',
			'width': 10,
		})
		fields.append({
			'name': 'col3',
			'index': 'data3',
			'width': 20,
		})
		fields.append({
			'name': 'col4',
			'index': 'data4',
			'width': 20,
		})
		return fields


	async def get_option_data(self) -> 'list[dict]':
		data = [
			{
				'data1': 'item 1 1',
				'data2': 'item 1 2',
				'data3': 'itme 1 3',
				'data4': 'item 1 4',
			},
			{
				'data1': 'item 2 1',
				'data2': 'item 2 2',
				'data3': 'itme 2 3',
				'data4': 'item 2 4',
			},
		]
		return data


	async def get_info_header_fields(self) -> 'list[dict]':
		fields = [
			{
				'name': 'Smol 1:',
				'width': 20,
				'index': 'header1',
			},
			{
				'name': 'Header Diff 2:',
				'width': 20,
				'index': 'header2',
			},
		]
		return fields


	async def get_info_header_data(self) -> dict:
		data = {
			'header1': 'hoho haha',
			'header2': 'asdf 1234',
		}
		return data


	async def get_info_data_fields(self) -> 'list[dict]':
		fields = [
			{
			'name': 'col1',
			'index': 'data1',
			'width': 10,
			},
			{
			'name': 'col2',
			'index': 'data2',
			'width': 30,
			},
		]
		return fields


	async def get_info_data(self) -> 'list[dict]':
		data = [
			{
				'data1': 'item 1 1',
				'data2': 'item 1 2',
			},
			{
				'data1': 'item 2 1',
				'data2': 'item 2 2',
			},
			{
				'data1': 'item 3 1',
				'data2': 'item 3 2',
			},
		]
		return data


	async def _render_field(self, row, field) -> str:
		if isinstance(row, dict):
			return str(row[field['index']])
		else:
			return str(getattr(row, field['index']))
