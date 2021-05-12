# ##### BEGIN MIT LICENSE BLOCK #####
# Copyright © 2021 Anime Nyan

# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and 
# associated documentation files (the “Software”), to deal in the Software without restriction, 
# including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, 
# and/or sell copies of the Software, and to permit persons 
# to whom the Software is furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, 
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, 
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, 
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ##### END MIT LICENSE BLOCK #####

# by Anime Nyan

from . import save_shader_map
from . import load_shader_map
import time
import bpy

bl_info = {
    "name": "UE Shader Map Setups",
    "author": "Anime Nyan",
    "version": (1, 0, 5),
    "blender": (2, 92, 0),
    "location": "3D View > Properties > UE Shaders + Shader Editor > Properties > Save UE Shaders",
    "description": "Adds the ability to save shader maps for 3d Meshes exported from Unreal Engine games and adds default preset shader maps for your convenience ",
    "warning": "",
    "wiki_url": "https://github.com/AnimNyan/UEShaderScript/wiki",
    "category": "Material",
    "tracker_url": "https://github.com/AnimNyan/UEShaderScript"
}

"""
Version': '1.0.5' written by Anime Nyan

Adds two panels one in the Shader Editor View to save different preset shader maps and one in the 3D View to load shader maps.
"""


def register():
    save_shader_map.register()
    load_shader_map.register()
    try:
        save_shader_map.import_current_or_default_json()
    except Exception as e:
        print("import_current_or_default_json() exception because blender is not ready yet. :", e)

def unregister():
    save_shader_map.unregister()
    load_shader_map.unregister()

print("(*) UE Shader Script add-on loaded")
