from argparse import Namespace
import logging

from pyplanet.conf import settings
from pyplanet.contrib.command import Command

logger = logging.getLogger(__name__)

class SetupCupManager:
	def __init__(self, app) -> None:
		self.app = app
		self.instance = app.instance


	async def on_start(self) -> None:
		await self.instance.permission_manager.register('setup_cup', 'Change match settings from the cup_manager', app=self.app, min_level=2, namespace=self.app.namespace)

		await self.instance.command_manager.register(
			Command(command='setup', aliases=['s'], namespace=self.app.namespace, target=self._command_setup,
				admin=True, perms='cup:setup_cup', description='Setup match settings based on some common presets.').add_param('preset'),
		)


	async def get_presets(self) -> dict:
		presets = {}
		try:
			presets = settings.CUP_MANAGER_PRESETS
		except:
			presets = {
				'rounds180': {
					'aliases': [ 'smurfscup', 'sc' ],
					'script': {
						'tm': 'Rounds.Script.txt',
						'tmnext': 'Trackmania/TM_Rounds_Online.Script.txt',
					},
					'settings': {
						'S_FinishTimeout': 10,
						'S_PointsLimit': 180,
						'S_WarmUpNb': 1,
						'S_WarmUpDuration': 0,
						'S_PointsRepartition': '50,45,41,38,36,34,32,30,28,26,24,22,20,18,16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,1,1',
						'S_TurboFinishTime': True,
					},
				},

				'rounds240': {
					'aliases': [],
					'script': {
						'tm': 'Rounds.Script.txt',
						'tmnext': 'Trackmania/TM_Rounds_Online.Script.txt',
					},
					'settings': {
						'S_FinishTimeout': 10,
						'S_PointsLimit': 240,
						'S_WarmUpNb': 1,
						'S_WarmUpDuration': 900,
						'S_PointsRepartition': '50,45,41,38,36,34,32,30,28,26,24,22,20,18,16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,1,1',
						'S_TurboFinishTime': True,
					},
				},

				'rounds480': {
					'aliases': [ 'mxlc', 'mxvc', 'nac' ],
					'script': {
						'tm': 'Rounds.Script.txt',
						'tmnext': 'Trackmania/TM_Rounds_Online.Script.txt',
					},
					'settings': {
						'S_FinishTimeout': 10,
						'S_PointsLimit': 480,
						'S_WarmUpNb': 1,
						'S_WarmUpDuration': 600,
						'S_PointsRepartition': '50,45,41,38,36,34,32,30,28,26,24,22,20,18,16,15,14,13,12,11,10,9,8,7,6,5,4,3,2,1,1,1',
						'S_TurboFinishTime': True,
					},
				},

				'laps50': {
					'aliases': [ 'hec' ],
					'script': {
						'tm': 'Laps.Script.txt',
						'tmnext': 'Trackmania/TM_Laps_Online.Script.txt',
					},
					'settings': {
						'S_FinishTimeout': 360,
						'S_ForceLapsNb': 50,
						'S_WarmUpNb': 1,
						'S_WarmUpDuration': 600,
					},
				},

				'timeattack': {
					'aliases': [ 'ta' ],
					'script': {
						'tm': 'TimeAttack.Script.txt',
						'tmnext': 'Trackmania/TM_TimeAttack_Online.Script.txt',
					},
					'settings': {
						'S_TimeLimit': 360,
						'S_WarmUpNb': 0,
						'S_WarmUpDuration': 0,
					},
				},

			}
		return presets


	async def _command_setup(self, player, data, **kwargs) -> None:
		cmd_preset = data.preset.lower()
		presets = await self.get_presets()
		selected_preset = None
		for preset_key, preset_data in presets.items():
			if cmd_preset == preset_key or cmd_preset in preset_data['aliases']:
				selected_preset = preset_key
				break

		if selected_preset in presets:
			preset_data = presets[selected_preset]

			if 'script' in preset_data and self.instance.game.game in preset_data['script']:
				await self.instance.mode_manager.set_next_script(preset_data['script'][self.instance.game.game])

			if 'settings' in preset_data:
				await self.instance.mode_manager.update_next_settings(preset_data['settings'])

			if 'commands' in preset_data:
				for command in preset_data['commands']:
					await self.instance.gbx.script(*command, encode_json=False, response_id=False)

			await self.app.instance.chat(f"$i$fffSet next script settings to preset '{selected_preset}'", player)
		else:
			await self.app.instance.chat(f"$i$f00Unknown preset name '{data.preset}'.\nAvailable presets are: {', '.join(presets.keys())}", player)
