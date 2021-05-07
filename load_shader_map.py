#import all libraries including re needed for regex matching
#import Path library to search recursively for files
import bpy, re
import glob
from pathlib import Path

import time

import os

#import with relative imports
#import classes 
from .save_shader_map import SHADER_PRESETS_UL_items, ShowMessageOperator
#import functions
from .save_shader_map import get_preferences, get_selected_folder_presets, json_to_nodes_dict, log


from mathutils import (Vector, Euler, Color)

#define globals
SHADER_EDITOR = "ShaderNodeTree"
COMPOSITOR_EDITOR = "CompositorNodeTree"
ANIMATION_NODE_EDITOR = "an_AnimationNodeTree"

# Special handled node types
NOT_NEEDED_NODE_TYPES = [
    "NodeReroute"
]

# Not to handle atts for these node types
NOT_TO_HANDLE_ATTRS_NODES = [
    # Need to handle CompositorNodeImage
    # "CompositorNodeImage"
]



#define all user input properties
class PathProperties(bpy.types.PropertyGroup):
    props_txt_path: bpy.props.StringProperty(name="Select PropsTxt File*", description="Select a props.txt file", subtype="FILE_PATH")
    skin_map_path: bpy.props.StringProperty(name="Select Skin Map File (Roman Noodles Skin Only)", description="Select a skin map image file", subtype="FILE_PATH")
    material_folder_path: bpy.props.StringProperty(name="Select Materials Folder", description="Select a Materials folder", subtype="DIR_PATH")
    export_folder_path: bpy.props.StringProperty(name="Select Exported Game Folder*", description="Select a Game folder", subtype="DIR_PATH")
    is_replace_nodes: bpy.props.BoolProperty(name="Replace Existing Shader Maps", default= True)
   

    texture_file_type_enum: bpy.props.EnumProperty(
        name = "Texture File Type",
        description = "Dropdown List of all the texture file types",
        items = 
        [
            (".tga" , ".tga", ""),
            (".png" , ".png", "")
        ]
        
    )
    clipping_method_enum: bpy.props.EnumProperty(
        name = "Clipping Method for Transparency",
        description = "Dropdown List of all the texture file types",
        items = 
        [
            ("CLIP" , "Alpha Clip", ""),
            ("HASHED" , "Alpha Hashed", "")
        ]
        
    )
    is_normal_non_colour: bpy.props.BoolProperty(name="Normal Map Textures Non Colour", default= True)
    is_m_non_colour: bpy.props.BoolProperty(name="Transparency Map Textures Non Colour", default= True)
    is_orm_non_colour: bpy.props.BoolProperty(name="Packed ARM Textures Non Colour (True for Roman Noodles)", default= False)

    is_add_img_textures: bpy.props.BoolProperty(name="Add Image Textures", default= True)
    is_delete_unused_img_texture_nodes: bpy.props.BoolProperty(name="Delete Unused Image Texture Nodes", default= True)
    is_delete_unused_related_nodes: bpy.props.BoolProperty(name="Delete Unused Image AND Related Texture Nodes (Slows down adding shaders)", default= False)

    is_change_principle_bsdf_emission_strength: bpy.props.BoolProperty(name="Change Principled BSDF Strength", default= True)
    principled_bsdf_emission_strength_float: bpy.props.FloatProperty(name="Principled BSDF Emission Strength", default = 5)

    #options to allow reuse of node groups and image textures
    is_reuse_node_group_with_same_name: bpy.props.BoolProperty(name="Reuse Node Group With Same Name", default= True)
    is_reuse_img_texture_with_same_name: bpy.props.BoolProperty(name="Reuse Image Textures With Same Name", default= True)

    # is_material_skin: bpy.props.BoolProperty(name="Add Skin Related Nodes", default= False)
    # is_add_height_map: bpy.props.BoolProperty(name="Add Height Map Skin Texture", default= False)


#code for drawing main panel in the 3D View
class LOADUESHADERSCRIPT_PT_main_panel(bpy.types.Panel):
    bl_label = "Load UE Shaders"
    bl_idname = "LOADUESHADERSCRIPT_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "UE Shaders"
    
    def draw(self, context):
        layout = self.layout
        
        #store active/selected scene to variable
        scene = context.scene
        #allow access to user inputted properties through pointer
        #to properties
        pathtool = scene.path_tool

        #set isOverridePackage to override __package__ variable as it does
        #not work for imported functions
        isOverridePackage = True
        preferences = get_preferences(isOverridePackage)

        #make folder section
        box = layout.box()
        row = box.row()
        row.label(text="Folders")
        row = box.row()
        left = row.column()
        left.alignment = "RIGHT"
        left.prop(preferences, 'folders', expand=False)


        selected_folders_presets = get_selected_folder_presets(isOverridePackage)

        #create the list of current presets
        layout.template_list("SHADER_PRESETS_UL_items", "", selected_folders_presets,
                               "presets", selected_folders_presets, "preset_index", rows=5)

        #option to replace or keep existing nodes in materials
        layout.prop(pathtool, "is_replace_nodes")

        #option to delete image texture nodes which have not had a texture
        #loaded into them
        layout.prop(pathtool, "is_delete_unused_img_texture_nodes")
        #only show this option if delete unused_img_texture_nodes is checked
        if(pathtool.is_delete_unused_img_texture_nodes):
            layout.prop(pathtool, "is_delete_unused_related_nodes")

        layout.prop(pathtool, "texture_file_type_enum")
        layout.prop(pathtool, "clipping_method_enum")

        layout.prop(pathtool, "is_reuse_node_group_with_same_name")
        layout.prop(pathtool, "is_reuse_img_texture_with_same_name")

        layout.prop(pathtool, "is_normal_non_colour")
        layout.prop(pathtool, "is_m_non_colour")
        layout.prop(pathtool, "is_orm_non_colour")
        
        layout.prop(pathtool, "is_change_principle_bsdf_emission_strength")

        if(pathtool.is_change_principle_bsdf_emission_strength):
            layout.prop(pathtool, "principled_bsdf_emission_strength_float")

        
        #Create a box for all related inputs and operators 
        #for adding the shader maps one by one to
        #selected material
        box = layout.box()
        
        #--------------draw user input boxes
        #create box for all related boxes adding shader map to selected material
        box.label(text = "ADD SHADER MAP TO SELECTED MATERIAL (ONE MATERIAL)",)
        box.label(text = "Select a mesh and a material and add a shader map to the selected material")
        box.prop(pathtool, "props_txt_path")
        box.prop(pathtool, "export_folder_path")
        box.prop(pathtool, "skin_map_path")
        box.operator("loadueshaderscript.addbasic_operator")
                
        #Create a box for adding shader maps to all materials
        #to the selected mesh with all
        #related inputs and operators 
        box = layout.box()
        box.label(text = "ADD SHADER MAP TO ALL MATERIALS ON SELECTED MESHES (ALL MATERIALS)")
        box.label(text = "Select multiple meshes and add shader maps to all the materials on the selected meshes")
        box.prop(pathtool, "material_folder_path")
        box.prop(pathtool, "export_folder_path")
        box.prop(pathtool, "skin_map_path")
        box.operator("loadueshaderscript.addbasicall_operator" )
        
        


class LOADUESHADERSCRIPT_OT_add_basic(bpy.types.Operator):
    bl_label = "Add ONE Shader Map"
    bl_idname = "loadueshaderscript.addbasic_operator"
    def execute(self, context):
        scene = context.scene 
        #allow access to user inputted properties through pointer
        #to properties
        pathtool = scene.path_tool
        
        #find the selected material and 
        #create a basic shader on it
        selected_mat = bpy.context.active_object.active_material

        #this makes a list of all selected objects (can be multiple)
        active_obj = bpy.context.active_object
        
        #shade smooth on the active object
        #may already be shaded smooth if coming from the 
        #create_all_shader_maps
        #but this is just in case the user only runs create_one_shader_map
        mesh = active_obj.data
        for f in mesh.polygons:
            f.use_smooth = True
        
        create_one_shader_map(context, selected_mat, pathtool.props_txt_path, pathtool)
        
        return {"FINISHED"}


class LOADUESHADERSCRIPT_OT_add_basic_all(bpy.types.Operator):
    bl_label = "Add ALL Shader Maps"
    bl_idname = "loadueshaderscript.addbasicall_operator"
    def execute(self, context):
        #time how long it takes to create all shader maps for all materials
        #set start time
        time_start = time.time()

        scene = context.scene 
        #allow access to user inputted properties through pointer
        #to properties
        pathtool = scene.path_tool
        
        create_basic_all_shader_maps(context, pathtool)
        #don't use log so can use new line characterws
        print("\n\n\n [UE Shader Script]: Finished create_basic_all_shader_maps in: %.4f sec" % (time.time() - time_start))
    
        return {"FINISHED"}



#create all basic shader maps function
#just runs the create one basic shader map function
#for all selected objects and all materials
def create_basic_all_shader_maps(context, pathtool):
    #if the folder path is a relative path
    #turn it into an absolute one
    #as relative paths cause problems
    #when trying to load an image
    #paths already absolute not affected
    abs_mat_folder_path =  bpy.path.abspath(pathtool.material_folder_path)
    
    
    #To get a specific material you have to use:
    #bpy.context.selected_objects[0].data.materials[0]
    
    #this makes a list of all selected objects (can be multiple)
    objects_list = bpy.context.selected_objects
    
    
    #go through each selected object
    #and in every selected object
    #go through all of the selected object's materials
    for active_obj in objects_list: 
        
        #shade smooth on the all selected meshes
        #inside loop
        #must use context.object.data
        #as part of bpy.ops
        #as bpy.ops.object.shade_smooth() as part of bpy.ops
        #not bpy.data
        mesh = active_obj.data
        for f in mesh.polygons:
            f.use_smooth = True
        
        #fetch all materials of the current active_object in a list
        active_obj_materials_list = active_obj.data.materials[:]
    
        #create a shader map for each material in the materials list
        #in a loop
        for material in active_obj_materials_list:
            #make sure to use nodes before anything else
            #this is because if you don't have use nodes
            #enabled, the material and material.name will not work properly
            material.use_nodes = True
            
            #returns a generator object with the matching
            #absolute path to the props txt file
            #rglob is a globbing function (match and return a pattern)
            #and Path is a path type object, used for easy manipulation of paths
            
            #we use rglob and search for the
            #props.txt file because the file we are looking for
            #might be in a subdirectory such as Outfit01
            #and the user might have selected the material folder path
            #C:\Nyan\Dwight Recolor\Game\Characters\Slashers\Nurse\Materials\
            #instead of C:\Nyan\Dwight Recolor\Game\Characters\Slashers\Nurse\Materials\Outfit01
            #this allows for extra redundancy
            #so the props.txt file can be either in the current directory, or its subdirectories
            props_txt_name = "".join((material.name, ".props.txt"))
            gen_obj_match = Path(abs_mat_folder_path).rglob(props_txt_name)
            
            props_txt_path = get_value_in_gen_obj(gen_obj_match)
            
            is_props_txt_exist_for_material = True
            #debug
            #print("props_txt_path:", props_txt_path)
            #if can't find the propstxt file in the material folder do a recursive glob search
            #in the exported Game folder which costs more time since many folders
            #because it might be somewhere else like this instead
            #\Game\Characters\Campers\CommonAcc\Materials\Top\MI_CMMHair019_TAA.props.txt
            if props_txt_path == "":
                abs_export_folder_path = bpy.path.abspath(pathtool.export_folder_path)
                gen_obj_match = Path(abs_export_folder_path).rglob(props_txt_name)
                #get the new props_txt_path in the new generator object
                props_txt_path = get_value_in_gen_obj(gen_obj_match)
                #debug
                #print("refind props_txt_path:", props_txt_path)
                
                #if the props_txt_path is still null
                #after second search in the game folder
                #show an error message and ignore the material
                #do not create a shader map for it
                if props_txt_path == "":
                    warning_message = " ".join(("Warning: the props.txt file for object", active_obj.name, "material", material.name, "was not found in the Game Folder so it was ignored!"))
                    bpy.ops.ueshaderscript.show_message(message = warning_message)
                    log(warning_message)
                    is_props_txt_exist_for_material = False
                
            
            
            #not needed any more
            #get the current material's name to concatenate
            #a string the path to the props.txt file
            #props_txt_path = abs_mat_folder_path + material.name + ".props.txt"

            if (is_props_txt_exist_for_material):
                create_one_shader_map(context, material, props_txt_path, pathtool)
            
    return {"FINISHED"}  


def get_value_in_gen_obj(gen_obj_match):
    #set default values to be used in for loop
    props_txt_path = ""
    match = 0
    
    #only way to access values inside a generator object is
    #to use a for loop
    for file_path in gen_obj_match:
        match = match + 1
        props_txt_path = file_path
    
    #should only be one match from rglob
    #because we are matching one specific file
    #so if more matches then one print an error
    if match > 1:
        error_message = "Error: More than one match for the props_txt_path for rglob"
        bpy.ops.ueshaderscript.show_message(message = error_message)
        log(error_message)
    
    return props_txt_path


def create_one_shader_map(context, material, props_txt_path, pathtool):
    #makes sure use_nodes is turned on
    #for just imported meshes from the psk importer
    material.use_nodes = True

    #convert windows path to string
    props_txt_path = str(props_txt_path)

    #if the folder path is a relative path
    #turn it into an absolute one
    #as relative paths cause problems
    #when trying to load an image
    #absolute paths will stay as absolute paths
    abs_props_txt_path =  bpy.path.abspath(props_txt_path)

    #if bool is checked delete all nodes to create a clean slate 
    #for the new node map to be loaded
    if (pathtool.is_replace_nodes):
        tree = material.node_tree
        clear_nodes(tree)
        clear_links(tree)
    
    load_preset(context, material, abs_props_txt_path, pathtool)


def clear_nodes(tree):
    nodes = tree.nodes
    nodes.clear()


def clear_links(tree):
    links = tree.links
    links.clear()


def load_preset(context, material, abs_props_txt_path, pathtool):
    area = context.area
    #editor_type = area.ui_type
  
    JSON = get_json_from_selected_preset()
    if JSON == {'FINISHED'}:
        return JSON
    nodes_dict = json_to_nodes_dict(JSON)
    #debug print the nodes dictionary
    #look at this in notepad++ with JSON Sort plugin
    #to see it clearly
    #print("nodes_dict:",nodes_dict)
    # if nodes_dict["editor_type"] != editor_type:
    #     bpy.ops.ueshaderscript.show_message(
    #         message="Selected preset can not be restored to this node editor.")
    #     return {'FINISHED'}
    if nodes_dict["editor_type"] == SHADER_EDITOR:
        if (bpy.context.object is not None and bpy.context.object.type != "MESH" and bpy.context.object.type != "LIGHT") or bpy.context.object is None:
            bpy.ops.ueshaderscript.show_message(
                message = "Selected object canot be restored, please choose a Mesh or a Lamp to restore.")
            return {'FINISHED'}
        # if "shader_type" in nodes_dict:
        #     shader_type_value = nodes_dict["shader_type"]
        #     area.spaces[0].shader_type = shader_type_value
        # Branch for shader type: Object or World
        # shader_type = area.spaces[0].shader_type
        shader_type = nodes_dict["shader_type"]
        if bpy.context.object.type == "LIGHT" and shader_type == "OBJECT":
            light = bpy.data.lights[bpy.context.object.name]
            light.use_nodes = True
            node_tree = light.node_tree
        elif bpy.context.object.type == "LIGHT" and shader_type == "WORLD":
            world = get_active_world()
            node_tree = world.node_tree
        elif shader_type == "OBJECT":
            if bpy.context.object is None:
                bpy.ops.ueshaderscript.show_message(
                    message = "Please choose an object in View 3D to restore.")
                return {'FINISHED'}
            #mat = add_material_to_active_object()
            mat = material
            node_tree = mat.node_tree
        elif shader_type == "WORLD":
            world = get_active_world()
            node_tree = world.node_tree
        #debug
        #print("nodes_dict", nodes_dict)
        nodes = dict_to_nodes(nodes_dict["nodes_list"], node_tree)
        list_to_links(nodes_dict["links_list"], node_tree, nodes)
        dict_to_textures(nodes_dict["img_textures_list"], material, node_tree, abs_props_txt_path, pathtool)
    else:
         bpy.ops.ueshaderscript.show_message(
                    message = "Only Shader Editor Restores are supported currently not Compositor editor restores.")


    # elif nodes_dict["editor_type"] == COMPOSITOR_EDITOR:
    #     bpy.context.scene.use_nodes = True
    #     node_tree = bpy.context.scene.node_tree
    #     if clear:
    #         clear_nodes(node_tree)
    #         clear_links(node_tree)
    #     nodes = dict_to_nodes(nodes_dict["nodes_list"], node_tree)
    #     list_to_links(nodes_dict["links_list"], node_tree, nodes)
    # elif nodes_dict["editor_type"] == ANIMATION_NODE_EDITOR:
    #     bpy.context.scene.use_nodes = True
    #     area = context.area
    #     node_editor = area
    #     node_tree = node_editor.spaces[0].node_tree
    #     if not node_tree:
    #         bpy.ops.node.new_node_tree()
    #         node_tree = node_editor.spaces[0].node_tree
    #     if clear:
    #         clear_nodes(node_tree)
    #         clear_links(node_tree)
    #     nodes = dict_to_nodes_for_animation_nodes(
    #         nodes_dict["nodes_list"], node_tree)
    #     list_to_links_for_animation_nodes(
    #         nodes_dict["links_list"], node_tree, nodes)
    # if from_10_last:
    #     pass
    # elif from_10_most:
    #     pass
    # else:
    #     # Add preset to 10 last used presets
    #     folder_name = get_selected_folder_name()
    #     preset_name = get_selected_preset_name()
    #     add_preset_to_10_last(folder_name, preset_name)
    #     # Update 10 most used presets
    #     update_selected_preset_used_count()
    #     update_10_most_used_presets()


def get_active_world():
    world = bpy.context.scene.world
    if world:
        world.use_nodes = True
        return world
    new_world = bpy.data.worlds.new(name="World")
    new_world.use_nodes = True
    bpy.context.scene.world = new_world
    return new_world


def add_material_to_active_object():
    obj_data = bpy.context.object.data
    obj = bpy.context.object
    if obj.active_material:
        obj.active_material.use_nodes = True
        return obj.active_material
    new_mat = bpy.data.materials.new("Material")
    new_mat.use_nodes = True
    obj_data.materials.append(new_mat)
    obj.active_material = new_mat
    return new_mat

def get_json_from_selected_preset():
    isOverridePackage = True
    selected_folder_presets = get_selected_folder_presets(isOverridePackage)
    index = selected_folder_presets.preset_index
    if index < 0:
        bpy.ops.ueshaderscript.show_message(
            message = "Please choose a nodes preset to restore.")
        return {'FINISHED'}
    JSON = selected_folder_presets.presets[index].content
    return JSON

#--------------------DICTIONARY CONVERT BACK TO NODES SHADER MAP


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
        # this is for Group nodes
        if node["node_name"] == "ShaderNodeGroup":
            dict_to_nodes_handle_shader_node_group(new_node, node)
        # if node["node_name"] == "CompositorNodeGroup":
        #     dict_to_nodes_handle_compositor_node_group(new_node, node)
        # if node["node_name"] == "CompositorNodeOutputFile":
        #     dict_to_nodes_handle_compositor_node_output_file(new_node, node)
        #     new_node.format.file_format = node["file_format"]
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

def dict_to_nodes_handle_shader_node_group(new_node, node_dict):
    #store active/selected scene to variable
    scene = bpy.context.scene
    #allow access to user inputted properties through pointer
    #to properties
    pathtool = scene.path_tool
    
    node_group_name = node_dict["node_tree"]["name"]
    #debug
    #print("pathtool.is_reuse_node_group_with_same_name", pathtool.is_reuse_node_group_with_same_name)

    #if the user has chosen to reuse node groups we must check 
    #whether a node group exists to be reused 
    if(pathtool.is_reuse_node_group_with_same_name):
        check_if_should_reuse_node_group(new_node, node_dict, node_group_name)
    else:
        #else if the user has chosen not to reuse node groups create new node groups
        #whether or not they already exist
        create_a_new_node_group(new_node, node_dict, node_group_name)
    

def check_if_should_reuse_node_group(new_node, node_dict, node_group_name):
    #check if the node group with name you are trying to restore exists
    #if it exists then check how many users it has
    is_node_group_name_exist = bpy.data.node_groups.get(node_group_name, None)
    
    #debug
    #print("is_node_group_name_exist for", node_group_name, ":", is_node_group_name_exist)

    if (is_node_group_name_exist):
        #if it has 0 users it will still reuse the node group
        #as long as a node group with the node group name 
        #recorded in the python dictionary exists
        #it will reuse it
        reuse_the_node_group(new_node, node_dict, node_group_name)
    else:
        create_a_new_node_group(new_node, node_dict, node_group_name)


def reuse_the_node_group(new_node, node_dict, node_group_name):
    #find and reuse already created node group
    node_tree_of_group = bpy.data.node_groups[node_group_name]

    #don't copy inputs and outputs of the shader_node group if you are reusing it
    #only set the node tree of the node to the existing node group
    new_node.node_tree = node_tree_of_group

    #make sure use fake user is enabled for the node group
    bpy.data.node_groups[node_group_name].use_fake_user = True


def create_a_new_node_group(new_node, node_dict, node_group_name):
    #make a new node_group
    node_tree_of_group = bpy.data.node_groups.new(type="ShaderNodeTree",
                                                          name=node_group_name)
    copy_inputs_outputs_links_for_node_group(node_tree_of_group, new_node, node_dict, node_group_name)
    

def copy_inputs_outputs_links_for_node_group(node_tree_of_group, new_node, node_dict, node_group_name):
    for input in node_dict["inputs"]:
        new_node.inputs.new(input["type_name"], input["name"])
        node_tree_of_group.inputs.new(input["type_name"], input["name"])
    for output in node_dict["outputs"]:
        new_node.outputs.new(output["type_name"], output["name"])
        node_tree_of_group.outputs.new(output["type_name"], output["name"])
    nodes = dict_to_nodes(node_dict["node_tree"]
                          ["nodes_list"], node_tree_of_group)
    list_to_links(node_dict["node_tree"]["links_list"],
                  node_tree_of_group, nodes)
    interface_inputs = node_tree_of_group.inputs
    inputs_list = node_dict["node_tree"]["interface_inputs"]
    list_to_interface_inputs(interface_inputs, inputs_list)
    new_node.node_tree = node_tree_of_group

    #make sure use fake user is enabled for the node group
    bpy.data.node_groups[node_group_name].use_fake_user = True



def list_to_links(links_list, tree, nodes):
    links = tree.links
    for link in links_list:
        from_node_index = link["from_node_index"]
        from_node = nodes[from_node_index]
        from_socket_index = link["from_socket_index"]
        #from_socket = from_node.outputs[from_socket_index]
        from_socket = get_output_by_name(
            from_node.outputs, link["from_socket_name"], from_socket_index)
        to_node_index = link["to_node_index"]
        to_node = nodes[to_node_index]
        to_socket_index = link["to_socket_index"]
        #to_socket = to_node.inputs[to_socket_index]
        to_socket = get_input_by_name(
            to_node.inputs, link["to_socket_name"], to_socket_index)
        if to_socket == None or from_socket == None:
            continue
        links.new(from_socket, to_socket)


def dict_to_textures(img_textures_list, material, node_tree, abs_props_txt_path, pathtool):
    print("\nabs_props_txt_path", abs_props_txt_path)
    
    #open the propstxt file for the material and find the
    #texture locations from it
    #with just means open and close file
    with open(abs_props_txt_path, 'r') as f:
        #read entire file to one string
        data = f.read()
        #find all matches through regex to the string Texture2D' with capture group 
        #any character zero to unlimited times and ending with '
        #also store capture groups into a list variable
        match_list = re.findall("Texture2D\'(.*)\.", data)


    #---------------------add image texture nodes 
    if pathtool.is_add_img_textures:
        #turn the path to the skin map to an absolute path instead of a relative one
        #to avoid errors
        abs_skin_map_path = bpy.path.abspath(pathtool.skin_map_path)

        not_delete_img_texture_node_list = []
        #use loop to go through all locations
        #specified in props.txt file
        #and create image texture nodes + 
        #load all images for image textures
        for tex_location in match_list:
            #unused since now we use .endswith otherwise some might have really long suffixes
            #fetch last 10 characters in path which will tell you what
            #the current texture is in charge of e.g slice _BC off
            #/Game/Characters/Slashers/Bear/Textures/Outfit01/T_BEHead01_BC
            #longest id is _TintBC 7 characters
            #tex_id = tex_location[-10:]
            
            #if the folder path is a relative path
            #turn it into an absolute one
            #as relative paths cause problems
            #when trying to load an image
            abs_export_folder_path = bpy.path.abspath(pathtool.export_folder_path)
            
            # Returns user specified export game folder path
            # with first character removed
            # reason why is there would be double up of \/ when 
            #concatenating strings
            user_tex_folder = abs_export_folder_path[:-1]
            
            #replace forward slash with backslash reason why is
            # when concatenating complete path looks like this
            #if no replace path looks like e.g. C:\Nyan\Dwight Recolor\Game/Characters/Slashers/Bear/Textures/Outfit01/T_BEHead01_BC
            #which is weird
            #backslash is used to escape backslash character
            tex_location = tex_location.replace("/","\\")
            
            #if the user selects the game folder instead of the
            #parent folder, the first 5 characters of 
            #the user input box: user_tex_folder will be "Game"
            #so we remove "Game\" from the tex_location
            #to avoid a double up
            #this is extra redundancy so if the
            #user chooses either the Game folder or
            #the parent folder of the Game folder
            #both options will work
            if user_tex_folder[-4:] == "Game":
                #backslash is used to escape backslash character
                tex_location = tex_location.replace("\\Game","")
     
            #must string concatenate the user specified texture location path to 
            #the texture location
            #as the tex_location will only be 
            #e.g /Game/Characters/Slashers/Bear/Textures/Outfit01/T_BEHead01_BC
            #this does not provide a complete path to where the user exported
            #the texture
            #we need e.g. C:\Nyan\Dwight Recolor\Game\Characters
            #\Slashers\Bear\Textures\Outfit01\T_BEHead01_BC
            #using pathtool.texture_file_type_enum because it may be ".tga" or ".png"
            complete_path = "".join((user_tex_folder, tex_location, pathtool.texture_file_type_enum))

            #If the texture is listed in the 
            #props.txt file and it is one of the
            #image textures we are interested in we will
            #load the corresponding image
            
            #this for loop will load all image textures
            #via reading the img_textures_list
            #recorded in the node_dict when the dictionary is saved
            for textures in img_textures_list:
                suffix_list = textures["suffix_list"]
                node_name = textures["node_name"]

                #special case if the node is a skin texture node
                #always load skin height map texture regardless
                #because it doesn't come from the props.txt file
                #it is externally added from skin_map_path
                #and the skin_map path is not empty
                #so do not need to check the suffix for a match against the propstxt file
                #always load
                if textures["texture"] == "skin" and abs_skin_map_path !="":
                    node_to_load = node_tree.nodes[node_name]
                    #bpy.data.images.load(abs_skin_map_path)
                    load_image_texture(node_to_load, abs_skin_map_path, pathtool)
                    #add to whitelist
                    not_delete_img_texture_node_list.append(node_to_load)
                    #continue and skip the rest of this loop because there is no need to check 
                    #whether this one should be loaded since we have loaded it already
                    continue
                
                #we must check a match against all the suffixes in the suffix list
                #one texture may have one to many suffixes e.g. transparency might have "_M", "_A"
                for suffix in suffix_list:
                    check_match_propstxt_tex_location_vs_preset_img_textures_list_suffix(tex_location, suffix, node_tree, node_name, 
                            complete_path, pathtool, textures, material, not_delete_img_texture_node_list)
        


        #check through the whole tree for image
        #texture nodes and delete any 
        #that are not on the whitelist
        if pathtool.is_delete_unused_img_texture_nodes:
            #debug
            #print("\nnot_delete_img_texture_node_list (the whitelist):", not_delete_img_texture_node_list)
            
            #initialise and clear blacklist to delete related nodes
            prefix_of_related_nodes_to_delete = []
            nodes = node_tree.nodes
            for node in nodes:
                #debug to find what the node.type is for 
                #image texture nodes
                #print("node.type:", node.type)
                #if it's not in the whitelist which means 
                #an image wasn't loaded to the node, delete the image texture node
                if node.type == "TEX_IMAGE" and not(node in not_delete_img_texture_node_list): 
                    #delete node and mark all related nodes to delete list
                    #that is mark all nodes which starts with the same name
                    prefix_of_related_nodes_to_delete.append(node.name)
                    nodes.remove(node) 

            
            #do one more loop through all nodes to check for related nodes
            #to delete if option is checked
            if pathtool.is_delete_unused_related_nodes:
                #debug
                #print("prefix_of_related_nodes_to_delete:", prefix_of_related_nodes_to_delete)

                #go back through all the nodes and now delete all nodes 
                #that start with the prefix
                for node in nodes:
                    #print("node:", node)
                    #the line below must not be int he loop otherwise the loop fails
                    node_name = node.name
                    #for every node check against every prefix that is on the blacklist
                    for prefix in prefix_of_related_nodes_to_delete:
                        if node_name.startswith(prefix):
                            #print("node:", node, "has been deleted.")
                            nodes.remove(node)


def check_match_propstxt_tex_location_vs_preset_img_textures_list_suffix(tex_location, suffix, node_tree, node_name, complete_path, pathtool, textures, material, not_delete_img_texture_node_list):
    #check what the last two/three characters are of the id
    #and look for the specific ids we are interested in
    #identifier
    #tex_location is from the props txt file comparing against 
    #suffix which is what is recorded from the node_dict
    if tex_location.endswith(suffix):
        #looks like this normally
        #node_to_load = bpy.context.active_object.active_material.node_tree.nodes["Diffuse Node"]
        #node_to_load.image = bpy.data.images.load("C:\Seabrook\Dwight Recolor\Game\Characters\Campers\Dwight\Textures\Outfit01\T_DFHair01_BC.tga")

        #use node_tree which is the current node tree
        #we're trying to texture
        #and node_name which is the Node Name in the Items panel in the shader editor
        #this will uniquely identify a single node
        node_to_load = node_tree.nodes[node_name]
        load_image_texture(node_to_load, complete_path, pathtool)

        img_textures_special_handler(textures, pathtool, material, node_to_load, node_tree)
            
            
        #if an image texture node has been loaded
        #and the option to delete image texture nodes who
        #have not had an image loaded to them is True
        #then we will add it to a whitelist
        #so it does not get deleted
        if pathtool.is_delete_unused_img_texture_nodes:
            not_delete_img_texture_node_list.append(node_to_load)

def img_textures_special_handler(textures, pathtool, material, node_to_load, node_tree):
    #special case if the node that was loaded was a transparency node _M
    #we need to set the material blend_method to alpha clip
    #and set the alpha threshold to 0 which looks best
    #with the least clipped
    if textures["texture"] == "transparency":
        #change to non-colour based on user settings
        if(pathtool.is_m_non_colour):
            node_to_load.image.colorspace_settings.name = "Non-Color"
        
        #change clipping method + threshold to clip
        clipping_method = pathtool.clipping_method_enum
        if clipping_method == "CLIP":
            material.blend_method = "CLIP"
            material.shadow_method = "CLIP"
            material.alpha_threshold = 0
        elif clipping_method == "HASHED":
            material.blend_method = "HASHED"
            material.shadow_method = "HASHED"
        else:
            error_message = "Error: could not find clipping method"
            bpy.ops.ueshaderscript.show_message(message = error_message)
            log(error_message)

    #special case if the node loaded was a Normal Map _N or Packed RGB ARM _ORM
    #change colour interpolation to non-colour
    elif textures["texture"] == "normal":
        if(pathtool.is_normal_non_colour):
            node_to_load.image.colorspace_settings.name = "Non-Color"
    
    elif textures["texture"] == "packed_orm":
        if(pathtool.is_orm_non_colour):
            node_to_load.image.colorspace_settings.name = "Non-Color"

    #special case if the node loaded was an emissive BDE
    #find the principled BSDF node
    #and turn the emission strength to 5
    elif textures["texture"] == "emissive":
        #only change the emission strength if the bool checkbox is checked
        if (pathtool.is_change_principle_bsdf_emission_strength):
            change_emission_strength_principled_bsdf(node_tree, "BSDF_PRINCIPLED", pathtool.principled_bsdf_emission_strength_float)


def load_image_texture(node_to_load, complete_path_to_image, pathtool):
    #if the user has chosen to reuse node groups we must check 
    #whether a node group exists to be reused 
    if(pathtool.is_reuse_img_texture_with_same_name):
        check_if_should_reuse_img_texture(node_to_load, complete_path_to_image)
    else:
        #else if the user has chosen not to reuse node groups create new node groups
        #whether or not they already exist
        create_a_new_img_texture(node_to_load, complete_path_to_image)

    
    

def check_if_should_reuse_img_texture(node_to_load, complete_path_to_image):
    #reminder complete_path_to_image will look like
    #C:\Nyan\Dwight Recolor\Game\Characters\Slashers\Bear\Textures\Outfit01\T_BEHead01_BC.tga
    #extract just the image texture name using basename to get only the very right bit just the file name
    
    img_texture_file_name = os.path.basename(complete_path_to_image)

    #debug
    #print("img_texture_file_name:", img_texture_file_name)

    #check if the node group with name you are trying to restore exists
    #if it exists then check how many users it has
    is_image_texture_name_exist = bpy.data.images.get(img_texture_file_name, None)
    
    #debug
    #print("is_image_texture_name_exist for", img_texture_name, ":", is_image_texture_name_exist)

    if (is_image_texture_name_exist):
        #if it has 0 users it will still reuse the image texture
        #as long as an image with the same name as the image texture being loaded exists
        #it will reuse it
        reuse_the_img_texture(node_to_load, img_texture_file_name)
    else:
        create_a_new_img_texture(node_to_load, complete_path_to_image)


def create_a_new_img_texture(node_to_load, complete_path_to_image):
    node_to_load.image = bpy.data.images.load(complete_path_to_image)


def reuse_the_img_texture(node_to_load, img_texture_file_name):
    node_to_load.image = bpy.data.images[img_texture_file_name]


#returns first principled bsdf in case of two
def change_emission_strength_principled_bsdf(node_tree, node_type, emission_strength):
    count = 0
    for node in node_tree.nodes:
        if (node.type == "BSDF_PRINCIPLED"):
            count = count + 1
            node.inputs["Emission Strength"] = emission_strength
    
    if count > 1:
        warning_message = "Warning: More than one P BSDF so changed all P BSDF node Emission Strengths to 5!"
        bpy.ops.ueshaderscript.show_message(message = warning_message)
        log(warning_message)
        

def get_input_by_name(inputs, name, index):
    for i, input in enumerate(inputs):
        if name == input.name and i == index:
            return input
    for i, input in enumerate(inputs):
        if name == input.name:
            return input
    return None


def input_dict_to_socket_value(input, input_dict):
    t = input_dict["type_name"]
    if t == "NodeSocketColor":
        value = tuple(input_dict["value"])
        input.default_value[0] = value[0]
        input.default_value[1] = value[1]
        input.default_value[2] = value[2]
        input.default_value[3] = value[3]
    elif t == "NodeSocketFloatFactor":
        value = input_dict["value"]
        input.default_value = value
    elif t == "NodeSocketVector" or t == "NodeSocketVectorDirection" or \
            t == "NodeSocketVectorEuler" or t == "NodeSocketVectorTranslation" or \
            t == "NodeSocketVectorVelocity" or t == "NodeSocketVectorXYZ":
        value = tuple(input_dict["value"])
        input.default_value[0] = value[0]
        input.default_value[1] = value[1]
        input.default_value[2] = value[2]
    elif t == "NodeSocketBool":
        value = input_dict["value"]
        if value == 0:
            input.default_value = False
        else:
            input.default_value = True
    elif t == "NodeSocketFloat":
        input.default_value = input_dict["value"]
    elif t == "NodeSocketFloatAngle":
        input.default_value = input_dict["value"]
    elif t == "NodeSocketFloatPercentage":
        input.default_value = input_dict["value"]
    elif t == "NodeSocketFloatTime":
        input.default_value = input_dict["value"]
    elif t == "NodeSocketFloatUnsigned":
        input.default_value = input_dict["value"]
    elif t == "NodeSocketInt":
        input.default_value = input_dict["value"]
    elif t == "NodeSocketIntFactor":
        input.default_value = input_dict["value"]
    elif t == "NodeSocketIntPercentage":
        input.default_value = input_dict["value"]
    elif t == "NodeSocketIntUnsigned":
        input.default_value = input_dict["value"]
    elif t == "NodeSocketString":
        input.default_value = input_dict["value"]
    elif t == "NodeSocketVector":
        value = tuple(input_dict["value"])
        input.default_value[0] = value[0]
        input.default_value[1] = value[1]
        input.default_value[2] = value[2]
    elif t == "NodeSocketVectorAcceleration":
        value = tuple(input_dict["value"])
        input.default_value[0] = value[0]
        input.default_value[1] = value[1]
        input.default_value[2] = value[2]

def get_output_by_name(outputs, name, index):
    for i, output in enumerate(outputs):
        if name == output.name and i == index:
            return output
    for i, output in enumerate(outputs):
        if name == output.name:
            return output
    return None


def list_to_interface_inputs(inputs, inputs_list):
    #debug
    #print("list(enumerate(inputs)):", list(enumerate(inputs)))
    for index, input in enumerate(inputs):
        min_value = inputs_list[index]["min_value"]
        max_value = inputs_list[index]["max_value"]
        if min_value != "None":
            input.min_value = min_value
        if max_value != "None":
            input.max_value = max_value


def output_dict_to_socket_value(output, output_dict):
    input_dict_to_socket_value(output, output_dict)

def dict_to_attr(node, attr_dict, repeated=False):
    t = attr_dict["type_name"]
    name = attr_dict["attr_name"]
    if t == "Not Handle Type":
        return
    if t == "NoneType":
        v = None
        return
    v = attr_dict["value"]
    if t == "bool":
        if v == 0:
            v = False
        else:
            v = True
    if t == "tuple":
        v = tuple(v)
    if t == "Vector":
        v = Vector(tuple(v))
    if t == "Euler":
        v = Euler(tuple(v), 'XYZ')
    if t == "Text":
        text_name = v
        if text_name != "":
            txt = bpy.data.texts.get(text_name)
        v = txt
    if t == "Image":
        image = bpy.data.images.get(v)
        if image is None:
            try:
                bpy.ops.image.open(filepath=attr_dict["image_filepath"])
            except Exception as e:
                log("file path of image attributes not found: ",
                      attr_dict["image_filepath"])
            filename = os.path.basename(attr_dict["image_filepath"])
            image = bpy.data.images.get(filename)
            if image is not None:
                image.source = attr_dict["image_source"]
        if image is not None:
            image.source = attr_dict["image_source"]
        v = image
    if t == "Object":
        obj = bpy.data.objects.get(v)
        v = obj
    if t == "ImageUser":
        set_values_for_ImageUser(node.image_user, v)
        return
    if t == "ParticleSystem":
        obj_name = attr_dict["object_name"]
        obj = bpy.data.objects[obj_name]
        particle_system = obj.particle_systems.get(v)
        ps = getattr(node, name)
        v = particle_system
    if t == "Color":
        v = Color(tuple(v))
    if t == "ColorRamp":
        if repeated:
            return
        color_ramp_dict = v
        color_ramp = node.color_ramp  # Currently all color ramp attr is via node.colorramp
        color_ramp.color_mode = color_ramp_dict["color_mode"]
        color_ramp.hue_interpolation = color_ramp_dict["hue_interpolation"]
        color_ramp.interpolation = color_ramp_dict["interpolation"]
        elements = color_ramp.elements
        # debug
        #for e in elements:
            # print("color ramp element position:", e.position)
        for index, color_ramp_element in enumerate(color_ramp_dict["elements"]):
            if index == 0 or index == len(color_ramp_dict["elements"]) - 1:
                ele = elements[index]
            else:
                ele = elements.new(color_ramp_element["position"])
            ele.alpha = color_ramp_element["alpha"]
            ele.color = tuple(color_ramp_element["color"])
            ele.position = color_ramp_element["position"]
    if t == "CurveMapping":
        if repeated:
           return
        curve_mapping_dict = v
        # Currently all curve mapping attr is via node.mapping
        curve_mapping = node.mapping
        set_values_for_CurveMapping(curve_mapping, curve_mapping_dict)
        return
    if t != "ColorRamp":
        try:
            setattr(node, name, v)
        except Exception as e:
            print("dict_to_attr() error:", str(e))

def set_values_for_CurveMapping(curve_mapping, value_dict):
    def recreat_points(curve, total_points):
        current_points = len(curve.points)
        while total_points > current_points:
            curve.points.new(0, 0)
            current_points = len(curve.points)

    def set_values_for_curve(curve, curve_dict):
        set_attr_if_exist(curve, "extend", curve_dict["extend"])
        remove_all_curve_points(curve)
        recreat_points(curve, len(curve_dict["points"]))
        for index, point_dict in enumerate(curve_dict["points"]):
            p = curve.points[index]
            p.handle_type = point_dict["handle_type"]
            p.location = tuple(point_dict["location"])

    curve_mapping.black_level = tuple(value_dict["black_level"])
    curve_mapping.clip_max_x = value_dict["clip_max_x"]
    curve_mapping.clip_max_y = value_dict["clip_max_y"]
    curve_mapping.clip_min_x = value_dict["clip_min_x"]
    curve_mapping.clip_min_y = value_dict["clip_min_y"]
    curve_mapping.tone = value_dict["tone"]
    curve_mapping.use_clip = value_dict["use_clip"]
    curve_mapping.white_level = tuple(value_dict["white_level"])
    curves_dict = value_dict["curves"]
    for index, curve_dict in enumerate(curves_dict):
        set_values_for_curve(curve_mapping.curves[index], curve_dict)
    curve_mapping.update()

def set_attr_if_exist(obj, attr, value):
    if hasattr(obj, attr) and value != "None":
        setattr(obj, attr, value)

def remove_all_curve_points(curve):
    while len(curve.points) > 2:
        points = curve.points
        for p in points:
            try:
                curve.points.remove(p)
            except:
                print("(Safe to ignore)Unable to remove curve point")



def set_values_for_ColorMapping(color_mapping, value_dict):
    color_mapping.blend_color = tuple(value_dict["blend_color"])
    color_mapping.blend_factor = value_dict["blend_factor"]
    color_mapping.blend_type = value_dict["blend_type"]
    color_mapping.brightness = value_dict["brightness"]
    color_mapping.contrast = value_dict["contrast"]
    color_mapping.saturation = value_dict["saturation"]
    color_mapping.use_color_ramp = value_dict["use_color_ramp"]


def set_values_for_ImageUser(image_user, value_dict):
    image_user.frame_current = value_dict["frame_current"]
    image_user.frame_duration = value_dict["frame_duration"]
    image_user.frame_offset = value_dict["frame_offset"]
    image_user.frame_start = value_dict["frame_start"]
    image_user.use_cyclic = value_dict["use_cyclic"]
    image_user.use_auto_refresh = value_dict["use_auto_refresh"]


#unused but good example of how to implement a shader map manually
#making each node and linking each node by hand
def roman_noodles_shader_map(material, props_txt_path, pathtool):
    #store new link function to variable
    link = material.node_tree.links.new
    
    #store new node function to variable
    new_node = material.node_tree.nodes.new
    
    #assign Principled BSDF to a variable so can be referenced later
    #so that nodes can link to it
    principled_node = material.node_tree.nodes.get('Principled BSDF')
    #add subsurface skin settings to principled BSDF node
    #if the material is for skin
    if pathtool.is_material_skin == True:
        principled_node.subsurface_method = "RANDOM_WALK"
        principled_node.inputs[1].default_value = 0.03
        principled_node.inputs["Subsurface Color"].default_value = (0.8, 0, 0, 1)
        
    principled_node.inputs["Specular"].default_value = 0.064

    #start adding all nodes and respective links to shader map
    #--------------add everything except image texture nodes
    #using inputs through ["Metallic"] rather than numbers is much
    #better as sometimes there are hidden inputs and outputs
    srgb_node = new_node("ShaderNodeSeparateRGB")
    srgb_node.location = (-150,150) # x,y
    link(srgb_node.outputs[2], principled_node.inputs["Metallic"])

    ramp_node_1 = new_node("ShaderNodeValToRGB")
    ramp_node_1.location = (-450,50) # x,y
    ramp_node_1.color_ramp.elements[1].position = 0.209
    link(ramp_node_1.outputs[0], principled_node.inputs["Roughness"])
    
    bump_node = new_node("ShaderNodeBump")
    bump_node.location = (-200,-200) # x,y
    bump_node.inputs[0].default_value = 0.175
    link(bump_node.outputs[0], principled_node.inputs["Normal"])
    
    rgbbw_node = new_node("ShaderNodeRGBToBW")
    rgbbw_node.location = (-150,0) # x,y
    link(rgbbw_node.outputs[0], ramp_node_1.inputs["Fac"])
    
    normap_node = new_node(type="ShaderNodeNormalMap")
    normap_node.location = (-400,-200) # x,y
    link(normap_node.outputs[0], bump_node.inputs["Normal"])
    
    #only add skin related nodes for height map
    #if material is for skin
    if pathtool.is_material_skin == True:
        map_node = new_node(type="ShaderNodeMapping")
        map_node.location = (-300,-450) # x,y
        map_node.inputs[3].default_value[0] = 12
        map_node.inputs[3].default_value[1] = 12
        map_node.inputs[3].default_value[2] = 12
        
        textcoord_node = new_node(type="ShaderNodeTexCoord")
        textcoord_node.location = (-500,-450) # x,y
        link(textcoord_node.outputs[2], map_node.inputs[0])

    
    #open the propstxt file for the material and find the
    #texture locations from it
    #with just means open and close file
    with open(props_txt_path, 'r') as f:
        #read entire file to one string
        data = f.read()
        #find all matches through regex to the string Texture2D' with capture group 
        #any character zero to unlimited times and ending with '
        #also store capture groups into a list variable
        match_list = re.findall("Texture2D\'(.*)\.", data)
    
    #only add image textures nodes if Include Image Textures
    #in panel is true
    if pathtool.is_add_img_textures:
        #---------------add image texture nodes    
        #example loading image
        #texImage.image = bpy.dat.images.load(
        #"C:\Users\myName\Downloads\Textures\Downloaded\flooring5.jpg")
        
        #add height map if Add Skin Related Nodes is checked and 
        #add Height Map Skin Texture is checked
        #add the height map image texture and load the user defined
        #height map image
        
        if pathtool.is_add_img_textures == True and pathtool.is_material_skin == True and pathtool.is_add_height_map == True:
            height_map_path = pathtool.height_map_path
            
            height_map_node = new_node('ShaderNodeTexImage')
            height_map_node.location = (-100,-450) #x,y
            height_map_node.image = bpy.data.images.load(height_map_path)
            link(height_map_node.outputs[0], bump_node.inputs[2])
            link(map_node.outputs[0], height_map_node.inputs[0])
            height_map_node.interpolation = "Cubic"
        
        
        #use loop to go through all locations
        #specified in props.txt file
        #and create image texture nodes + 
        #load all images for image textures
        for tex_location in match_list:
            
            #fetch last 6 characters in path which will tell you what
            #the current texture is in charge of e.g slice _BC off
            #/Game/Characters/Slashers/Bear/Textures/Outfit01/T_BEHead01_BC
            #longest id is _ORM or _BDE 4 characters 
            tex_id = tex_location[-6:]
            
            #if the folder path is a relative path
            #turn it into an absolute one
            #as relative paths cause problems
            #when trying to load an image
            abs_export_folder_path = bpy.path.abspath(pathtool.export_folder_path)
            
            # Returns user specified export game folder path
            # with first character removed
            # reason why is there would be double up of \/ when 
            #concatenating strings
            user_tex_folder = abs_export_folder_path[:-1]
            
            #replace forward slash with backslash reason why is
            # when concatenating complete path looks like this
            #if no replace path looks like e.g. C:\Nyan\Dwight Recolor\Game/Characters/Slashers/Bear/Textures/Outfit01/T_BEHead01_BC
            #which is weird
            #backslash is used to escape backslash character
            tex_location = tex_location.replace("/","\\")
            
            #if the user selects the game folder instead of the
            #parent folder, the first 5 characters of 
            #the user input box: user_tex_folder will be "Game"
            #so we remove "Game\" from the tex_location
            #to avoid a double up
            #this is extra redundancy so if the
            #user chooses either the Game folder or
            #the parent folder of the Game folder
            #both options will work
            if user_tex_folder[-4:] == "Game":
                #backslash is used to escape backslash character
                tex_location = tex_location.replace("\\Game","")
     
            #must string concatenate the user specified texture location path to 
            #the texture location
            #as the tex_location will only be 
            #e.g /Game/Characters/Slashers/Bear/Textures/Outfit01/T_BEHead01_BC
            #this does not provide a complete path to where the user exported
            #the texture
            #we need e.g. C:\Nyan\Dwight Recolor\Game\Characters
            #\Slashers\Bear\Textures\Outfit01\T_BEHead01_BC
            #using join because it's faster
            #also join requires a tuple so there are two circle brackets used
            complete_path = "".join((user_tex_folder, tex_location, ".tga"))

            #If the texture is listed in the 
            #props.txt file and it is one of the
            #image textures we are interested in we will add the node
            #and load the corresponding image
                 
            #check what the last two/three characters are of the id
            #and look for the specific ids we are interested in
            #identifier
            if tex_id.endswith("_BC"):
                bc_node = new_node('ShaderNodeTexImage')
                bc_node.location = (-300,450) #x,y
                bc_node.image = bpy.data.images.load(complete_path)
                link(bc_node.outputs[0], principled_node.inputs[0])
                link(bc_node.outputs[0], rgbbw_node.inputs[0])
                bc_node.interpolation = "Cubic"
                
            elif tex_id.endswith("_ORM"):
                orm_node = new_node('ShaderNodeTexImage')
                orm_node.location = (-750, 300) #x,y
                orm_node.image = bpy.data.images.load(complete_path)
                link(orm_node.outputs[0], srgb_node.inputs[0])
                orm_node.image.colorspace_settings.name = "Non-Color"
                
            elif tex_id.endswith("_N"):
                n_node = new_node('ShaderNodeTexImage')
                n_node.location = (-800,-200) #x,y
                n_node.image = bpy.data.images.load(complete_path)
                link(n_node.outputs[0], normap_node.inputs[1])
                n_node.image.colorspace_settings.name = "Non-Color"
                
            elif tex_id.endswith("_M"):
                #add ramp node to connect to M node and control
                #alpha if alpha transparency is required
                ramp_node_2 = new_node("ShaderNodeValToRGB")
                ramp_node_2.location = (-750,20) # x,y
                ramp_node_2.color_ramp.elements[1].position = 0.95
                link(ramp_node_2.outputs[0], principled_node.inputs["Alpha"])
                
                m_node = new_node('ShaderNodeTexImage')
                m_node.location = (-1100,20) #x,y
                m_node.image = bpy.data.images.load(complete_path)
                link(m_node.outputs[0], ramp_node_2.inputs[0])
                material.blend_method = 'CLIP'






classes = [PathProperties, LOADUESHADERSCRIPT_PT_main_panel, 
LOADUESHADERSCRIPT_OT_add_basic, LOADUESHADERSCRIPT_OT_add_basic_all]
 
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
        #register path_tool as a type which has all
        #the user input properties from the properties class 
        bpy.types.Scene.path_tool = bpy.props.PointerProperty(type = PathProperties)
 
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
        
        #unregister path_tool as a type
        del bpy.types.Scene.path_tool
 
 
if __name__ == "__main__":
    register()
