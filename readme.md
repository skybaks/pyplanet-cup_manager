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
| `//cup setup` | `//cup s` | Open a GUI to display all presets which are available to the current game. From this GUI you can also choose a preset and apply it. |
| `//cup setup [name]` | `//cup s [name]` | Apply the match settings of a particular preset configuration. For most consistent results *ALWAYS* switch to a different mode script than the current. |


## Preset Setup types

The following default presets are defined:

* rounds180 / smurfscup / sc
* rounds240
* rounds480 / mxlc
* laps50 / hec
* timeattack / ta

If you would like to define your own presets, copy the **local.py** file from the settings folder in this repository into your settings folder for pyplanet. Then modify or update it according to your needs.


## Planet Payout Handling

If the game is Trackmania 2 or Shootmania and the pyplanet transactions module is enabled, admins will have access to a "Payout" button on the results view of any match or sum of matches.
From there they can choose a payment scheme and then send planets to players based on their placement. The implementation of the payment uses the transaction module's `//pay` command and subsequently
is only available to admins with the correct permissions.

Some default payment schemes are provided based on existing competitions. To define your own payment schemes see the `CUP_MANAGER_PAYOUTS` field of the **local.py** file in the settings folder.
You will need to add a local.py file to your pyplanet settings folder and then define that variable as desired.


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
* Speedtrap

**Shootmania**
* Melee
* Elite
* Royal
* Siege
* Infection
* Combo
