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
