# Cup Manager Setup and Usage

**Contents**
* [Setting up with a dedicated server](./usage.md#setting-up-with-a-dedicated-server)
    * [Set up Pyplanet](./usage.md#set-up-pyplanet)
    * [Get the plugin code](./usage.md#get-the-plugin-code)
    * [Install the plugin](./usage.md#install-the-plugin)
    * [Set up a local.py](./usage.md#set-up-a-local.py)
* [Running a cup as server admin](./usage.md#running-a-cup-as-server-admin)
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
+-- apps
|   +-- cup_manager
|   |   +-- cup_manager
|   |   +-- settings
|   |   +-- .gitignore
|   |   +-- readme.md
|   |   +-- usage.md
+-- env
+-- settings
|   +-- __init__.py
|   +-- apps.py
|   +-- base.py
+-- manage.py
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
tbd

# Plugin operations as a player
tbd
