import logging

from pyplanet.conf import settings
from pyplanet.contrib.command import Command
from pyplanet.apps.core.maniaplanet import callbacks as mp_signals
from pyplanet.apps.core.trackmania import callbacks as tm_signals


from .views import PresetsView

logger = logging.getLogger(__name__)

class SetupCupManager:
	def __init__(self, app) -> None:
		self.app = app
		self.instance = app.instance
		self.context = app.context


	async def on_start(self) -> None:
		self.context.signals.listen(mp_signals.map.map_start, self.check_points_repartition)
		self.context.signals.listen(mp_signals.flow.round_start, self.check_points_repartition)

		await self.instance.permission_manager.register('setup_cup', 'Change match settings from the cup_manager', app=self.app, min_level=2, namespace=self.app.namespace)

		await self.instance.command_manager.register(
			Command(command='setup', aliases=['s'], namespace=self.app.namespace, target=self.command_setup,
				admin=True, perms='cup:setup_cup', description='Setup match settings based on some common presets.').add_param('preset', required=False),
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


	async def command_setup(self, player, data, **kwargs) -> None:
		if not await self.instance.permission_manager.has_permission(player, 'cup:setup_cup'):
			return

		if data.preset:
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

				await self.app.instance.chat(f"$z$s$i$0cfSet next script settings to preset: $<$fff{selected_preset}$>", player)
			else:
				await self.app.instance.chat(f"$z$s$i$f00Unknown preset name $<$fff'{data.preset}'$>\nAvailable presets are: $<$fff{', '.join(presets.keys())}$>", player)
		else:
			view = PresetsView(self)
			await view.display(player=player)


	async def check_points_repartition(self, *args, **kwargs) -> None:
		# Need to verify points repartition in the mode script backend is set
		# to the values we wanted. This has been observed to be sometimes inconsistent.
		current_script = (await self.instance.mode_manager.get_current_script()).lower()
		if 'rounds' in current_script or 'team' in current_script or 'cup' in current_script:
			script_current_settings = await self.instance.mode_manager.get_settings()

			if 'S_PointsRepartition' in script_current_settings and script_current_settings['S_PointsRepartition']:
				pointsrepartition_desired = [int(point) for point in script_current_settings['S_PointsRepartition'].split(',')]
				getpointsrepartition_response = await self.instance.gbx.script('Trackmania.GetPointsRepartition', encode_json=False)

				if 'pointsrepartition' in getpointsrepartition_response:
					pointsrepartition_actual = getpointsrepartition_response['pointsrepartition']

					if pointsrepartition_actual != pointsrepartition_desired:
						logger.debug('Current PointsRepartition is not equal to S_PointsRepartition. Performing correction...')
						await self.instance.gbx.script(*(['Trackmania.SetPointsRepartition'] + [str(point) for point in pointsrepartition_desired]), encode_json=False, response_id=False)
