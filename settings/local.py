"""
Copy this 'local.py' file into your pyplanet settings folder to modify the
behavior of the cup_manager plugin. If you already have a local.py file then you
can add these settings to the existing file.
"""


# Use this to define preset script settings which can be activated from the
# "//cup setup" command. A different script must be defined for each game. For
# TM2 Maniaplanet use `tm`, for TM2020 use 'tmnext', and for Shootmania use 'sm'.
CUP_MANAGER_PRESETS = {
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


# Use this to define planet reward payouts. Admins can select from these payout
# schemes from the match results view.
CUP_MANAGER_PAYOUTS = {
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


# Use this to define the name and alias of cup.
CUP_MANAGER_NAMES = {

	'mxlc': {
		'name': 'ManiaExchange Lagoon Cup',
		'preset_on': 'mxlc',
		'preset_off': 'timeattack',
		'map_count': 1,
	},

	'hec': {
		'name': 'Hypeboys Endurance Cup',
		'preset_on': 'laps50',
		'preset_off': 'timeattack',
		'map_count': 1,
	},

	'nac': {
		'name': 'North America Cup',
		'preset_on': 'nac',
		'preset_off': 'timeattack',
		'map_count': 1,
	},

	'tec': {
		'name': 'Expedition Cup',
		'preset_on': 'rounds180',
		'preset_off': 'timeattack',
		'map_count': 5,
	},

	'tmic': {
		'name': 'TM2 Island Cup',
		'preset_on': 'rounds480',
		'preset_off': 'timeattack',
		'map_count': 1,
	},

	'tmrc': {
		'name': 'TMOne Retro Cup',
		'preset_on': 'rounds480',
		'preset_off': 'timeattack',
		'map_count': 1,
	},

}
