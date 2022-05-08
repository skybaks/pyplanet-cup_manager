import logging

logger = logging.getLogger(__name__)


def escape_discord(input: str) -> str:
	return input.replace('_', '\\_').replace('*', '\\*')
