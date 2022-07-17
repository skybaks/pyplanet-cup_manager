# Cup Manager Setup and Usage

**Contents**
* [Setting up with a dedicated server](./usage.md#setting-up-with-a-dedicated-server)
    * [Set up Pyplanet](./usage.md#set-up-pyplanet)
    * [Get the plugin code](./usage.md#get-the-plugin-code)
    * [Install the plugin](./usage.md#install-the-plugin)
    * [Set up a local py file](./usage.md#set-up-a-local-py-file)
* [Running a cup as server admin](./usage.md#running-a-cup-as-server-admin)
    * [Admin quick reference](./usage.md#admin-quick-reference)
    * [Set up before the cup map starts](./usage.md#set-up-before-the-cup-map-starts)
        * [Start the cup logic](./usage.md#start-the-cup-logic)
            * [Update the cup edition](./usage.md#update-the-cup-edition)
            * [Update the cup map count](./usage.md#update-the-cup-map-count)
        * [Choose the mode script and settings preset](./usage.md#choose-the-mode-script-and-settings-preset)
        * [Set the number of maps](./usage.md#set-the-number-of-maps)
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

Pyplanet has a very robust set of documentation and extremely helpful directions on how to get it set up. Go to: https://pypla.net/

## Get the plugin code

With Pyplanet configured you will need to acquire the code for this plugin. You can do this by either downloading a
[zip archive of the plugin code](https://github.com/skybaks/pyplanet-cup_manager/tags) or use git to clone the repository.

## Install the plugin

Locate the directory where you have set up Pyplanet. This is the folder where "manage.py" lives. If an "apps" folder does
not exist yet for your Pyplanet installation I recommend you create one now in that same folder with "manage.py".

Place the downloaded or cloned plugin code inside this apps folder. If you downloaded a zip archive then unzip it to here.
The path where you placed the plugin code is important. It doesnt have to match this guide exactly but unless you are
confident in your knowledge of how Pyplanet plugin loading works I recommend you follow this path structure.

After the plugin is installed you should have the following:

```
my_pyplanet
\ apps
    \ cup_manager
        \ cup_manager
        \ settings
        - .gitignore
        - readme.md
        - usage.md
\ env
\ settings
    - __init__.py
    - apps.py
    - base.py
- manage.py
```

Then you will need to add the plugin to your "settings\apps.py". Add the following to the list of apps to load:

```
'apps.cup_manager.cup_manager',
```

## Set up a local py file

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

# Running a cup as server admin

## Admin quick reference

Quick reference of all commands that *might* be relevant to a cup admin. Read below for more specific usage information.

```
-- Before Cup --
//cup on <cup_name>
//cup edition <edition_number>
//cup mapcount <map_count>
//cup setup <cup_settings_preset>

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
