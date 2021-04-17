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

import bpy

#define all user input properties
class AddProperties(bpy.types.PropertyGroup):
    cust_map_name: bpy.props.StringProperty(name="Name of Shader Map", description="Name of your custom shader map")
    bc_suffix: bpy.props.StringProperty(name="Diffuse Suffix", description="Suffix of Diffuse", default="_BC")
    bc_suffix_node: bpy.props.StringProperty(name="Diffuse Node Name", description="Diffuse image texture node name", default="Diffuse Node")
    orm_suffix: bpy.props.StringProperty(name="Packed RGB ARM Suffix", description="Suffix of Packed RGB (AO, Rough, Metallic)", default="_ORM")
    orm_suffix_node: bpy.props.StringProperty(name="Packed RGB Node Name", description="Packed RGB image texture node name", default="Packed RGB Node")
    n_suffix: bpy.props.StringProperty(name="Normal Map Suffix", description="Suffix of Normal Map", default="_N")
    n_suffix_node: bpy.props.StringProperty(name="Normal Map Node Name", description="Normal Map image texture node name", default="Normal Map Node")
    m_suffix: bpy.props.StringProperty(name="Alpha Map Suffix", description="Suffix of Alpha (Transparency) Map", default="_M")
    m_suffix_node: bpy.props.StringProperty(name="Alpha Map Node Name", description="Alpha Map image texture node name", default="Transparency Map Node")
    bde_suffix: bpy.props.StringProperty(name="Emissions Map Suffix", description="Suffix of Emissions Map", default="_BDE")
    bde_suffix_node: bpy.props.StringProperty(name="Emissions Map Node Name", description="Emissions Map image texture node name", default="Emissions Map Node")
    is_add_img_textures: bpy.props.BoolProperty(name="Load Image Textures to Shader Map", default= True)


#code for drawing main panel in the 3D View
class AddUEShaderScript_PT_main_panel(bpy.types.Panel):
    bl_label = "Add UE Shaders"
    bl_idname = "AddUEShaderScript_PT_main_panel"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Add DBD Shaders"
    
    def draw(self, context):
        layout = self.layout
        
        #store active/selected scene to variable
        scene = context.scene
        
        #allow access to user inputted properties through pointer
        #to properties
        mytool = scene.my_tool
        
        layout.label(text = "Add a Custom Shader Map")
        
        layout.prop(mytool, "cust_map_name")
        
        layout.prop(mytool, "is_add_img_textures")
        if (mytool.is_add_img_textures == True):
            box = layout.box()
            box.label(text = "Image Texture Suffixes and Node Names")
            box.label(text = "(leave suffix + node name empty if you do NOT want to load the specific image texture)")
            box.label(text = "Node Names can be found/changed by selecting an image texture node > Press n > Item > Name")
            box.prop(mytool, "bc_suffix")
            box.prop(mytool, "bc_suffix_node")
            box.prop(mytool, "orm_suffix")
            box.prop(mytool, "orm_suffix_node")
            box.prop(mytool, "n_suffix")
            box.prop(mytool, "n_suffix_node")
            box.prop(mytool, "m_suffix")
            box.prop(mytool, "m_suffix_node")
            box.prop(mytool, "bde_suffix")
            box.prop(mytool, "bde_suffix_node")
        
        layout.operator("AddUEShaderScript.saveshadermap_operator")
        layout.operator("AddUEShaderScript.loadimagetexture_operator")
      
class AddUEShaderScript_OT_save_shader_map(bpy.types.Operator):
    #default name is for Roman Noodles label
    #text is changed for other Shader Map Types
    bl_label = "Save Shader Map"
    bl_idname = "AddUEShaderScript.saveshadermap_operator"
    def execute(self, context):
        scene = context.scene 
        #allow access to user inputted properties through pointer
        #to properties
        mytool = scene.my_tool
        
        if(mytool.is_add_img_textures == True):
            print("hey")
            
        saveNodes(self,context, mytool)
        
        return {"FINISHED"}

def saveNodes(self, context, mytool):
    nodes = tree.nodes
    for node in nodes:
        node_dict = {"node_name": node.bl_idname}
        node_dict["x"] = node.location.x
        node_dict["y"] = node.location.y
        node_dict["width"] = node.width
        node_dict["width_hidden"] = node.width_hidden
        node_dict["height"] = node.height

        parent = node.parent
        if parent == None:
            node_dict["parent"] = "None"
        else:
            parent_index = get_node_index(nodes, parent)
            node_dict["parent"] = parent_index
        attrs = dir(node)
        attrs_list = []
        for attr in attrs:
            attr_dict = attr_to_dict(node, attr)
            if attr_dict["type_name"] == "NoneType" \
                    or attr_dict["type_name"] == "Not Handle Type":
                continue
            attrs_list.append(attr_dict)
        node_dict["attrs"] = attrs_list

class AddUEShaderScript_OT_load_image_texture(bpy.types.Operator):
    #default name is for Roman Noodles label
    #text is changed for other Shader Map Types
    bl_label = "Load Image Texture"
    bl_idname = "AddUEShaderScript.loadimagetexture_operator"
    def execute(self, context):
        scene = context.scene 
        #allow access to user inputted properties through pointer
        #to properties
        mytool = scene.my_tool
        
        if(mytool.is_add_img_textures == True):
            node_to_load = bpy.context.active_object.active_material.node_tree.nodes["Diffuse Node"]
            node_to_load.image = bpy.data.images.load("C:\Seabrook\Dwight Recolor\Game\Characters\Campers\Dwight\Textures\Outfit01\T_DFHair01_BC.tga")
            
        
        return {"FINISHED"}


classes = [AddProperties, AddUEShaderScript_PT_main_panel, AddUEShaderScript_OT_save_shader_map, AddUEShaderScript_OT_load_image_texture]
 
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
        #register my_tool as a type which has all
        #the user input properties from the properties class 
        bpy.types.Scene.my_tool = bpy.props.PointerProperty(type = AddProperties)
 
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
        
        #unregister my_tool as a type
        del bpy.types.Scene.my_tool
 
 
if __name__ == "__main__":
    register()