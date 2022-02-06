# Cup Manager
Cup Manager is a plugin for Pyplanet, the python server controller for Maniaplanet and Trackmania.

This goal of this plugin is to automate or simplify the actions needed to manage or run a simple cup competition in these games. In this context, "cup" does not refer specifically to the online Cup mode but rather to the generic name for any simple trackmania competition usually played in rounds on one or a couple maps.

Commands for everyone:

| Command | Shorthand | Description |
| --- | --- | --- |
| `/cup matches` | `/cup m` | Browse through previous matches and use the checkboxes to view aggregate scores. |

Commands for admins:

| Command | Shorthand | Description |
| --- | --- | --- |
| `//cup matches`      | `//cup m`        | Same effect as the non-admin version. |
| `//cup setup [type]` | `//cup s [type]` | Apply the match settings of a particular preset configuration. For most consistent results *ALWAYS* switch to a different mode script than the current. |


## Preset Setup types

* rounds180 / smurfscup / sc
* rounds240
* rounds480 / mxlc
* laps50 / hec
* timeattack / ta


## Supported games and modes

**TM Maniaplanet**
* Timeattack
* Rounds
* Laps

**TM 2020**
* Timeattack
* Rounds
* Laps
* MedalAttack

**Shootmania**
* Melee - *Implemented, needs testing*

