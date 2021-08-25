# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

# by Anime Nyan

from . import save_shader_map
from . import load_shader_map

bl_info = {
    "name": "Load Save UE Shader Map Setups",
    "author": "Anime Nyan",
    "version": (1, 1, 9),
    "blender": (2, 93, 0),
    "location": "3D View > Properties > Load UE Shaders + Shader Editor > Properties > Save UE Shaders",
    "description": "Adds the ability to save and load shader maps and textures for Meshes and adds default preset shader maps",
    "warning": "",
    "wiki_url": "https://github.com/AnimNyan/UEShaderScript",
    "category": "Material",
    "tracker_url": "https://github.com/AnimNyan/UEShaderScript"
}

"""
Written by Anime Nyan

Adds two panels one in the Shader Editor View to save different preset shader maps and textures and one in the 3D View to load shader maps and textures.
"""


def register():
    save_shader_map.register()
    load_shader_map.register()

    #import_current_or_default_json will cause an error when blender first starts
    #this is because you cannot run the function bpy.ops.wm.save_userpref() inside save_pref()
    #as blender cannot allow
    #to access bpy.ops when file starts when blender just starts
    #however, this will still load the json file to the current add on preferences for the current file
    #it will just not load them to the default add on preferences until the user has made a change in the Save UE Shaders Panel
    #then blender will allow access to bpy.ops and the changes will save to the default add on preferences
    #for all files

    #import_current_or_default_json here is also used when the add on 
    #is being re enabled in the Edit > Preferences > Add Ons panel
    #and in this case you have access to bpy.ops because blender is already open
    #therefore, changes will happen to the current preferences and default preferences
    try:
        save_shader_map.import_current_or_default_json()
    except Exception as e:
        print("import_current_or_default_json() exception because blender is not ready yet. :", e)
    
    #you cannot run the function bpy.ops.wm.save_userpref() inside save_pref()
    #as blender cannot allow
    #to access bpy.ops when file starts when blender just starts
    #however, this will still reset and update the json file to the current add on preferences for the current file
    #it will just not update the presets to the default add on preferences until the user has made a change in the Save UE Shaders Panel
    #then blender will allow access to bpy.ops and the changes will save to the default add on preferences
    #for all files
    try:
        save_shader_map.reset_and_update_default_presets()
    except Exception as e:
        print("reset_and_update_default_presets() exception because blender is not ready yet. :", e)

def unregister():
    save_shader_map.unregister()
    load_shader_map.unregister()

print("(*) UE Shader Script add-on loaded")
