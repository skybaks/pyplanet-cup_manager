from difflib import Match
import logging

from pyplanet.conf import settings
from pyplanet.contrib.command import Command

from .views import MatchHistoryView, PayoutsView, ResultsView
from .app_types import ScoreSortingPresets

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


	async def get_payouts(self) -> dict:
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


	async def _button_payout(self, player, values, view: MatchHistoryView, **kwargs):
		if not await self._check_payout_permissions(player=player):
			logger.error(f"{player.login} does not have permission 'transactions:pay'")
			return

		if view.scores_query:
			scores_data = await self.app.results.get_data_scores(view.scores_query, view.scores_sorting)
			payout_view = PayoutsView(self, scores_data)
			await payout_view.display(player=player)


	async def _check_payout_permissions(self, player, *args, **kwargs) -> bool:
		return await self.instance.permission_manager.has_permission(player, 'transactions:pay')
