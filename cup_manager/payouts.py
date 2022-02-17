import logging

from pyplanet.conf import settings
from pyplanet.contrib.command import Command

from .views import MatchHistoryView, PayoutsView

logger = logging.getLogger(__name__)

class PayoutCupManager:
	def __init__(self, app) -> None:
		self.app = app
		self.instance = app.instance
		self.context = app.context


	async def on_start(self) -> None:
		await self.instance.command_manager.register(
			Command(command='debug', aliases=['d'], target=self._button_payout)
		)

		MatchHistoryView.add_button(self._button_payout, 'Payout', self._check_payout_permissions, 25)


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


	async def _button_payout(self, player, *args, **kwargs):
		logger.info("Called _button_payout")
		if not await self._check_payout_permissions(player=player):
			logger.error(f"{player.login} Does not have permission 'transactions:pay'")
			return

		logger.info('called from command')
		payout_view = PayoutsView(self)
		await payout_view.display(player=player)


	async def _check_payout_permissions(self, player, *args, **kwargs) -> bool:
		return await self.instance.permission_manager.has_permission(player, 'transactions:pay')
