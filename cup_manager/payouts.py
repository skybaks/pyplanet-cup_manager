import logging
from math import trunc

from pyplanet.conf import settings
from pyplanet.contrib.command import Command

from .models import CupInfo
from .views import MatchHistoryView, PayoutsView, ResultsView
from .app_types import TeamPlayerScore

logger = logging.getLogger(__name__)

class PayoutCupManager:
	def __init__(self, app) -> None:
		self.app = app
		self.instance = app.instance
		self.context = app.context


	async def on_start(self) -> None:
		if self.instance.game.game not in ['tm','sm'] or 'transactions' not in self.instance.apps.apps:
			return

		ResultsView.add_button('Payout', self._button_payout, self._check_payout_permissions)


	async def get_payouts(self) -> 'dict[str, list[int]]':
		payouts = {}
		try:
			payouts = settings.CUP_MANAGER_PAYOUTS
		except:
			payouts = {
				'hec': [
					1000,
					700,
					500,
					400,
					300,
				],
				'smurfscup': [
					6000,
					4000,
					3000,
					2500,
					1500,
					1000,
					800,
					600,
					400,
					200,
				],
			}
		return payouts


	async def pay_players(self, player, payment_data) -> None:
		if not await self._check_payout_permissions(player=player):
			logger.error(f"{player.login} does not have permission 'transactions:pay'")
			return
		if 'transactions' in self.instance.apps.apps:
			for payment in payment_data:
				logger.debug(f"Attempting to pay {payment.login} {str(payment.amount)}")
				await self.instance.apps.apps['transactions'].pay_to_player(player=player, data=payment)


	async def get_data_payout_score(self, payout_key: str, sorted_results: 'list[TeamPlayerScore]') -> 'list[tuple[TeamPlayerScore, int]]':
		payouts = await self.get_payouts()
		selected_payout = []	# type: list[int]
		if payout_key in payouts:
			selected_payout = payouts[payout_key]
		payout_score = []
		score_ties = TeamPlayerScore.get_ties(sorted_results)
		for player_score in sorted_results:
			if 0 <= player_score.placement-1 < len(selected_payout):
				if player_score.login in score_ties:
					tied_players_count = len(score_ties[player_score.login]) + 1
					tied_payment_pool = 0
					for index in range(0, tied_players_count):
						if player_score.placement - 1 + index < len(selected_payout):
							tied_payment_pool += selected_payout[player_score.placement-1+index]
						else:
							break
					payout_score.append((
						player_score,
						max(int(tied_payment_pool / tied_players_count), 1)
					))
				else:
					payout_score.append((
						player_score,
						selected_payout[player_score.placement-1]
					))
			else:
				break
		return payout_score


	async def _button_payout(self, player, values, view: MatchHistoryView, **kwargs):
		if not await self._check_payout_permissions(player=player):
			logger.error(f"{player.login} does not have permission 'transactions:pay'")
			return

		if view.scores_query:
			scores_data = await self.app.results.get_data_scores(view.scores_query, view.scores_sorting)
			payout_view = PayoutsView(self, scores_data)

			if hasattr(view, 'cup_start_time'):
				cup_info = await self.app.active.get_data_specific_cup_info(view.cup_start_time)	# type: CupInfo
				cup_keyname, cup_settings = await self.app.active.get_specific_cup_settings(cup_info.cup_key)
				if 'payout' in cup_settings:
					payout_view.selected_option = {'name': cup_settings['payout'], 'selected': True}

			await payout_view.display(player=player)


	async def _check_payout_permissions(self, player, *args, **kwargs) -> bool:
		return await self.instance.permission_manager.has_permission(player, 'transactions:pay')
