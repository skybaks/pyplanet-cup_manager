# Cup Manager Setup and Usage

**Contents**
* [Setting up with a dedicated server](./usage.md#setting-up-with-a-dedicated-server)
    * [Set up Pyplanet](./usage.md#set-up-pyplanet)
    * [Get the plugin code](./usage.md#get-the-plugin-code)
    * [Install the plugin](./usage.md#install-the-plugin)
    * [Set up a local.py](./usage.md#set-up-a-local.py)
* [Running a cup as server admin](./usage.md#running-a-cup-as-server-admin)
    * [Set up before the cup map starts](./usage.md#set-up-before-the-cup-map-starts)
        * [Choose the mode script and settings preset](./usage.md#choose-the-mode-script-and-settings-preset)
        * [Start the cup logic](./usage.md#start-the-cup-logic)
        * [Set the number of maps](./usage.md#set-the-number-of-maps)
    * [During the cup](./usage.md#during-the-cup)
        * [Reset the mode script and settings](./usage.md#reset-the-mode-script-and-settings)
        * [Notify the cup logic of cup end](./usage.md#notify-the-cup-logic-of-cup-end)
* [Plugin operations as a player](./usage.md#plugin-operations-as-a-player)

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

## Set up a local.py

> This is optional.

A "local.py" is an optional settings file which Pyplanet can load to provide additional custom information to plugins.
This plugin opts to use the format of a local.py file rather than your server database to store information about mode
presets, payout schemas, etc... because it is much easier to copy your customizations between multiple servers you host in
this format.

If you do not already have a local.py file in your Pyplanet settings folder then you can copy the one from the settings
folder in cup_manager. [This one is provided as an example](./settings/local.py).

`CUP_MANAGER_PRESETS` defines the script and setting presets which are available from the command `//cup setup <preset>`.

`CUP_MANAGER_PAYOUTS` defines the payment schemes that are available to admins from the "Payout" button on a match results
screen.

TODO: `CUP_MANAGER_NAMES`

# Running a cup as server admin

## Set up before the cup map starts

The expected use cases for this plugin are competitions in Rounds or Laps modes. The server is most likely starting in
TimeAttack mode before the cup. This is good because Pyplanet and the dedicated server provide the most consistent results
from the "setup" command.

### Choose the mode script and settings preset

If you know the name of the preset you want, run the command:

```
//cup setup <preset_name>
```

If you dont remember the name of the preset, run this command instead and you will be able to pick from all the defined
presets:

```
//cup setup
```

### Start the cup logic

Activating the cup logic tells the plugin that it should pay special attention to next map(s) and adds some special
printouts to keep players updated on maps and scores.

If you have defined named cups in the "local.py" under CUP_MANAGER_NAMES, you can use them now by entering the key name as an argument to the command:

```
//cup on <cup_key_name>
```

If you dont have any named cups defined you can run an anonymous cup by simply entering the command:

```
//cup on
```

TODO: decide on how the edition will be implemented

### Set the number of maps

For a multi-map cup (more than one map), you can define the number of maps in the cup. Then with the cup logic active, you
can see a nice message printed at the start of each map that says something like "Map X of Y". If you are not running a multilap cup (one cup map), you can skip running this command.

```
//cup mapcount <number_of_maps>
```

## During the cup

While the cup is running there is not really any actions you need to take **until you reach the final map**.

### Reset the mode script and settings

After the cup is over you want to immediately switch back to the mode the server was playing before the cup started. This is most likely TimeAttack. On the final cup map run the command:

```
//cup setup <preset>
```

With the TimeAttack preset so that the map immediately following the cup will return to TimeAttack mode.

### Notify the cup logic of cup end

On the final map of the cup you want to tell the cup logic. At any time while the final map is playing, run the following command:

```
//cup off
```

## After the cup

tbh

# Plugin operations as a player
tbd
