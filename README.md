# UEShaderScript

## Discord
First things first, I have a discord server for questions, support and bugs find me here: https://discord.gg/rkkWSH2EMz

## Credits
Thank you to Aaron Elkins who designed Node Kit, a Blender plugin under the GPL Licence which was several years in the making. 
UEShaderScript copies a huge amount of code from Node Kit and I want to thank Aaron Elkins for his kindness 
for giving me permission to release UEShaderscript. Please have a look at his plugin and his work [here](https://blendermarket.com/products/node-kit).

I also want to extend my overwhelming gratitude towards Roman Noodles, YanimaDBD, Pit Princess and Frutto for their fantastic work in designing the presets that come with this plugin, but also for their guidance and support which without I would not have been able to finish this plugin!

## Permissions
UEShaderScript is under the GPL Licence that means you have permission to use part or the whole of this plugin for free or commercial purposes free of charge.
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

## Video Demo and Tutorial for UEShaderScript
[![UEShaderScript Dead By Daylight Tutorial](https://i.ytimg.com/vi/8bptSUSiyB8/maxresdefault.jpg)](https://www.youtube.com/watch?v=8bptSUSiyB8 "UEShaderScript Dead By Daylight Tutorial")
[![UEShaderScript v1.0.3 demo](https://i.ytimg.com/vi/sGY5rCJW5ZQ/maxresdefault.jpg)](https://www.youtube.com/watch?v=sGY5rCJW5ZQ&lc=UgyelgrzDH2_XMyxoBB4AaABAg "UEShaderScript v1.0.3 demo")

# Installation
### To install UEShaderScript:
1. Go here: https://github.com/AnimNyan/UEShaderScript/releases Right click on "UEShaderScript_v.X.X.X.zip" > "Save Link As" and do NOT unzip it. 
2. Open Blender and click Edit > Preferences > Add-Ons > Install > in the file explorer find "UEShaderScript_v.X.X.X.zip" and select it.
3. In the Add-Ons search, search for UE Shader Maps and enable the Add On to complete the installation.

### Prerequisite software
- UModel/UE Viewer: https://www.gildor.org/en/projects/umodel (Download and unzip)
- Befzz's psk importer: https://github.com/Befzz/blender3d_import_psk_psa (Right Click on the Stable (branch latest) 280 direct link > Save Link As)
- Pak files of an Unreal Engine Game you are trying to unpack (for Steam Games select the game in your library > press the cog icon > 
browse local files > a file explorer should have opened with your game folder > look for a Content Folder with pak files in folders)

# Usage
## Using Prerequisite Software to setup for UEShaderScript
### Installing Prerequisite Software
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
in step 4. of Installing Prequisite Software by pressing Ctrl + v 
OR
if you copied the PAK into the UModel folder as in step 2. of Installing Prerequisite software press the "..." button > 
go into the PAK folder in the file explorer > press Select Folder.
4. Press OK to open the PAK files in UModel.
5. Now once you're in UModel you want to find the folder for the character you are interested in. 
For Dead By Daylight this will be in /Game/Characters/Campers for survivors and /Game/Characters/Slashers for the Killers.
For this example I will try and find the Kate model from Dead By Daylight in the /Game/Characters/Campers/Guam/Models folder.
7. There are two ways of exporting meshes from UModel either Tag and Export Meshes or Export Folder Content.

### Tag and Export Meshes from UModel
1. So in the left hand folder tree you want to right click on the /Game/Characters/Campers/Guam/Models folder > Open Folder Content.
2. Make sure to Enable the setting Navigate > Include Meshes to see only meshes and not materials,
Press Ctrl + g to disable the glow effect, press PgUp and PgDown to preview the next mesh, press Ctrl + t to tag the meshes that you want.
3. Once you have tagged all the meshes you want, press Ctrl + x to export the current object, choose an export folder
I suggest creating a new folder and exporting into there as it is cleaner.

### Export Folder Content from UModel
1. So in the left hand folder tree you want to right click on the /Game/Characters/Campers/Guam/Models folder > Export Folder Content
to export all meshes in the Models folder.
2. Choose an export folder, I suggest creating a new folder and exporting into there as it is cleaner.

## Loading Preset Shader Maps
1. Go to the 3D View and press n > you should see a panel called "UE Shaders" > click on UE Shaders to open the panel.
2. You may need to hover your mouse over the left edge of the panel > click and drag to the left to expand the window to see the text.
3. At the very top of the of the Panel you should see a list of Preset Shader Maps > click on one of these Presets to highlight and select it.
4. Now scroll down to the bottom of the panel and you should see two boxes one labelled "ADD SHADER MAP TO MULTIPLE MATERIALS (MULTIPLE MATERIALS)",
this is for adding a shader map to a single material. The other box should be labelled "ADD SHADER MAP TO ALL MATERIALS ON SELECTED MESHES (ALL MATERIALS)"

### Bulk Loading a Preset for all materials on all selected meshes
So to load a single preset for all materials on all selected objects we want to look at the box labelled 
"ADD SHADER MAP TO ALL MATERIALS ON SELECTED MESHES (ALL MATERIALS)"
This is for if you want to load your preset shader map to all selected meshes.
The reason why we have to select the Materials Folder and Exported Game Folder is if you are loading image textures
dynamically, we need to know where materials info/props.txt files are and where the image textures are located.
1. Select all the Meshes you want to load the shader map preset to by holding the Shift key and pressing Left Mouse Button. 
2. Press on the folder icon for the Exported Game Folder input this is a required field as shown by the (!) before the field name and in the file
explorer navigate to the folder you have exported the meshes to. From here you should be able to find a Game folder, go inside
the game folder and then press Accept.
3. Press on the folder icon for the Materials Folder input. This is an optional field but will speed up the rate at which shader map presets
are loaded. So in this case what you want to do is find the character folder in this case Guam and then there should be a Materials folder.
Go inside the Materials folder and press Accept.
4. Press Add Shader Maps to ALL Selected Meshes.

### Loading a Preset for multiple materials on the active mesh
So this is to load the preset onto multiple materials on the active (last selected) mesh. 
This is useful when you want to load different presets on different materials on one mesh.
1. Select the single mesh you want to load presets to.
2. Press on the folder icon for the Exported Game Folder input this is a required field as shown by the (!) before the field name and in the file
explorer navigate to the folder you have exported the meshes to. From here you should be able to find a Game folder, go inside
the game folder and then press Accept.
3. Press on the folder icon for the Materials Folder input. This is an optional field but will speed up the rate at which shader map presets
are loaded. So in this case what you want to do is find the character folder in this case Guam and then there should be a Materials folder.
Go inside the Materials folder and press Accept.
4. Now in the Indexes of Material Slots to be loaded tab delete everything that is there. So click on the materials tab,
should be a Material ball icon and check what materials you would like to load to. count from the top downwards starting from 
Index 0. So if I wanted to load the shader map preset to the first and third materials, in the box I will type "0 2" without 
the double quotes. As you can see multiple materials are separated by a single space and it starts from 0 so material slot number 1 is 0.
5. Once you have entered the indexes of the material slots you want to load your preset to press Add Shader Maps to Multiple Materials.

### Loading a Preset for one selected material
Most of the time we don't want to use this, because it only adds a preset to one selected material. 
This is just in case we have one material which should have a different shader map preset.
So to load a single preset for one material we want to look at the box labelled "ADD SHADER MAP TO SELECTED MATERIAL (ONE MATERIAL)"
1. 

#### Disclaimer for Pit Princess's presets from Pit Princess
Using custom per-light ray denoising in compositing will break because my "colour" of objects can be outside the sdr range, because blender technically only has diffuse and specular light rays
it's easily fixable by denoising in hdr range. For example, skin can be seen to be "glowing" in the direct colour pass.

#### Using Pit Princess's presets
For the cloth shader:
* Softness (-1) is meant for soft fabrics like cotton / Hardness (1) is meant for hard stuff like leather or rubber
* Velour (-1) is for stuff like fur, carpets, velvet, etc, and Fuzziness (+1) is for tight fine fabrics like silk or a thin-sheet adidas-tracksuit
* Translucency is meant for anything that's supposed to let light through it such as thin t-shirts. Less light going through (0) and more light going through (1) 

The sliders have been designed so that mixing and matching values yields plausible results, so it's perfectly okay to experiment.
If the slider accepts an input combination, it works.

### Advanced Options Loading Preset Shader Maps

## Saving Preset Shader Maps
### Rules when Saving presets
1. The X Node Name input box refers to an image texture node on your current node tree.
You can think of the X Node Name input box marking an image texture node that we wish to dynamically load with an image texture.

#### How do we mark an image texture node you ask? 
So we make sure what is inside the X Node Name is the same as the image texture node name. e.g. inside the Diffuse Node Name box: "Diffuse Node" 
so we select an image texture node > press n to open up Properties > Items > Now change the Node Name: to "Diffuse Node". And you're done!

2. The X Suffix input box refers to the name of the image textures. So you'll have to check 
what textures are in charge of diffuse and what suffix they end with in the file name. e.g. 
for Dead By Daylight the diffuse textures are named "_BC", "_BC_01", ""_BC_02", "_BC_03" and "_BC_04". 
So we put each different suffix in the Diffuse Suffix input box separated by spaces like so: "_BC _BC_01 _BC_02 _BC_03 _BC_04"

3. It is important that you rename every Node Group you wish to save as a preset, do NOT leave it as the default name "NodeGroup",
please rename it to something relevant like "EmissiveMapNodeGroup" because by default the option to "Reuse Node Groups with Same Name" is enabled.
This means if you already had a Node Group named "NodeGroup" in your blender file before loading a shader map, the loaded shader map would 
reuse the Node Group with the same name "Node Group". Renaming it to something relevant like "EmissiveMapNodeGroup" before Saving a shader map preset
usually prevents reusing the wrong node group.

4. If you wish to make use of the "Delete Unused Image Texture Nodes AND Related Nodes" option which is disabled by default because it slows down
adding shader maps, change the Node Name: of related nodes to the image texture node to "[Node Name][number]">, for example: "Diffuse Node2", 
"Diffuse Node3", ... . Now when an image texture node is deleted because it is unused and "Delete Unused Image Texture Nodes AND Related Nodes" 
is enabled it will delete these extra nodes labelled "Diffuse Node2", "Diffuse Node3", ... .
