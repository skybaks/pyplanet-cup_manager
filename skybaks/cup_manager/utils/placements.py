import logging

logger = logging.getLogger(__name__)


def pretty_placement(placement: any) -> str:
	postfix = ''
	try:
		ones_digit = int(placement) % 10
		if ones_digit == 1 and int(placement) != 11:
			postfix = 'st'
		elif ones_digit == 2 and int(placement) != 12:
			postfix = 'nd'
		elif ones_digit == 3 and int(placement) != 13:
			postfix = 'rd'
		else:
			postfix = 'th'
	except:
		logger.error(f'Unable to handle input placement value \"{str(placement)}\"')
	return str(placement) + postfix


def pretty_list(items: 'list[any]', item_format: bool=True, item_prefix: str='$fff') -> str:
	formatted_items = [f'$<{item_prefix}{str(item)}$>' for item in items] if item_format else items
	result = ''
	if formatted_items:
		if len(formatted_items) == 1:
			result = formatted_items[0]
		elif len(formatted_items) == 2:
			result = formatted_items[0] + " and " + formatted_items[1]
		elif len(formatted_items) > 2:
			result = ', '.join(formatted_items[0:-1]) + ', and ' + formatted_items[-1]
	return result
