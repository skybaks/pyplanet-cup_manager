import logging

logger = logging.getLogger(__name__)


def escape_discord(input: str) -> str:
	return input.replace('_', '\\_').replace('*', '\\*')


def create_table(column_data: 'list[list[str]]', column_header: 'list[dict]', column_spacing: int=2, include_header: bool=False) -> str:
	column_titles = []	# type: list[str]
	column_title_justs = []	# type: list[str]
	column_data_justs = []	# type: list[str]
	for header in column_header:
		column_titles.append(header['name'] if 'name' in header else None)
		column_title_justs.append(header['title_just'] if 'title_just' in header else None)
		column_data_justs.append(header['data_just'] if 'data_just' in header else None)

	longest_data_length = 0
	column_lengths = []
	for data, title in zip(column_data, column_titles):
		longest_data_length = max(longest_data_length, len(data))
		data_max_length = len(max(data, key=len))
		title_length = len(title) if include_header else 0
		column_lengths.append(max(data_max_length, title_length))

	text = []	# type: list[str]
	if include_header:
		header_row = []	# type: list[str]
		for length, title, just in zip(column_lengths, column_titles, column_title_justs):
			if just == 'right':
				header_row.append(title.rjust(length))
			else:
				header_row.append(title.ljust(length))
		text.append(str(' ' * column_spacing).join(header_row))
		text.append(str('=' * (sum(column_lengths) + ((len(column_data) - 1) * column_spacing))))

	for data_index in range(longest_data_length):
		data_row = []	# type: list[str]
		for length, data, just in zip(column_lengths, column_data, column_data_justs):
			if data_index < len(data):
				if just == 'left':
					data_row.append(data[data_index].ljust(length))
				else:
					data_row.append(data[data_index].rjust(length))
			else:
				data_row.append(' ' * length)
		text.append(str(' ' * column_spacing).join(data_row))

	text = [t.rstrip() for t in text]

	text.insert(0, '```')
	text.append('```')
	return '\n'.join(text)
