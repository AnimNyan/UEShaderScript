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
            
        nodes_to_dict(self,context, mytool)
        
        return {"FINISHED"}


def nodes_to_dict(tree):
    """ Actually, we construct and return a List """
    if tree is not None:
        nodes = tree.nodes
    else:
        nodes = []
    nodes_list = []
    for node in nodes:
        #bl_idname e.g. ShaderNodeTexImage
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
        inputs = []
        for input in node.inputs:
            input_dict = socket_to_dict_input(input)
            inputs.append(input_dict)
        if node.bl_idname != "CompositorNodeOutputFile":
            node_dict["inputs"] = inputs
        else:
            node_dict["inputs"] = []
        outputs = []
        for output in node.outputs:
            output_dict = socket_to_dict_output(output)
            outputs.append(output_dict)
        node_dict["outputs"] = outputs
        # Special handling ShaderNodeGroup
        if node.bl_idname == "ShaderNodeGroup":
            node_dict["node_tree"] = nodes_to_dict_handle_shader_node_group(
                node)
        if node.bl_idname == "CompositorNodeGroup":
            node_dict["node_tree"] = nodes_to_dict_handle_compositor_node_group(
                node)
        if node.bl_idname == "CompositorNodeOutputFile":
            # We just handle OutputFile->file_slots, does not handle layer_slots (Waiting for bugs)
            node_dict["file_slots"] = nodes_to_dict_handle_compositor_node_output_file(
                node)
            # We treat all file slot's file format as the same of OutputFile->format->file_format
            node_dict["file_format"] = node.format.file_format
        nodes_list.append(node_dict)
    links_list = links_to_list(tree)
    return (nodes_list, links_list)


def dict_to_nodes(nodes_list, tree):
    nodes = tree.nodes
    ret_nodes = []
    for node in nodes_list:
        # Fixed: in input_dict_to_socket_value
        # input.default_value[0] = value[0]
        # TypeError: ‘float’ object does not support item assignment
        if node["node_name"] in NOT_NEEDED_NODE_TYPES:
            new_node = nodes.new(type=node["node_name"])
            ret_nodes.append(new_node)
            new_node.width = node["width"]
            new_node.width_hidden = node["width_hidden"]
            new_node.height = node["height"]
            if node["parent"] != "None":
                parent = nodes[node["parent"]]
                new_node.parent = parent
            new_node.location.x = node["x"]
            new_node.location.y = node["y"]
            continue
        new_node = nodes.new(type=node["node_name"])
        ret_nodes.append(new_node)
        new_node.width = node["width"]
        new_node.width_hidden = node["width_hidden"]
        new_node.height = node["height"]
        if node["parent"] != "None":
            parent = nodes[node["parent"]]
            new_node.parent = parent
        new_node.location.x = node["x"]
        new_node.location.y = node["y"]
        # Special handlling ShaderNodeGroup
        if node["node_name"] == "ShaderNodeGroup":
            dict_to_nodes_handle_shader_node_group(new_node, node)
        if node["node_name"] == "CompositorNodeGroup":
            dict_to_nodes_handle_compositor_node_group(new_node, node)
        if node["node_name"] == "CompositorNodeOutputFile":
            dict_to_nodes_handle_compositor_node_output_file(new_node, node)
            new_node.format.file_format = node["file_format"]
        if node["node_name"] in NOT_TO_HANDLE_ATTRS_NODES:
            continue
        for attr_dict in node["attrs"]:
            dict_to_attr(new_node, attr_dict)
        # Repeat one more time to make sure UI updates right
        for attr_dict in node["attrs"]:
            dict_to_attr(new_node, attr_dict, repeated=True)
        inputs = new_node.inputs
        for index, input_dict in enumerate(node["inputs"]):
            # Get the right input socket by name
            input = get_input_by_name(inputs, input_dict["name"], index)
            if input is not None:
                input_dict_to_socket_value(input, input_dict)
            #input_dict_to_socket_value(inputs[index], input_dict)
        outputs = new_node.outputs
        for index, output_dict in enumerate(node["outputs"]):
            # Get the right ouput socket by name
            output = get_output_by_name(outputs, output_dict["name"], index)
            if output is not None:
                output_dict_to_socket_value(output, output_dict)
            #output_dict_to_socket_value(outputs[index], output_dict)
    return ret_nodes

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