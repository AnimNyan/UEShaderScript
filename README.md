# UEShaderScript

## Discord
First things first, I have a discord server for questions, support and bugs find me here: https://discord.gg/rkkWSH2EMz

## Credits
A huge thank you to Aaron Elkins who designed Node Kit, a Blender plugin under the GPL Licence which was several years in the making. 
UEShaderScript copies a huge amount of code from Node Kit and I want to thank Aaron Elkins for his kindness 
for giving me permission to release UEShaderscript. Please have a look at his plugin and his work here: https://blendermarket.com/products/node-kit

## Permissions
UEShaderScript is under the MIT Licence that means you have permission to use part or the whole of this plugin for free or commercial purposes free of charge.
This add on is completely free what I want is for the most people to benefit from this and that's enough to make me smile. 
I promise continued support and updates to this the add on for free!

## What does UEShaderScript do?
UEShaderScript is a free Blender Plugin designed to be used with UModel: https://www.gildor.org/en/projects/umodel#files and Befzz's psk/psa importer: https://github.com/Befzz/blender3d_import_psk_psa

The plugin allows for one click bulk texturing for all selected meshes and is built for all 3d assets exported from Unreal Engine. 

UEShaderScript does three things:
1. Comes with default shader map presets for Dead By Daylight. 
We are still looking for shader maps to add to the default presets for other games! 
Again find me on my discord here: https://discord.gg/rkkWSH2EMz to send me screenshots of shader maps you want to be included in the default presets!

2. Adds the ability to save shader maps and mark which image texture nodes should load an image and dynamically load image textures to them.

3. Adds the ability to load shader maps and their respective image textures based on a props.txt file exported from UModel: https://www.gildor.org/en/projects/umodel#files

## Video Demo and Tutorial for UEShaderScript (Tutorial to be added)
[![UEShaderScript v1.0.3 demo](https://i.ytimg.com/vi/sGY5rCJW5ZQ/maxresdefault.jpg)](https://www.youtube.com/watch?v=sGY5rCJW5ZQ&lc=UgyelgrzDH2_XMyxoBB4AaABAg "UEShaderScript v1.0.3 demo")

## Installation
### To install:
1. Download the "UEShaderScript_v.X.X.X.zip" file do NOT unzip it. 
2. Open Blender and click Edit > Preferences > Add-Ons > Install > in the file explorer find "UEShaderScript_v.X.X.X.zip" and select it.
3. In the Add-Ons search, search for UE Shader Maps and enable the Add On to complete the installation.

### Prerequisite software
- UModel/UE Viewer: https://www.gildor.org/en/projects/umodel (Download and unzip)
- Befzz's psk importer: https://github.com/Befzz/blender3d_import_psk_psa (Right Click on the Stable (branch latest) 280 direct link > Save Link As)
- Pak files of an Unreal Engine Game you are trying to unpack (for Steam Games select the game in your library > press the cog icon > 
browse local files > a file explorer should have opened with your game folder > look for a Content Folder with pak files in folders)

## Usage
## Using Prerequisite Software to setup for UEShaderScript
### Installing Prequisite Software
1. Download the latest version of [UModel/UE Viewer](https://www.gildor.org/en/projects/umodel#files) for your operating system, 
right click on the umodel zip file > Extract All which will create an unzipped folder.
2. We have to find the path to the Unreal Engine Game For Steam Games select the game in your library > press the cog icon >
browse local files > a file explorer should have opened with your game folder > look for a Content Folder with pak files in folders
3. I suggest if you have the space making a copy of the Pak folder you found in step 2 into the unzipped folder of UModel. 
4. Once you are in the directory where the PAK files are > click on an empty space in the address bar of the file 
explorer to select the path > press Ctrl + c to copy the path to the PAK files we will need this later.
5. Next go to [Befzz's psk importer](https://github.com/Befzz/blender3d_import_psk_psa), 
and right click on the Stable (branch latest) 280 direct link > Save Link As and save it somewhere.
6. To install Befzz's psk importer, open a Blender file > click Edit > Preferences > Add-Ons > Install > 
in the Blender file explorer find the file "io_import_scene_unreal_psa_psk_280.py" you downloaded and select and install it.

### Using UModel
1. In the unzipped UModel open the "umodel.exe" file this will open up a window, now you'll 
need to know what settings to use for your game which you'll likely find on the Gildor Forums for UModel: https://www.gildor.org/smf/ . 
2. For Dead By Daylight check the box labelled override game detection and as of DBD version 4.7.0 click the 
1st Dropdown for "Unreal Engine 4" and second for "Unreal Engine 4.25", it will be different for other games so ask around on the Gildor
Forums or search up what version of Unreal Engine your game is using.
3. In the "Path to Game Files:" input box you want to paste the path to the PAK files copied 
in step 4. of Installing Prequisite Software by pressing Ctrl + v. 
OR
If you copied the PAK into the UModel folder as in step 2. of Installing Prerequisite software press the "..." button > 
go into the PAK folder in the file explorer > press Select Folder.
4. Press OK to open the PAK files in UModel.
5. Now once you're in UModel you want to find the folder for the character you are interested in. 
For Dead By Daylight this will be in /Game/Characters/Campers for survivors and /Game/Characters/Slashers for the Killers.
For this example I will try and find the Kate model from Dead By Daylight in the /Game/Characters/Campers/Guam/Models folder.
6.
 
## Loading Preset Shader Maps
1. Go to the 3D View and press n > you should see a panel called "UE Shaders" > click on UE Shaders to open the panel.
2. You may need to hover your mouse over the left edge of the panel > click and drag to the left to expand the window to see the text.
3. At the very top of the of the Panel you should see a list of Preset Shader Maps > click on one of these Presets to highlight and select it.
4. Now scroll down to the bottom of the panel and you should see two boxes one labelled "ADD SHADER MAP TO SELECTED MATERIAL (ONE MATERIAL)",
this is for adding a shader map to a single material. The other box should be labelled "ADD SHADER MAP TO ALL MATERIALS ON SELECTED MESHES (ALL MATERIALS)"

### Bulk Loading a Preset for all materials on all selected meshes
So to load a single preset for all materials on all selected objects we want to look at the box labelled 
"ADD SHADER MAP TO ALL MATERIALS ON SELECTED MESHES (ALL MATERIALS)"

### Loading a Preset for one selected material
Most of the time we don't want to use this, because it only adds a preset to one selected material. 
This is just in case we have one material which should have a different shader map preset.
So to load a single preset for one material we want to look at the box labelled "ADD SHADER MAP TO SELECTED MATERIAL (ONE MATERIAL)"
1. 

### Advanced Options Loading Preset Shader Maps

## Saving Preset Shader Maps
### Rules when Saving presets
1. The X Node Name input box refers to an image texture node on your current node tree.
You can think of the X Node Name marking an image texture node that we wish to dynamically load with an image texture.

#### How do we mark an image texture node you ask? 
So we make sure what is inside the X Node Name is the same as the image texture node name. e.g. inside the Diffuse Node Name box: "Diffuse Node" 
so we select an image texture node > press n to open up Properties > Items > Now change the Node Name: to "Diffuse Node". And you're done!

2. The X Suffix input box refers to what is of the texture inside the files. So you'll have to check what textures are in charge of diffuse. e.g. 
for Dead By Daylight the diffuse textures are named "_BC", "_BC_01", ""_BC_02", "_BC_03" and "_BC_04". So we put each of those in the input box separated by spaces
like so: "_BC _BC_01 _BC_02 _BC_03 _BC_04"
