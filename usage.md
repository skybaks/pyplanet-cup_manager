# Cup Manager Setup and Usage

**Contents**
* [Setting up with a dedicated server](./usage.md#setting-up-with-a-dedicated-server)
    * [Set up Pyplanet](./usage.md#set-up-pyplanet)
    * [Install the plugin](./usage.md#install-the-plugin)
    * [DEPRECATED] [Set up a local py file](./usage.md#set-up-a-local-py-file)
    * [Customizing the cup configuration](./usage.md#customizing-the-cup-configuration)
* [Running a cup as server admin](./usage.md#running-a-cup-as-server-admin)
    * [Admin quick reference](./usage.md#admin-quick-reference)
    * [Set up before the cup map starts](./usage.md#set-up-before-the-cup-map-starts)
        * [Start the cup logic](./usage.md#start-the-cup-logic)
            * [Update the cup edition](./usage.md#update-the-cup-edition)
            * [Update the cup map count](./usage.md#update-the-cup-map-count)
        * [Choose the mode script and settings preset](./usage.md#choose-the-mode-script-and-settings-preset)
        * [Choose a specific score sorting mode](./usage.md#choose-a-specific-score-sorting-mode)
    * [During the cup](./usage.md#during-the-cup)
        * [Add or remove maps from the active cup](./usage.md#add-or-remove-maps-from-the-active-cup)
        * [Notify the cup logic of cup end](./usage.md#notify-the-cup-logic-of-cup-end)
        * [Reset the mode script and settings](./usage.md#reset-the-mode-script-and-settings)
    * [After the cup](./usage.md#after-the-cup)
        * [Export the cup results](./usage.md#export-the-cup-results)
        * [Pay planets to the winners](./usage.md#pay-planets-to-the-winners)
* [Plugin operations as a player](./usage.md#plugin-operations-as-a-player)
    * [Player quick reference](./usage.md#player-quick-reference)

# Setting up with a dedicated server

## Set up Pyplanet

This plugin runs from within the Pyplanet server controller. You will need to have pyplanet configured and working
before starting to set up this plugin.

Pyplanet has a very robust set of documentation and extremely helpful directions on how to get it set up. Go to:
https://pypla.net/

## Install the plugin

Run the command to install the latest version of the plugin.

```
python -m pip install --upgrade pyplanet-cup-manager
```

Then you will need to add the plugin to your "settings\apps.py". Add the following to the list of apps to load:

```
"skybaks.cup_manager",
```

## Set up a local py file

**⚠ Use of the local.py file is DEPRECATED and could be removed in future updates.** Please use instead
[Customizing the cup configuration](./usage.md#customizing-the-cup-configuration).

> This is optional but you should try to set one up if you want to utilize full functionality of the plugin.

A "local.py" is an optional settings file which Pyplanet can load to provide additional custom information to plugins.
This plugin opts to use the format of a local.py file rather than your server database to store information about mode
presets, payout schemas, etc... because it is much easier to copy your customizations between multiple servers you
host in this format.

If you do not already have a local.py file in your Pyplanet settings folder then you can copy the one from the settings
folder in cup_manager. [This one is provided as an example](./settings/local.py).

**`CUP_MANAGER_PRESETS` defines the script and setting presets which are available from the command `//cup setup <preset>`.**
This is a python dictionary of preset entries where the key value is the preset lookup name.
|Preset Subfield|Value Type|Required|Usage|
|---------------|----------|--------|-----|
|aliases|list[str]|Yes|Define an optional list of additional names which can be used to trigger the preset|
|script|dict[str,str]|Yes|Set the mode script to load with this preset on a per game basis where the key value is the short identifier for the game. valid game identifiers are 'tm' for maniaplanet, 'sm' for shootmania, and 'tmnext' for tm2020|
|settings|dict[str,Any]|Yes|Define the script settings to be applied when the mode script loads|

**`CUP_MANAGER_PAYOUTS` defines the payment schemes that are available to admins from the "Payout" button on a match results screen.**
This is a python dictionary where the key value should be a meaningful name and the value should be a list[int]
of the number of planets to pay each player ordered from first to last.

**`CUP_MANAGER_NAMES` defines the name and associated default settings for a given cup.**
By defining cup default settings here you can greatly increase the level of automation from the plugin. The key is the
lookup name for the cup which is what you will pass into the `//cup on <cup_name>` command.
|Cup Subfield|Value Type|Required|Usage|
|------------|----------|--------|-----|
|name|str|Yes|The verbose name for the cup which will be used in ingame chat messages and saved in the cup results|
|preset_on|str|Optional|Include this subfield if you would like to have `//cup set <preset>` called automatically for you when you start the cup. The value should match a key name or alias name of on of your defined presets|
|preset_off|str|Optional|Include this subfield if you would like to have `//cup setup <preset>` called automatically for you when you end the cup. The value should match a key name or alias name of on of your defined presets|
|map_count|int|Optional|This will set the cup mapcount automatically when you start the cup. If a non-zero mapcount is set for a cup it will automatically end itself after the defined number of maps has passed. You can always change an active cup's mapcount using the `//cup mapcount <count>` command|
|payout|str|Optional|This is used to link a certain payout scheme to your cup. This linkage will be used to default the selection on the payout and export windows.|
|scoremode|str|Optional|Use this to predefine a score sorting mode for the cup. If left undefined the default sorting mode for your mode script will be used.|

## Customizing the cup configuration

Setting up your cup specifics in the configuration is meant to reduce workload ingame when running your cup.

The configuration is customized with a json file. Using this file you can enter the name of your specific cup, the
number of maps the competition will be over, the kind of scoring you want to use, one or more mode script setting
presets, and even a planets payout scheme.

### Create a Cup Configuration File

The cup configuration file is a Json formatted text file with a specific structure. See
[cup_manager_config](./settings/cup_manager_config.json) for an example.

The base level of the config file contains three elements like so:

```json
{
    "names": {},
    "presets": {},
    "payouts": {}
}
```

#### Cup Config File: Names

The "names" config contains the names of the cups which you are going to run from the plugin as well as any additional
information tying these cups to any presets or payouts which are also defined in the config file.

```json
{
    "my_cup": {
        "name": "My Cup"
    },
    "my_other_cup": {
        "name": "My Other Cup"
    }
}
```

The most simple instantiation of a named cup is defined with only a "name" attribute that will be the display name of
the cup. In the example above, the key names "my_cup" and "my_other_cup" are the ID names that would be used with the
`//cup on <ID>` command to start the cup from in game.

```json
{
    "my_cup": {
        "name": "My Cup",

        /* [Optional]
            Use preset_on and preset_off fields to link starting and stopping the cup to automatically trigger a
            settings preset. You can define one or the other or both.
            - preset_on is equivalent to running "//cup setup <preset>" immediately after starting the cup
            - preset_off is equivalent to running "//cup setup <preset>" imemdiately after the cup ends
        */
        "preset_on": "my_rounds_preset",
        "preset_off": "my_timeattack_preset",

        /* [Optional]
            Use map_count to predefine the number of maps the cup will be played on. This is equivalent to running
            "//cup mapcount <map_count>" right after you start the cup.
        */
        "map_count": 7,

        /* [Optional]
            Use payout to predefine the payout config this cup will be using. The value entered in this field should
            match the ID name of a payout defined in this config file.
            Predefining the payout here will make it easier to access from the results and will make it appear in the
            exported results.
        */
        "payout": "my_payout",

        /* [Optional]
            Use scoremode to force the type of score behavior for the cup. This is equivalent to running
            "//cup scoremode <score_mode>" after starting a cup. If included the field should be set to one of the
            scoremode IDs found when running "//cup scoremode"
        */
        "scoremode": "score_mode_mixed"
    }
}
```

Shown above are the additional optional fields which can be added to further customize a defined cup. Each is
documented in the attached comment.

#### Cup Config File: Presets

The presets section of the config file allows you to define a preset mode script and settings. Each preset that you
define can be invoked using the `//cup setup <preset>` command.

```json
{
    "my_preset": {

        /*
            The aliases section of the preset defines shorthand names that can be used with the "//cup setup" command
            instead of the full preset identifier.
            In the case of this current example preset, each of the following commands could be used to activate:
            - //cup setup my_preset
            - //cup setup mp
            - //cup setup 1
        */
        "aliases": [ "mp", "1" ],

        /*
            The script field contains the name of the mode script to be used with this preset along with what game it
            is associated with. Since script filenames can differ between games, this is designed to allow for preset
            reuse. You are only required to define at least one script.
            The available game names are:
            - tm        -> Used for Maniaplanet
            - tmnext    -> Used for Trackmania (2020)
            - sm        -> Used for Shootmania
        */
        "script": {
            "tm": "Rounds.Script.txt",
            "tmnext": "Trackmania/TM_Rounds_Online.Script.txt"
        },

        /*
            This field is used to define settings that will be applied to the mode script when the preset is activated.
            Define any number of script settings along with the value you want to be applied.
        */
        "settings": {
            "S_FinishTimeout": 10,
            "S_PointsLimit": 240,
            "S_PointsRepartition": "15,12,10,8,6,4,3,3,3,2,2,2,1"
        }
    },

    "my_other_preset": {
        "aliases": [],
        "script": {
            "tmnext": "Trackmania/TM_TimeAttack_Online.Script.txt"
        },
        "settings": {
            "S_TimeLimit": 360,
        }
    }
}
```

Shown above is an example of two presets with comments used to document each of the sub-fields. Any number of presets
can be defined in the config file.

The identifiers "my_preset" and "my_other_preset" are simply examples and your presets can use whatever identifier
names that are meaningful to you. These identifiers are also what would be used for the "preset_on" or "preset_off"
fields in the names config.

#### Cup Config File: Payouts

The payouts section of the config file is used to define a award scheme for planets. In games which support planets,
the defined payouts can be accessed from the cup results to pay the winning players in batch.

```json
{
    /*
        In this case, "my_payout" can be whatever name you would like to use to identify the payout by. The numbers in
        this array define the payment scheme in order where the first element would be given the highest ranked player.
    */
    "my_payout": [ 500, 250, 100 ],

    "my_other_payout": [6000, 1000, 500, 200, 100, 50]
}
```

Shown above is an example of payouts annotated with comments. The names of the payouts shown here "my_payout" and
"my_other_payout" are custom and you can define your payouts with any names that are meaningful to you. These names are
the identifiers for the payouts and would also be used along with the "payout" field in the names config.

### Cup Configuration Location

The default location for saving and loading cup configuration json files is `UserData/Maps/MatchSettings` under the
dedicated server.
This value can be changed by adding `CUP_MANAGER_CONFIG_PATH` to your pyplanet settings file. However, it is
recommended in most instances to stick with the defaults.


# Running a cup as server admin

## Admin quick reference

Quick reference of all commands that *might* be relevant to a cup admin. Read below for more specific usage information.

```
-- Before Cup --
//cup on <cup_name>
//cup edition <edition_number>
//cup mapcount <map_count>
//cup setup <cup_settings_preset>
//cup scoremode <cup_scoremode_id>

-- During Cup --
//cup edit

-- Last Cup Map --
//cup off
//cup setup <ta_settings_preset>

-- After Cup --
/cup results
/cup matches
```

## Set up before the cup map starts

The expected use cases for this plugin are competitions in Rounds or Laps modes. The server is most likely starting in
TimeAttack mode before the cup. This is good because Pyplanet and the dedicated server provide the most consistent
results from the "setup" command when you switch from one mode script to another.

### Start the cup logic

Activating the cup logic tells the plugin that it should pay special attention to next map(s) and adds some special
printouts to keep players updated on maps and scores.

If you have defined named cups in the "local.py" under CUP_MANAGER_NAMES, you can use them now by entering the key
name as an argument to the command:

```
//cup on <cup_key_name>
```

If you dont have any named cups defined you can run an anonymous cup by simply entering the command:

```
//cup on
```

#### Update the cup edition

The plugin will automatically look up the edition of the last time you ran a cup with this key name and set the current
edition to 1 + last edition. Sometimes that isnt correct so you can change that with the following command.

```
//cup edition <edition_number>
```

#### Update the cup map count

If you know how many maps will be in your cup you can set the cup map count. This enables the plugin to print out
informational messages at the start of each cup map that say "map X of Y". Additionally, when the final map is reached
the plugin will automatically end the cup for you by running the internal eqivalent of the `//cup off` command.

```
//cup mapcount <map_count>
```

If you dont want to deal with the auto-end logic then you can set the map count to 0 and the cup will run until you
stop it.

### Choose the mode script and settings preset

> This step is not necessary if you are using the `//cup on` command with a defined "preset_on" field in the local.py

If you are not using the `//cup on` command, or there is no preset linked automatically to your cup, or you want to use a
different preset than the cup default, you can change that using this setup command.

```
//cup setup <preset_name>
```

If you dont remember the name of the preset, run this command instead and you will be able to pick from all the
defined presets:

```
//cup setup
```

### Choose a specific score sorting mode

> This step is completely optional and only should be used when your cup needs score sorting logic not covered in the default behaviors.

The plugin has automatic detection built in for most common mode scripts in Trackmania and Maniaplanet as well as some generic fallback sorting modes which should cover a large variety of cases. However, you may still be interested in using a specific sorting mode for your cup. In that case use the command following command to set it:

```
//cup scoremode <scoremode_id>
```

If you dont know the name of the mode, run the following command instead and it will open a window you can use the pick the sorting mode you want.

```
//cup scoremode
```

## During the cup

### Add or remove maps from the active cup

If for any reason there was some problem and you need to include or exclude a scored map from the cup results you can using this command:

```
//cup edit
```

This will open a window showing the scored maps that are currently included in the cup. From the far left column you
can click to add or remove maps.

### Notify the cup logic of cup end

> This step is not necessary if you told the plugin your map count

If you are not using a defined map count you will manually need to tell the plugin when the cup has reached the final map.

```
//cup off
```

### Reset the mode script and settings

> This step is not necessary if you are using `//cup on` with a defined "preset_off" field

After the cup is over you want to immediately switch back to the mode the server was playing before the cup started.
This is most likely TimeAttack. On the final cup map run the command:

```
//cup setup <preset>
```

With the TimeAttack preset so that the map immediately following the cup will return to TimeAttack mode.

## After the cup

### Export the cup results

After the cup is over you can use the export window to get the cup results in a variety of formats. If you ran the cup using the `//cup on` command then you can get to the results window using the command:

```
/cup results
```

From the results window click the "Export" button, then modify the settings as you desire copy the text to your clipboard.

If you did not use the `//cup on` command to run the cup you can still access cup results. Use the command:

```
/cup matches
```

To open a view of all previous matches. Use the leftmost checkboxes to select all cup maps then click the "Sum Sel."
button to view the summed results for all the selected maps. From there you can click the "Export" button and follow
the same steps as above to export the results via your clipboard.

### Pay planets to the winners

If you are in a game that supports paying players planets and you have defined some payout schemes in your local.py
file, you can pay players based on the cup results. Follow the instructions above to get to the cup results either using `/cup results` or `/cup matches`, then click the button "Payout" to open the payout window.

# Plugin operations as a player

## Player quick reference

```
/cup results
/cup cups
/cup matches
```
