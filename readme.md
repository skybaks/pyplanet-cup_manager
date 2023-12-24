# Cup Manager

A plugin for [PyPlanet](https://pypla.net/).

This plugin will handle hosting a cup competition in Trackmania, Maniaplanet, and Shootmania. It provides a competition
host with the following:

* Manage mode scripts and settings to ensure consistent competitions
* Record player score results and sum totals across multiple maps
* Provide player placement status information and podium results
* Use result totals to pay planets to players in batch
* Export results in multiple formats including Csv and Discord

The following games and modes have been tested and shown to have some level of functionality. In general, this plugin
will work with any script mode which supports the scores callback.

* Trackmania - Timeattack, Rounds, Laps, MedalAttack, Speedtrap
* Maniaplanet - Timeattack, Rounds, Laps
* Shootmania - Melee, Elite, Royal, Siege, Infection, Combo


# Cup Manager Setup and Usage

**Contents**
* [Setting up with a dedicated server](./readme.md#setting-up-with-a-dedicated-server)
    * [Set up Pyplanet](./readme.md#set-up-pyplanet)
    * [Install the plugin](./readme.md#install-the-plugin)
* [Customizing the cup configuration](./readme.md#customizing-the-cup-configuration)
    * [Create, Load, or Edit a Cup Configuration](./readme.md#create-load-or-edit-a-cup-configuration)
        * [Edit the Current Config](./readme.md#edit-the-current-config)
        * [Load a Config File](./readme.md#load-a-config-file)
        * [Download a Config File](./readme.md#download-a-config-file)
        * [Create a New Config](./readme.md#create-a-new-config)
    * [Create a Cup Configuration File Manually](./readme.md#create-a-cup-configuration-file-manually)
        * [Cup Config File: Names](./readme.md#cup-config-file-names)
        * [Cup Config File: Presets](./readme.md#cup-config-file-presets)
        * [Cup Config File: Payouts](./readme.md#cup-config-file-payouts)
    * [Cup Configuration Location](./readme.md#cup-configuration-location)
* [Running a cup as server admin](./readme.md#running-a-cup-as-server-admin)
    * [Admin quick reference](./readme.md#admin-quick-reference)
    * [Set up before the cup map starts](./readme.md#set-up-before-the-cup-map-starts)
        * [Start the cup logic](./readme.md#start-the-cup-logic)
            * [Update the cup edition](./readme.md#update-the-cup-edition)
            * [Update the cup map count](./readme.md#update-the-cup-map-count)
        * [Choose the mode script and settings preset](./readme.md#choose-the-mode-script-and-settings-preset)
        * [Choose a specific score sorting mode](./readme.md#choose-a-specific-score-sorting-mode)
    * [During the cup](./readme.md#during-the-cup)
        * [Add or remove maps from the active cup](./readme.md#add-or-remove-maps-from-the-active-cup)
        * [Notify the cup logic of cup end](./readme.md#notify-the-cup-logic-of-cup-end)
        * [Reset the mode script and settings](./readme.md#reset-the-mode-script-and-settings)
    * [After the cup](./readme.md#after-the-cup)
        * [Export the cup results](./readme.md#export-the-cup-results)
        * [Pay planets to the winners](./readme.md#pay-planets-to-the-winners)
* [Plugin operations as a player](./readme.md#plugin-operations-as-a-player)
    * [Player quick reference](./readme.md#player-quick-reference)

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

# Customizing the cup configuration

The plugin contains the means to customize to fit your competition's needs through the `//cup config` command. This
allows customization of the `//cup on <name>` command and enables further automation in cup execution.

The recommended way to customize to meet your cup's needs is through the in-server UI. However, the configuration can
also be created through a Json formatted text file and loaded from your dedicated server location or downloaded from a
Url.

## Create, Load, or Edit a Cup Configuration

Commands quick reference:

```
//cup config
//cup config load <filename>
//cup config download <url>
//cup config new <filename>
```

### Edit the Current Config

To edit the currently loaded config file, use the following command:

```
//cup config
```

This will launch the config editing UI where you can make changes and the press "Save" to commit those changes.

### Load a Config File

To load a different config file, use the following command:

```
//cup config load <filename>
```

This will unload the current config file and load the specified one, if it exists.

### Download a Config File

To download a config file, use the following command:

```
//cup config download <url>
```

This will download the all the text at the given Url and create a new config file. For example, if downloading a file
from Github, make sure to use the raw link so that it only downloads the Json file contents. When it comes to the name
of the new config file, the last part of the given Url will be used. For example, if the Url was
`https://raw.githubusercontent.com/skybaks/pyplanet-cup_manager/master/settings/cup_manager_config.json` then the
filename would be set to "cup_manager_config.json".

### Create a New Config

> When starting the plugin for the first time it is not necessary to use this command. The plugin already creates a new
> config file for you by default.

To create a new config file, use the following command:

```
//cup config new <filename>
```

This will create a new config file with some default settings, and then open the editing UI.

## Create a Cup Configuration File Manually

The cup configuration file is a Json formatted text file with a specific structure. See
[cup_manager_config](./settings/cup_manager_config.json) for an example.

The base level of the config file contains three elements like so:

```jsonc
{
    "names": {},
    "presets": {},
    "payouts": {}
}
```

### Cup Config File: Names

The "names" config contains the names of the cups which you are going to run from the plugin as well as any additional
information tying these cups to any presets or payouts which are also defined in the config file.

```jsonc
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

```jsonc
{
    "my_cup": {
        "name": "My Cup",

        /* [Optional]
            Use preset_on and preset_off fields to link starting and stopping the cup to automatically trigger a
            settings preset. You can define one or the other or both.
            - preset_on is equivalent to running "//cup setup <preset>" immediately after starting the cup
            - preset_off is equivalent to running "//cup setup <preset>" immediately after the cup ends
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

### Cup Config File: Presets

The presets section of the config file allows you to define a preset mode script and settings. Each preset that you
define can be invoked using the `//cup setup <preset>` command.

```jsonc
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

### Cup Config File: Payouts

The payouts section of the config file is used to define a award scheme for planets. In games which support planets,
the defined payouts can be accessed from the cup results to pay the winning players in batch.

```jsonc
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

## Cup Configuration Location

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

> This step is completely optional and only should be used when your cup needs score sorting logic not covered in the
> default behaviors.

The plugin has automatic detection built in for most common mode scripts in Trackmania and Maniaplanet as well as some
generic fallback sorting modes which should cover a large variety of cases. However, you may still be interested in
using a specific sorting mode for your cup. In that case use the command following command to set it:

```
//cup scoremode <scoremode_id>
```

If you dont know the name of the mode, run the following command instead and it will open a window you can use the pick
the sorting mode you want.

```
//cup scoremode
```

## During the cup

### Add or remove maps from the active cup

If for any reason there was some problem and you need to include or exclude a scored map from the cup results you can
using this command:

```
//cup edit
```

This will open a window showing the scored maps that are currently included in the cup. From the far left column you
can click to add or remove maps.

### Notify the cup logic of cup end

> This step is not necessary if you told the plugin your map count

If you are not using a defined map count you will manually need to tell the plugin when the cup has reached the final
map.

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

After the cup is over you can use the export window to get the cup results in a variety of formats. If you ran the cup
using the `//cup on` command then you can get to the results window using the command:

```
/cup results
```

From the results window click the "Export" button, then modify the settings as you desire copy the text to your
clipboard.

If you did not use the `//cup on` command to run the cup you can still access cup results. Use the command:

```
/cup matches
```

To open a view of all previous matches. Use the leftmost checkboxes to select all cup maps then click the "Sum Sel."
button to view the summed results for all the selected maps. From there you can click the "Export" button and follow
the same steps as above to export the results via your clipboard.

### Pay planets to the winners

If you are in a game that supports paying players planets and you have defined some payout schemes in your local.py
file, you can pay players based on the cup results. Follow the instructions above to get to the cup results either
using `/cup results` or `/cup matches`, then click the button "Payout" to open the payout window.

# Plugin operations as a player

## Player quick reference

```
/cup results
/cup cups
/cup matches
```
