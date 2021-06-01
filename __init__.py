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
    "version": (1, 0, 9),
    "blender": (2, 92, 0),
    "location": "3D View > Properties > Load UE Shaders + Shader Editor > Properties > Save UE Shaders",
    "description": "Adds the ability to save and load shader maps for 3d Meshes exported from Unreal Engine games and adds default preset shader maps for your convenience ",
    "warning": "",
    "wiki_url": "https://github.com/AnimNyan/UEShaderScript/wiki",
    "category": "Material",
    "tracker_url": "https://github.com/AnimNyan/UEShaderScript"
}

"""
Version': '1.0.9' written by Anime Nyan

Adds two panels one in the Shader Editor View to save different preset shader maps and one in the 3D View to load shader maps.
"""


def register():
    save_shader_map.register()
    load_shader_map.register()
    #import_current_or_default_json will not work when blender just
    #starts the reason why is because you cannot get add on preferences
    #when blender starts
    #so this is only used when the add on is being re enabled in the addons panel
    try:
        save_shader_map.import_current_or_default_json()
    except Exception as e:
        print("import_current_or_default_json() exception because blender is not ready yet. :", e)

def unregister():
    save_shader_map.unregister()
    load_shader_map.unregister()

print("(*) UE Shader Script add-on loaded")
