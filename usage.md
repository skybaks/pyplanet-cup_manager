# Cup Manager Setup and Usage

**Contents**
* [Setting up with a dedicated server](./usage.md#setting-up-with-a-dedicated-server)
    * [Set up Pyplanet](./usage.md#set-up-pyplanet)
    * [Get the plugin code](./usage.md#get-the-plugin-code)
    * [Install the plugin](./usage.md#install-the-plugin)
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

Place the downloaded or cloned plugin code inside this apps folder. If you downloaded a zip archive then unzip it to here. The path where you placed the plugin code is important. It doesnt have to match this guide exactly but unless you are
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

# Running a cup as server admin
tbd

# Plugin operations as a player
tbd
