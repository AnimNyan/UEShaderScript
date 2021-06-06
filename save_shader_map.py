import bpy

import json

import os

from bpy.props import (StringProperty,
                       BoolProperty,
                       IntProperty,
                       FloatProperty,
                       FloatVectorProperty,
                       EnumProperty,
                       PointerProperty,
                       CollectionProperty
                       )

from bpy.types import (Panel,
                       Operator,
                       AddonPreferences,
                       PropertyGroup,
                       UIList
                       )



#import libraries required for types
#for dict to nodes
from mathutils import (Vector, Euler, Color)
from bpy.types import Text
from bpy.types import Object
from bpy.types import ColorMapping, CurveMapping, ColorRamp
from bpy.types import Image, ImageUser, ParticleSystem



from bpy.types import (
    NodeSocketBool, NodeSocketColor, NodeSocketFloat, NodeSocketFloatAngle,
    NodeSocketFloatFactor, NodeSocketFloatPercentage, NodeSocketFloatTime,
    NodeSocketFloatUnsigned, NodeSocketInt, NodeSocketIntFactor, NodeSocketIntPercentage,
    NodeSocketIntUnsigned, NodeSocketShader, NodeSocketString, NodeSocketVector,
    NodeSocketVectorAcceleration, NodeSocketVectorDirection, NodeSocketVectorEuler,
    NodeSocketVectorTranslation, NodeSocketVectorVelocity, NodeSocketVectorXYZ, NodeSocketVirtual
)

#import pathlib for finding current working direction for get_default_and_current_json_paths()
#and .exists in import_current_or_default_json()
import pathlib

#define globals
SHADER_EDITOR = "ShaderNodeTree"
COMPOSITOR_EDITOR = "CompositorNodeTree"
ANIMATION_NODE_EDITOR = "an_AnimationNodeTree"



class SAVEUESHADERSCRIPT_OT_save_shader_map(bpy.types.Operator):
    #default name is for Roman Noodles label
    #text is changed for other Shader Map Types
    bl_label = "Save Shader Map"
    bl_description = "Save Current Shader Map as a Preset"
    bl_idname = "saveueshaderscript.saveshadermap_operator"
    def execute(self, context):
  

        #store active/selected scene to variable
        scene = context.scene
        
        #allow access to user inputted properties through pointer
        #to properties
        savetool = scene.save_tool

        if preset_name_exist(savetool.cust_map_name):
            bpy.ops.ueshaderscript.show_message(
            message="The nodes preset name exists, please choose another name and try again.")
            return {'FINISHED'}

        area = context.area
        editor_type = area.ui_type
        
        scene = context.scene 
        #allow access to user inputted properties through pointer
        #to properties
        savetool = scene.save_tool
        
        node_editor = area
        
        tree = node_editor.spaces[0].node_tree
        
        
        #debug
        #print("context.area.spaces[0].node_tree: ", tree)
        #print("tree.nodes[0].bl_idname", tree.nodes[0].bl_idname)
        
        nodes_list, links_list, img_textures_list = nodes_to_dict(tree, savetool)
        
        #img_textures_list will be blank {} if add_image_textures is False or if no image textures should be loaded
        nodes_dict = {"nodes_list": nodes_list, "links_list": links_list, "img_textures_list": img_textures_list}
        nodes_dict["editor_type"] = editor_type
        shader_type = area.spaces[0].shader_type
        nodes_dict["shader_type"] = shader_type
        # Debug:
        # print(nodes_dict)
        JSON = nodes_dict_to_json(nodes_dict)
        selected_folder_presets = get_selected_folder_presets()
        presets = selected_folder_presets.presets
        new_preset = presets.add()
        #debug
        #print("savetool.cust_map_name:", savetool.cust_map_name)
        new_preset.name = savetool.cust_map_name
        new_preset.content = JSON
        selected_folder_presets.preset_index = len(presets) - 1
        save_pref()
        redraw_all()
        
        return {"FINISHED"}





#------------------------NODES TO DICTIONARY RELATED CODE



#by default not in a node group
def nodes_to_dict(tree, savetool, is_in_node_group = False):
    """ Actually, we construct and return a List """
    if tree is not None:
        nodes = tree.nodes
    else:
        nodes = []
    nodes_list = []
    for node in nodes:
        #copy default node properties to node_dict
        node_dict = {"node_name": node.bl_idname}
        node_dict["x"] = node.location.x
        node_dict["y"] = node.location.y
        node_dict["width"] = node.width
        node_dict["width_hidden"] = node.width_hidden
        node_dict["height"] = node.height

        #debug
        #print("node dict after basic node properties:", node_dict)
        
        #copy node parents means which frames
        #each node belongs to to node_dict
        parent = node.parent
        if parent == None:
            node_dict["parent"] = "None"
        else:
            parent_index = get_node_index(nodes, parent)
            node_dict["parent"] = parent_index  
        
        #copy node attributes to node_dict
        #dir() returns all properties and methods of 
        #the specified object, without the values.
        attrs = dir(node)
        attrs_list = []
        
        for attr in attrs:
            attr_dict = attr_to_dict(node, attr)
            if attr_dict["type_name"] == "NoneType" \
                    or attr_dict["type_name"] == "Not Handle Type":
                continue
            attrs_list.append(attr_dict)
        node_dict["attrs"] = attrs_list
        #debug
        #print("node dict after attrs:", node_dict)
        
        #copy node inputs and output values and types to node_dict
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
        #debug
        #print("node dict after inputs outputs:", node_dict)
        

        # Special handling ShaderNodeGroup
        # this is for recording node groups
        if node.bl_idname == "ShaderNodeGroup":
            node_dict["node_tree"] = nodes_to_dict_handle_shader_node_group(
                node, savetool)

        ### ignore as we only need to use the Shader Editor none of the other editors
#        if node.bl_idname == "CompositorNodeGroup":
#            node_dict["node_tree"] = nodes_to_dict_handle_compositor_node_group(
#                node)
#        if node.bl_idname == "CompositorNodeOutputFile":
#            # We just handle OutputFile->file_slots, does not handle layer_slots (Waiting for bugs)
#            node_dict["file_slots"] = nodes_to_dict_handle_compositor_node_output_file(
#                node)
#            # We treat all file slot's file format as the same of OutputFile->format->file_format
#            node_dict["file_format"] = node.format.file_format

        nodes_list.append(node_dict)
    #debug
    #print("full node_dict:", node_dict)
    #print("\n\nfull nodes_list", nodes_list)
    #print("\n\nfull nodes_list length", len(nodes_list))
    
    #record all links in a python list
    links_list = links_to_list(tree)
    
    #debug
    #print("\n\nlinks_list", links_list)
    
    #if the option to load image textures is true then record
    #what image texture suffixes and node names the user has written 
    #only record textures to list if not in a node group
    if(savetool.is_add_img_textures == True and not is_in_node_group):
        nodes = tree.nodes
        img_textures_list = textures_to_list(savetool, nodes)
    else:
        img_textures_list = []

    if(is_in_node_group):
        return (nodes_list, links_list)
    else:
        return (nodes_list, links_list, img_textures_list)

def socket_to_dict_output(output):
    return socket_to_dict_input(output)

def socket_to_dict_input(input):
    t = type(input)
    dict = {}
    if t == NodeSocketColor:
        dict["type_name"] = "NodeSocketColor"
        dict["value"] = list(input.default_value)
    elif t == NodeSocketFloatFactor:
        dict["type_name"] = "NodeSocketFloatFactor"
        dict["value"] = input.default_value
    elif t == NodeSocketVector or t == NodeSocketVectorDirection or \
            t == NodeSocketVectorEuler or t == NodeSocketVectorTranslation or \
            t == NodeSocketVectorVelocity or t == NodeSocketVectorXYZ:
        dict["type_name"] = "NodeSocketVector"
        dict["value"] = list(input.default_value)
    elif t == NodeSocketBool:
        dict["type_name"] = "NodeSocketBool"
        if input.default_value == True:
            value = 1
        else:
            value = 0
        dict["value"] = value
    elif t == NodeSocketFloat:
        dict["type_name"] = "NodeSocketFloat"
        dict["value"] = input.default_value
    elif t == NodeSocketFloatAngle:
        dict["type_name"] = "NodeSocketFloatAngle"
        dict["value"] = input.default_value
    elif t == NodeSocketFloatPercentage:
        dict["type_name"] = "NodeSocketFloatPercentage"
        dict["value"] = input.default_value
    elif t == NodeSocketFloatTime:
        dict["type_name"] = "NodeSocketFloatTime"
        dict["value"] = input.default_value
    elif t == NodeSocketFloatUnsigned:
        dict["type_name"] = "NodeSocketFloatUnsigned"
        dict["value"] = input.default_value
    elif t == NodeSocketInt:
        dict["type_name"] = "NodeSocketInt"
        dict["value"] = input.default_value
    elif t == NodeSocketIntFactor:
        dict["type_name"] = "NodeSocketIntFactor"
        dict["value"] = input.default_value
    elif t == NodeSocketIntPercentage:
        dict["type_name"] = "NodeSocketIntPercentage"
        dict["value"] = input.default_value
    elif t == NodeSocketIntUnsigned:
        dict["type_name"] = "NodeSocketIntUnsigned"
        dict["value"] = input.default_value
    elif t == NodeSocketString:
        dict["type_name"] = "NodeSocketString"
        dict["value"] = input.default_value
    elif t == NodeSocketVector:
        dict["type_name"] = "NodeSocketVector"
        dict["value"] = list(input.default_value)
    elif t == NodeSocketVectorAcceleration:
        dict["type_name"] = "NodeSocketVectorAcceleration"
        dict["value"] = list(input.default_value)
    elif t == NodeSocketShader:
        dict["type_name"] = "NodeSocketShader"
    elif t == NodeSocketVirtual:
        dict["type_name"] = "NodeSocketVirtual"
    else:
        log("socket_to_dict_input() can not handle input type: %s" % t)
        raise ValueError(
            "socket_to_dict_input() can not handle input type: %s" % t)
    dict["name"] = input.name
    return dict



def get_node_index(nodes, node):
    index = 0
    for n in nodes:
        if n == node:
            return index
        index += 1
    return "None"

def attr_to_dict(node, attr):
    dict = {}
    if not is_default_attr(attr):
        t = type(getattr(node, attr))
        v = getattr(node, attr)
        if v == None:
            dict["type_name"] = "NoneType"
        elif t == str:
            dict["type_name"] = "str"
            dict["value"] = getattr(node, attr)
        elif t == int:
            dict["type_name"] = "int"
            dict["value"] = getattr(node, attr)
        elif t == float:
            dict["type_name"] = "float"
            dict["value"] = getattr(node, attr)
        elif t == bool:
            dict["type_name"] = "bool"
            if getattr(node, attr) == True:
                value = 1
            else:
                value = 0
            dict["value"] = value
        elif t == list:
            dict["type_name"] = "list"
            dict["value"] = getattr(node, attr)
        elif t == tuple:
            dict["type_name"] = "tuple"
            dict["value"] = list(getattr(node, attr))
        elif t == Vector:
            dict["type_name"] = "Vector"
            dict["value"] = list(getattr(node, attr).to_tuple())
        elif t == Euler:
            dict["type_name"] = "Euler"
            value = getattr(node, attr)
            dict["value"] = list(value[:])
        elif t == Text:
            dict["type_name"] = "Text"
            value = getattr(node, attr)
            dict["value"] = value.name
        elif t == ColorMapping:
            dict["type_name"] = "NoneType"
        elif t == Image:
            dict["type_name"] = "Image"
            image = getattr(node, attr)
            dict["value"] = image.name
            dict["image_filepath"] = image.filepath
            dict["image_source"] = image.source
        elif t == Object:
            dict["type_name"] = "Object"
            value = getattr(node, attr)
            dict["value"] = value.name
        elif t == ImageUser:
            dict["type_name"] = "ImageUser"
            image_user = getattr(node, attr)
            value = get_value_from_ImageUser(image_user)
            dict["value"] = value
        elif t == ParticleSystem:
            dict["type_name"] = "ParticleSystem"
            value = getattr(node, attr)
            dict["value"] = value.name
            dict["object_name"] = bpy.context.object.name
        elif t == CurveMapping:
            dict["type_name"] = "CurveMapping"
            dict["value"] = get_value_from_CurveMapping(getattr(node, attr))
        elif t == Color:
            dict["type_name"] = "Color"
            value = getattr(node, attr)
            dict["value"] = list(value)
        elif t == ColorRamp:
            dict["type_name"] = "ColorRamp"
            color_ramp = getattr(node, attr)
            color_ramp_dict = {}
            color_ramp_dict["color_mode"] = color_ramp.color_mode
            color_ramp_dict["hue_interpolation"] = color_ramp.hue_interpolation
            color_ramp_dict["interpolation"] = color_ramp.interpolation
            elements = []
            for ele in color_ramp.elements:
                color_ramp_element = {}
                color_ramp_element["alpha"] = ele.alpha
                color_ramp_element["color"] = list(ele.color)
                color_ramp_element["position"] = ele.position
                elements.append(color_ramp_element)
            color_ramp_dict["elements"] = elements
            dict["value"] = color_ramp_dict
        else:
            dict["type_name"] = "NoneType"
            log("attr_to_dict() can not handle attr type: %s attr:%s" % (t, attr))
            # We don't raise error because some type no need to handle, and
            # it works well for restore
            #raise ValueError("attr_to_dict() can not handle attr type: %s" % t)
    else:
        dict["type_name"] = "Not Handle Type"
    dict["attr_name"] = attr
    return dict



def get_value_from_CurveMapping(curve_mapping):
    def get_curve_points(curve):
        ret = []
        for p in curve.points:
            point_dict = {}
            point_dict["handle_type"] = p.handle_type
            point_dict["location"] = list(p.location)
            ret.append(point_dict)
        return ret

    dict = {}
    dict["black_level"] = list(curve_mapping.black_level)
    dict["clip_max_x"] = curve_mapping.clip_max_x
    dict["clip_max_y"] = curve_mapping.clip_max_y
    dict["clip_min_x"] = curve_mapping.clip_min_x
    dict["clip_min_y"] = curve_mapping.clip_min_y
    dict["tone"] = curve_mapping.tone
    dict["use_clip"] = curve_mapping.use_clip
    dict["white_level"] = list(curve_mapping.white_level)
    curves = []
    for curve in curve_mapping.curves:
        curve_dict = {}
        #curve_dict["extend"] = curve.extend
        set_attr_if_exist_for_dict(curve, "extend", curve_dict)
        curve_dict["points"] = get_curve_points(curve)
        curves.append(curve_dict)
    dict["curves"] = curves
    return dict

def set_attr_if_exist_for_dict(obj, attr, dict):
    if hasattr(obj, attr):
        dict[attr] = getattr(obj, attr)
    else:
        dict[attr] = "None"

def get_value_from_ImageUser(image_user):
    dict = {}
    dict["frame_current"] = image_user.frame_current
    dict["frame_duration"] = image_user.frame_duration
    dict["frame_offset"] = image_user.frame_offset
    dict["frame_start"] = image_user.frame_start
    dict["use_cyclic"] = image_user.use_cyclic
    dict["use_auto_refresh"] = image_user.use_auto_refresh
    return dict


def get_value_from_ColorMapping(color_mapping):
    dict = {}
    dict["blend_color"] = list(color_mapping.blend_color)
    dict["blend_factor"] = color_mapping.blend_factor
    dict["blend_type"] = color_mapping.blend_type
    dict["brightness"] = color_mapping.brightness
    dict["contrast"] = color_mapping.contrast
    dict["saturation"] = color_mapping.saturation
    dict["use_color_ramp"] = color_mapping.use_color_ramp
    return dict




def is_default_attr(attr):
    if attr in get_default_attrs():
        return True
    else:
        return False


def get_default_attrs():
    # `codeEffects` is a value which can not be JSONify in KDTree (Animation Node)
    return ['__doc__', '__module__', '__slots__', 'bl_description',
            'bl_height_default',
            'bl_height_max', 'bl_height_min', 'bl_icon', 'bl_idname',
            'bl_label', 'bl_rna', 'bl_static_type', 'bl_width_default',
            'bl_width_max', 'bl_width_min', 'dimensions',
            'draw_buttons', 'draw_buttons_ext', 'height',
            'input_template', 'inputs', 'internal_links', 'is_active_output',
            'is_registered_node_type', 'location', 'mute',
            'output_template', 'outputs', 'parent', 'poll', 'poll_instance',
            'rna_type', 'select', 'show_options', 'show_preview',
            'show_texture', 'socket_value_update', 'type', 'update',
            'width', 'width_hidden',
            'codeEffects'
            ]

#this is to handle node groups
def nodes_to_dict_handle_shader_node_group(node, savetool):
    node_tree_of_node_group = node.node_tree
    inputs = node_tree_of_node_group.inputs
    interface_inputs_list = interface_inputs_to_list(inputs)
    node_tree_dict = {}
    node_tree_dict["interface_inputs"] = interface_inputs_list
    node_tree_dict["name"] = node_tree_of_node_group.name
    
    #set in node group bool to true
    is_in_node_group = True
    nodes_list, links_list = nodes_to_dict(node_tree_of_node_group, savetool, is_in_node_group)
    node_tree_dict["nodes_list"] = nodes_list
    node_tree_dict["links_list"] = links_list
    return node_tree_dict

def interface_inputs_to_list(inputs):
    inputs_list = []
    for input in inputs:
        if hasattr(input, "min_value"):
            min_value = input.min_value
        else:
            min_value = "None"
        if hasattr(input, "max_value"):
            max_value = input.max_value
        else:
            max_value = "None"
        dict = {"min_value": min_value, "max_value": max_value}
        inputs_list.append(dict)
    return inputs_list

def links_to_list(tree):
    if tree is None:
        links = []
        nodes = []
    else:
        links = tree.links
        nodes = tree.nodes
    links_list = []
    for link in links:
        link_dict = {}
        for node_index, n in enumerate(nodes):
            inputs = n.inputs
            outputs = n.outputs
            for index, o in enumerate(outputs):
                if link.from_socket == o:
                    link_dict["from_node_index"] = node_index
                    link_dict["from_socket_index"] = index
                    link_dict["from_socket_name"] = o.name
            for index, i in enumerate(inputs):
                if link.to_socket == i:
                    link_dict["to_node_index"] = node_index
                    link_dict["to_socket_index"] = index
                    link_dict["to_socket_name"] = i.name
        links_list.append(link_dict)
    return links_list

def textures_to_list(savetool, nodes):
    #nested function so that don't have to pass lists around
    #nested functions can access parent function's variables
    def suffix_and_node_name_to_list(suffix, node_name, texture):
        img_textures_dict = {}
        
        #if both the suffix and suffix node are not empty
        #record the suffix in the dictionary
        if suffix != "" and node_name != "":

            #try get the node by node name
            #if it does not exist 
            #do not let it be recorded in the img_textures_dict or img_textures_list
            #because we don't want to record 
            #img textures that will never get loaded
            #debug
            #print("node_name:", node_name)
            node = nodes.get(node_name, None)
            
            #print("node:", node, "\n")

            #by default assume node with suffix node name does not exist
            is_node_with_node_name_exist = False

            if (node != None):
                is_node_with_node_name_exist = True
            else:
                #notify user if their
                #Shader Map did not have a Node with the correctly named Node Name
                #two brackets inner brackets converts to tuple .join needs a tuple
                warning_message = "".join(("A node with Node Name: \"", node_name, "\" does not exist so the ", texture, " texture was not recorded to load!"))
                bpy.ops.ueshaderscript.show_message(message = warning_message)
            
            #only record in the img_textures_dict and img_textures_list if the node exists
            #in the current shader setup
            if is_node_with_node_name_exist:
                #texture is for debugging purposes so can check JSON file
                #but it is also used to uniquely identify a 
                #specific marked image texture node
                #this is because both suffix and node_name can be changed
                #but texture is always the same
                img_textures_dict["texture"] = texture
                img_textures_dict["node_name"] = node_name
                #for the suffix property the rules are 
                #every suffix should be separated by a space
                #so we are separating every suffix with .split()
                #.split generates a list so no need for extra square brackets
                #around suffix.split(" ")
                suffix_list = suffix.split(" ")
                img_textures_dict["suffix_list"] = suffix_list

        #if node name is missing but suffix is there
        #special case to avoid skin texture because
        #the default is always missing the Node Name
        #since it only needs a Node Name
        elif suffix != "" and node_name == "" and texture != "skin":
            #notify user if they
            #did not fill in both the suffix and the node name
            warning_message = "".join(("The Node Name input is missing for texture: \"", texture, "\" so the texture was not recorded to load!"))
            bpy.ops.ueshaderscript.show_message(message = warning_message)
        
        #if suffix is missing but node name is there
        elif suffix == "" and node_name != "":
            #notify user if they
            #did not fill in both the suffix and the node name
            warning_message = "".join(("The Suffix input is missing for texture: \"", texture, "\" so the texture was not recorded to load!"))
            bpy.ops.ueshaderscript.show_message(message = warning_message)

        #if the suffix and node name is missing then this is the default state
        #so no warning message needs to be shown

        #if an entry was added into the img_textures_dict 
        #append it to the list
        #otherwise don't append anything to the list
        if img_textures_dict != {}:
            img_textures_list.append(img_textures_dict)
        #-------------------------------end of nested function




    img_textures_list = []
    suffix_and_node_name_to_list(savetool.bc_suffix, savetool.bc_node_name, "diffuse")
    suffix_and_node_name_to_list(savetool.orm_suffix, savetool.orm_node_name, "packed_orm")
    suffix_and_node_name_to_list(savetool.n_suffix, savetool.n_node_name, "normal")
    suffix_and_node_name_to_list(savetool.m_suffix, savetool.m_node_name, "transparency")
    suffix_and_node_name_to_list(savetool.bde_suffix, savetool.bde_node_name, "emissive")
    suffix_and_node_name_to_list(savetool.hm_suffix, savetool.hm_node_name, "height")
    suffix_and_node_name_to_list(savetool.hair_gradient_suffix, savetool.hair_gradient_node_name, "hair_gradient")
    suffix_and_node_name_to_list(savetool.specular_suffix, savetool.specular_node_name, "specular")
    suffix_and_node_name_to_list(savetool.gloss_suffix, savetool.gloss_node_name, "gloss")

    #skin texture is always added and is found from the user chosen path 
    suffix_and_node_name_to_list("Not/Applicable", savetool.skin_node_name, "skin")
    suffix_and_node_name_to_list(savetool.cust1_suffix, savetool.cust1_node_name, "cust1")
    suffix_and_node_name_to_list(savetool.cust2_suffix, savetool.cust2_node_name, "cust2")
    suffix_and_node_name_to_list(savetool.cust3_suffix, savetool.cust3_node_name, "cust3")
    suffix_and_node_name_to_list(savetool.cust4_suffix, savetool.cust4_node_name, "cust4")

   
    #if the img_textures list is empty
    #that is equivalent to having 
    #no image textures to load

    #debug
    #print("img_textures_list: ", img_textures_list)
    #print("img_textures_list length: ", len(img_textures_list))
    
    return img_textures_list





#---------------------------Panel related code including preset and folder new , deletion, renaming 
#define all user input properties
class SaveProperties(bpy.types.PropertyGroup):
    cust_map_name: bpy.props.StringProperty(name="Name of Shader Map", description="Name of your custom shader map")
    bc_suffix: bpy.props.StringProperty(name="Diffuse Suffix", description="Suffix of Diffuse", default="_BC _BC_01 _BC_02 _BC_03 _BC_04")
    bc_node_name: bpy.props.StringProperty(name="Diffuse Node Name", description="Diffuse image texture node name", default="Diffuse Node")
    orm_suffix: bpy.props.StringProperty(name="Packed RGB ARM Suffix", description="Suffix of Packed RGB (AO, Rough, Metallic)", default="_ORM")
    orm_node_name: bpy.props.StringProperty(name="Packed RGB Node Name", description="Packed RGB image texture node name", default="Packed RGB Node")
    n_suffix: bpy.props.StringProperty(name="Normal Map Suffix", description="Suffix of Normal Map", default="_N")
    n_node_name: bpy.props.StringProperty(name="Normal Map Node Name", description="Normal Map image texture node name", default="Normal Map Node")
    m_suffix: bpy.props.StringProperty(name="Alpha Map Suffix", description="Suffix of Alpha (Transparency) Map", default="_M _A")
    m_node_name: bpy.props.StringProperty(name="Alpha Map Node Name", description="Alpha Map image texture node name", default="Transparency Map Node")
    bde_suffix: bpy.props.StringProperty(name="Emissions Map Suffix", description="Suffix of Emissions Map", default="_BDE _BDE_EventGlowEyes _BDE_02 _BDE_PW01 _BDE_Eye")
    bde_node_name: bpy.props.StringProperty(name="Emissions Map Node Name", description="Emissions Map image texture node name", default="Emissions Map Node")
    hm_suffix: bpy.props.StringProperty(name="Height Map Suffix", description="Suffix of Height Map", default="")
    hm_node_name: bpy.props.StringProperty(name="Height Map Node Name", description="Height Map image texture node name", default="")
    hair_gradient_suffix: bpy.props.StringProperty(name="Hair Gradient Map Suffix", description="Suffix of Hair Gradient Map", default="")
    hair_gradient_node_name: bpy.props.StringProperty(name="Hair Gradient Map Node Name", description="Hair Gradient Map image texture node name", default="")
    specular_suffix: bpy.props.StringProperty(name="Specular Map Suffix", description="Suffix of Specular Map", default="")
    specular_node_name: bpy.props.StringProperty(name="Specular Map Node Name", description="Specular Map image texture node name", default="")
    gloss_suffix: bpy.props.StringProperty(name="Gloss Map Suffix", description="Suffix of Gloss Map", default="")
    gloss_node_name: bpy.props.StringProperty(name="Gloss Map Node Name", description="Gloss Map image texture node name", default="")

    is_show_custom_textures: bpy.props.BoolProperty(name="Show Custom Suffix and Node Names", default= False)
    cust1_suffix: bpy.props.StringProperty(name="Custom1 Suffix", description="Suffix of Custom1 Texture", default="")
    cust1_node_name: bpy.props.StringProperty(name="Custom1 Node Name", description="Custom1 image texture node name", default="")
    cust2_suffix: bpy.props.StringProperty(name="Custom2 Suffix", description="Suffix of Custom2 Texture", default="")
    cust2_node_name: bpy.props.StringProperty(name="Custom2 Node Name", description="Custom2 image texture node name", default="")
    cust3_suffix: bpy.props.StringProperty(name="Custom3 Suffix", description="Suffix of Custom3 Texture", default="")
    cust3_node_name: bpy.props.StringProperty(name="Custom3 Node Name", description="Custom3 image texture node name", default="")
    cust4_suffix: bpy.props.StringProperty(name="Custom4 Suffix", description="Suffix of Custom4 Texture", default="")
    cust4_node_name: bpy.props.StringProperty(name="Custom4 Node Name", description="Custom4 image texture node name", default="")

    #skin only needs a node name as it is not from the game files
    #rather it is externally added by the user themself
    skin_node_name: bpy.props.StringProperty(name="Skin Node Name", description="Skin image texture node name", default="")
    is_add_img_textures: bpy.props.BoolProperty(name="Load Image Textures to Shader Map Dynamically", default= True)
    
    #enum property for using default suffixes
    default_suffix_enum: bpy.props.EnumProperty(
        name = "(Optional) Suffix/Node Name Preset to Use",
        description = "Default Suffix Type",
        items = 
        [
            ("DBD_GENERAL" , "DBD Generic/Basic", ""),
            ("DBD_SKIN", "DBD Skin", ""),
            ("DBD_HAIR" , "DBD Hair", "")
        ]
        
    )



#----------------code for drawing main panel in the 3D View
#don't register this class it is not a bpy panel or type so
#it does not need to be registered
class SAVEUESHADERSCRIPT_shared_main_panel:
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Save UE Shaders"

    #so poll only allows the draw
    #and execute function to work if
    #poll function returns True
    #so in this case only draw a panel
    #if the current window is the Shader Editor window
    #NOT the compositor view
    #because the plugin only saves shader editor shader maps
    @classmethod
    def poll(self, context):
        return context.area.ui_type == "ShaderNodeTree"

#main panel 1
#inheriting the shared panel's bl_space_type, bl_region_type and bl_category
#and poll function
class SAVEUESHADERSCRIPT_PT_manage_presets_main_panel_1(SAVEUESHADERSCRIPT_shared_main_panel, bpy.types.Panel):
    bl_label = "Manage Presets"
    bl_idname = "SAVEUESHADERSCRIPT_PT_manage_presets_main_panel_1"
    
    def draw(self, context):
        layout = self.layout

        preferences = get_preferences()
        #make folder section
        box = layout.box()
        row = box.row()
        row.label(text="Folders")
        row = box.row()
        left = row.column()
        left.alignment = "RIGHT"
        left.prop(preferences, 'folders', expand=False)
        right = row.column()
        right.alignment = "LEFT"
        right.operator("ueshaderscript.folder_actions", text="", icon="MENU_PANEL")

        selected_folders_presets = get_selected_folder_presets()
        layout.label(text = "Your presets")
        row = layout.row()
        left, right = get_two_column(self, row, factor=0.7)
        #create the list of current presets
        left.template_list("SHADER_PRESETS_UL_items", "", selected_folders_presets,
                               "presets", selected_folders_presets, "preset_index", rows=5)
        col1 = right.row().column(align=True)
        col1.operator("ueshaderscript.remove_preset",
                        text="Remove", icon="REMOVE")
        col1.operator("ueshaderscript.rename_preset",
                          text="Rename", icon="GREASEPENCIL")
        col1.operator("ueshaderscript.move_preset",
                        text="Move To...", icon="FILE_FOLDER")
        col2 = right.row().column(align=True)
        col2.operator("ueshaderscript.move_preset_up",
                        icon='TRIA_UP', text="Move Up")
        col2.operator("ueshaderscript.move_preset_down",
                        icon='TRIA_DOWN', text="Move Down")
        
        layout.operator("ueshaderscript.import_append_presets")
        layout.operator("ueshaderscript.export_presets")
        layout.operator("ueshaderscript.reset_update_default_presets")


#main panel 2
#inheriting the shared panel's bl_space_type, bl_region_type and bl_category
#and poll function
class SAVEUESHADERSCRIPT_PT_save_custom_preset_main_panel_2(SAVEUESHADERSCRIPT_shared_main_panel, bpy.types.Panel):
    bl_label = "Save a Custom Shader Map"
    bl_idname = "SAVEUESHADERSCRIPT_PT_save_custom_preset_main_panel_2"

    def draw(self, context):
        layout = self.layout

        #store active/selected scene to variable
        scene = context.scene
        
        #allow access to user inputted properties through pointer
        #to properties
        savetool = scene.save_tool

        layout.prop(savetool, "cust_map_name")
        layout.prop(savetool, "is_add_img_textures")

        #formatting
        #layout.use_property_split means that it will try and display 
        #the property fully
        layout.use_property_split = True

        #don't show the keyframe button next to animateable properties
        #such as the Bool Property
        layout.use_property_decorate = False
        
        if (savetool.is_add_img_textures == True):
            box = layout.box()
            box.label(text = "Image Texture Suffixes and Node Names")
            box.label(text = "(leave suffix and node name empty if you do NOT want to load the specific image texture)")
            box.label(text = "Node Names can be found/changed by selecting an image texture node > Press n > Item > Name")
            box.label(text = "Separate different suffixes with a single space")
            box.prop(savetool, "default_suffix_enum")
            box.operator("saveueshaderscript.load_default_suffixes_operator")
            box.prop(savetool, "bc_suffix")
            box.prop(savetool, "bc_node_name")
            box.prop(savetool, "orm_suffix")
            box.prop(savetool, "orm_node_name")
            box.prop(savetool, "n_suffix")
            box.prop(savetool, "n_node_name")
            box.prop(savetool, "m_suffix")
            box.prop(savetool, "m_node_name")
            box.prop(savetool, "bde_suffix")
            box.prop(savetool, "bde_node_name")
            box.prop(savetool, "hm_suffix")
            box.prop(savetool, "hm_node_name")
            box.prop(savetool, "hair_gradient_suffix")
            box.prop(savetool, "hair_gradient_node_name")
            box.prop(savetool, "specular_suffix")
            box.prop(savetool, "specular_node_name")
            box.prop(savetool, "gloss_suffix")
            box.prop(savetool, "gloss_node_name")
    
            box.prop(savetool, "is_show_custom_textures")
            if(savetool.is_show_custom_textures == True):
                box.prop(savetool, "cust1_suffix")
                box.prop(savetool, "cust1_node_name")
                box.prop(savetool, "cust2_suffix")
                box.prop(savetool, "cust2_node_name")
                box.prop(savetool, "cust3_suffix")
                box.prop(savetool, "cust3_node_name")
                box.prop(savetool, "cust4_suffix")
                box.prop(savetool, "cust4_node_name")

            row = box.row()

            box.label(text = "Skin Texture Node (Special Case No Suffix)")
            box.label(text = "Skin Texture Height Map is always added regardless of the props.txt files")
            box.prop(savetool, "skin_node_name")
            box.operator("SAVEUESHADERSCRIPT.reset_inputs_main_panel_operator")
        
        layout.operator("SAVEUESHADERSCRIPT.saveshadermap_operator")


#this class is the list to be displayed in the main panel
class SHADER_PRESETS_UL_items(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        row = layout.row()
        custom_icon = "NODE"
        row.label(text=item.name, icon=custom_icon)

    def invoke(self, context, event):
        pass

class SHADER_MT_FolderActionsMenu(bpy.types.Menu):
    bl_label = ""
    bl_idname = "SHADER_MT_FolderActionsMenu"

    def draw(self, context):
        layout = self.layout
        # https://docs.blender.org/api/current/bpy.types.Menu.html
        # https://docs.blender.org/api/current/bpy.ops.html#operator-execution-context
        # This fix below operators not working properly
        layout.operator_context = 'INVOKE_DEFAULT'
        row = layout.row()
        row.operator("ueshaderscript.new_folder", text="Add New Folder", icon="ADD")
        row = layout.row()
        row.operator("ueshaderscript.remove_folder",
                     text="Remove Selected Folder", icon="REMOVE")
        row = layout.row()
        row.operator("ueshaderscript.rename_folder",
                     text="Rename Selected Folder", icon="EVENT_R")


class Shader_ShowFolderActionsOperator(bpy.types.Operator):
    bl_idname = "ueshaderscript.folder_actions"
    bl_label = ""
    bl_description = "Show Message for Node Kit"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        bpy.ops.wm.call_menu(name="SHADER_MT_FolderActionsMenu")
        return {'FINISHED'}


class Shader_NewFolderOperator(bpy.types.Operator):
    bl_idname = "ueshaderscript.new_folder"
    bl_label = "New Folder"
    bl_description = "New Folder"
    folder_name: bpy.props.StringProperty(name="")

    @classmethod
    def poll(cls, context):
        return True

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        left, right = get_two_column(self, row)
        left.label(text="New Folder Name:")
        right.prop(self, "folder_name")

    def execute(self, context):
        if folder_name_exist(self.folder_name):
            bpy.ops.ueshaderscript.show_message(
                message="The folder name exists, please choose another name and try again.")
            return {'FINISHED'}
        pref = get_preferences()
        new_folder_presets = pref.folders_presets.add()
        new_folder_presets.folder_name = self.folder_name
        index = len(pref.folders_presets) - 1
        pref.folders = "%d" % index
        save_pref()
        redraw_all()
        return {'FINISHED'}

    def invoke(self, context, event):
        suggested_name = suggested_folder_name()
        self.folder_name = suggested_name
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=300)

#buttons for changing preset order renaming and moving presets between folders

class RenamePresetOperator(bpy.types.Operator):
    bl_idname = "ueshaderscript.rename_preset"
    bl_label = "Rename Preset"
    bl_description = "Rename Preset"
    bl_options = {'REGISTER'}
    preset_name: bpy.props.StringProperty(name="")

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        selected_folder_presets = get_selected_folder_presets()
        index = selected_folder_presets.preset_index
        if index < 0:
            bpy.ops.ueshaderscript.show_message(
                message="Please choose a nodes preset to rename.")
            return {'FINISHED'}
        preset = selected_folder_presets.presets[index]
        self.preset_name = preset.name
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        left, right = get_two_column(self, row)
        left.label(text="New Preset Name:")
        right.prop(self, "preset_name")

    def execute(self, context):
        selected_folder_presets = get_selected_folder_presets()
        index = selected_folder_presets.preset_index
        if index < 0:
            return {'FINISHED'}
        if preset_name_exist(self.preset_name):
            bpy.ops.ueshaderscript.show_message(
                message="The nodes preset name exists, please choose another name and try again.")
            return {'FINISHED'}
        preset = selected_folder_presets.presets[index]
        preset.name = self.preset_name
        save_pref()
        redraw_all()
        return {'FINISHED'}


class MovePresetUpOperator(bpy.types.Operator):
    bl_idname = "ueshaderscript.move_preset_up"
    bl_label = "Move Selected Preset Up"
    bl_description = "Move Selected Preset Up"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        move_preset_up()
        save_pref()
        redraw_all()
        return {'FINISHED'}

def move_preset_up():
    selected_folder_presets = get_selected_folder_presets()
    up_preset = selected_folder_presets.preset_index - 1
    if up_preset >= 0:
        exchange_preset(selected_folder_presets.preset_index, up_preset)
        selected_folder_presets.preset_index -= 1

def exchange_preset(a, b):
    selected_folder_presets = get_selected_folder_presets()
    selected_folder_presets.presets.move(a, b)

class MovePresetDownOperator(bpy.types.Operator):
    bl_idname = "ueshaderscript.move_preset_down"
    bl_label = "Move Selected Preset Down"
    bl_description = "Move Selected Preset Down"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        move_preset_down()
        save_pref()
        redraw_all()
        return {'FINISHED'}

def move_preset_down():
    selected_folder_presets = get_selected_folder_presets()
    down_preset = selected_folder_presets.preset_index + 1
    if down_preset <= len(selected_folder_presets.presets) - 1:
        exchange_preset(selected_folder_presets.preset_index, down_preset)
        selected_folder_presets.preset_index += 1


def get_folders_items(self, context):
    pref = get_preferences()
    enum_types_items = []
    for index, folder_preset in enumerate(pref.folders_presets):
        enum_types_items.append(("%d" % index, folder_preset.folder_name, ""))
    return tuple(enum_types_items)


class MovePresetOperator(bpy.types.Operator):
    bl_idname = "ueshaderscript.move_preset"
    bl_label = "Move Selected Preset to Folder"
    bl_description = "Move Selected Preset to Folder"
    bl_options = {'REGISTER'}

    folders: EnumProperty(name="",
                          description="",
                          items=get_folders_items,
                          update=None,
                          default=None)

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(self, 'folders', expand=False)

    def execute(self, context):
        selected_folder_presets = get_selected_folder_presets()
        selected_preset = get_selected_preset()
        if selected_preset is None:
            bpy.ops.ueshaderscript.show_message(message="No preset selected")
            return {'FINISHED'}
        target_folder = get_folder_presets_by_index(self.folders)
        if preset_name_exist_in_folder(target_folder.folder_name, selected_preset.name):
            bpy.ops.ueshaderscript.show_message(
                message="The nodes preset name exists in target folder, please rename it and try again.")
            return {'FINISHED'}
        target_folder_presets = target_folder.presets
        new_preset = target_folder_presets.add()
        new_preset.name = selected_preset.name
        new_preset.content = selected_preset.content
        selected_folder_presets.presets.remove(
            int(selected_folder_presets.preset_index))
        save_pref()
        redraw_all()
        return {'FINISHED'}





def get_folder_presets_by_index(index):
    pref = get_preferences()
    folder_presets = pref.folders_presets
    return folder_presets[int(index)]


#--------------------check if preset or folder name exists
def preset_name_exist(name):
    selected_folder_presets = get_selected_folder_presets()
    presets = selected_folder_presets.presets
    for preset in presets:
        if name == preset.name:
            return True
    return False


def folder_name_exist(name):
    pref = get_preferences()
    folder_presets = pref.folders_presets
    for folder_preset in folder_presets:
        if name == folder_preset.folder_name:
            return True
    return False

def preset_name_exist_in_folder(folder_name, preset_name):
    pref = get_preferences()
    folders_presets = pref.folders_presets
    for folder in folders_presets:
        if folder.folder_name == folder_name:
            for preset in folder.presets:
                if preset.name == preset_name:
                    return True
    return False


def suggested_preset_name():
    name = "preset"
    index = 1
    suggested_name = "%s %d" % (name, index)
    while preset_name_exist(suggested_name):
        index += 1
        suggested_name = "%s %d" % (name, index)
    return suggested_name


def suggested_folder_name():
    name = "folder"
    index = 1
    suggested_name = "%s %d" % (name, index)
    while folder_name_exist(suggested_name):
        index += 1
        suggested_name = "%s %d" % (name, index)
    return suggested_name

#----check if preset or folder name exists end


class Shader_RemoveFolderOperator(bpy.types.Operator):
    bl_idname = "ueshaderscript.remove_folder"
    bl_label = "Do you really want to remove selected folder?"
    bl_description = "Remove Folder"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        pref = get_preferences()
        selected_folder = pref.folders
        remove_folder(selected_folder)
        save_pref()
        redraw_all()
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

def remove_folder(selected_folder_index):
    pref = get_preferences()
    folder_presets = pref.folders_presets
    for index, folder_preset in enumerate(folder_presets):
        if index == int(selected_folder_index):
            folder_presets.remove(index)
            l = len(pref.folders_presets) - 1
            if l >= 0:
                pref.folders = "%d" % l
            break

class Shader_RenameFolderOperator(bpy.types.Operator):
    bl_idname = "ueshaderscript.rename_folder"
    bl_label = "Rename Folder"
    bl_description = "Rename Folder"
    bl_options = {'REGISTER'}
    folder_name: bpy.props.StringProperty(name="")

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        pref = get_preferences()
        selected_folder_index = pref.folders
        folder_name = get_folder_name(selected_folder_index)
        self.folder_name = folder_name
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        left, right = get_two_column(self, row)
        left.label(text="New Folder Name:")
        right.prop(self, "folder_name")

    def execute(self, context):
        pref = get_preferences()
        if folder_name_exist(self.folder_name):
            bpy.ops.ueshaderscript.show_message(
                message="The folder name exists, please choose another name and try again.")
            return {'FINISHED'}
        selected_folder_index = pref.folders
        new_folder_name = self.folder_name
        print("index: ", selected_folder_index,
              " new folder name:", new_folder_name)
        rename_folder(selected_folder_index, new_folder_name)
        save_pref()
        redraw_all()
        return {'FINISHED'}

def rename_folder(selected_folder_index, new_folder_name):
    pref = get_preferences()
    folder_presets = pref.folders_presets
    for index, folder_preset in enumerate(folder_presets):
        if index == int(selected_folder_index):
            folder_preset.folder_name = new_folder_name


def get_folder_name(selected_folder_index):
    pref = get_preferences()
    folder_presets = pref.folders_presets
    for index, folder_preset in enumerate(folder_presets):
        if index == int(selected_folder_index):
            return folder_preset.folder_name
    return ""

#--------formatting functions for panels
def get_two_column(self, row, factor=0.5):
    splitrow = layout_split(row, factor=factor)
    left = splitrow.column()
    left.alignment = "RIGHT"
    right = splitrow.column()
    right.alignment = "LEFT"
    return (left, right)

def layout_split(layout, factor=0.0, align=False):
    """Intermediate method for pre and post blender 2.8 split UI function"""
    if not hasattr(bpy.app, "version") or bpy.app.version < (2, 80):
        return layout.split(percentage=factor, align=align)
    return layout.split(factor=factor, align=align)

#--------end formatting functions for panels

#remove preset button
class SAVEUESHADERSCRIPT_OT_remove_preset(bpy.types.Operator):
    bl_idname = "ueshaderscript.remove_preset"
    bl_label = "Do you really want to remove selected preset?"
    bl_description = "Remove Preset"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        selected_folder_presets = get_selected_folder_presets()
        index = selected_folder_presets.preset_index
        if index < 0:
            return {'FINISHED'}
        folder_name = get_selected_folder_name()
        preset_name = get_selected_preset_name()
        selected_folder_presets.presets.remove(index)
        selected_folder_presets.preset_index = len(
            selected_folder_presets.presets) - 1
        #remove_preset_from_10_last_used(folder_name, preset_name)
        #update_10_most_used_presets()
        save_pref()
        redraw_all()
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)

def get_selected_folder_name():
    pref = get_preferences()
    if pref.folders == "" or pref.folders == None:
        return None
    index = int(pref.folders)
    return pref.folders_presets[index].folder_name


def get_selected_preset_name():
    return get_selected_preset().name

def get_selected_preset():
    selected_folder_presets = get_selected_folder_presets()
    if selected_folder_presets.preset_index < 0 or \
            len(selected_folder_presets.presets) <= 0:
        return None
    return selected_folder_presets.presets[selected_folder_presets.preset_index]


#----------------------------------CONVERT TO JSON AND SAVE PRESETS RELATED CODE



def nodes_dict_to_json(nodes_dict):
    try:
        JSON = dict_to_string(nodes_dict)
    except Exception as e:
        report_error(self, str(e))
    return JSON


def json_to_nodes_dict(JSON):
    try:
        nodes_dict = json_to_dict(JSON)
    except Exception as e:
        report_error(self, str(e))
    return nodes_dict

def json_to_dict(json_string):
    """Convert JSON string into a Python dictionary"""
    return json.loads(json_string)


def dict_to_string(d):
    """Convert a Python dictionary to JSON string"""
    return json.dumps(d, indent=4)



def get_default_and_current_json_paths():
    DEFAULT_PRESETS_JSON_FILE = "ue_shader_script_default_presets_json.json"
    CURRENT_PRESETS_JSON_FILE = "ue_shader_script_current_presets_json.json"
    path_lib = pathlib.Path(__file__).parent.absolute()
    home = os.path.expanduser("~")
    #the current presets file always stores the current presets that the user has
    current_presets_full_path = os.path.join(home, CURRENT_PRESETS_JSON_FILE)

    #so default presets json file always stores the default presets that come with the plugin
    default_presets_full_path = os.path.join(path_lib, DEFAULT_PRESETS_JSON_FILE)
    #debug
    #print("current_presets_full_path: ", current_presets_full_path)
    #print("default_presets_full_path: ", default_presets_full_path)
    return current_presets_full_path, default_presets_full_path


def import_current_or_default_json():
    """Use this to import the current or default json file in ~/ue_shader_script_default_json or the plugin directory respectively"""
    current_presets_full_path, default_presets_full_path = get_default_and_current_json_paths()
    # try:
    #     with open(full_path) as f:
    #         json_string = f.read()
    #         json_string_to_presets(json_string, skip_autosave=True)
    # except IOError:
    #     print(full_path, ": file not accessible")
    
    current_presets_json_file = pathlib.Path(current_presets_full_path)
    default_presets_json_file = pathlib.Path(default_presets_full_path)
    #first try to import current_presets_full_path which will be in the home directory
    #this is because if the user created presets but deleted the add on
    #this json file in the current_presets_full_path will still be there
    #however, the json file in the plugin folder will have been deleted
    #when the plugin was uninstalled
    
    if(current_presets_json_file.exists()):
        with open(current_presets_full_path) as f:
            json_string = f.read()
            #json_string_to_presets will delete any existing presets
            json_string_to_presets(json_string, skip_autosave=True)
    else:
        log("Home directory current presets JSON File not accessible.")
        #if the current presets json file in the home directory does not exist 
        #this may be a first install of the program
        #so check the plugin folder for the default presets json file
        #and load the default presets that come with the plugin
        if(default_presets_json_file.exists()):
            with open(default_presets_full_path) as f:
                json_string = f.read()
                #json_string_to_presets will delete any existing presets
                json_string_to_presets(json_string, skip_autosave=True)
        else:
            log("Error: no JSON File was found in the Home or Plugin Folder, please send a screenshot of the error to the developer.")



# _10_LAST_USED_PRESETS_KEY = "10_last_used_presets"
# USED_KEY = "_used"

#json_string_to_presets will delete any existing presets
def json_string_to_presets(json_string, skip_autosave=False):
    dict = json_to_dict(json_string)
    #debug
    #print("dict: ", dict)
    pref = get_preferences()
    folders_presets = pref.folders_presets
    #clear all presets in folder
    folders_presets.clear()
    for key in dict:
        #Not using 10 last used functionality
        # if key == _10_LAST_USED_PRESETS_KEY:
        #     presets_list = dict[key]
        #     import_10_last_used_presets(presets_list)
        #     continue
        presets = dict[key]
        new_folder = folders_presets.add()
        new_folder.folder_name = key
        #returns instance of FolderPresetsCollection
        new_folder_presets = new_folder.presets
        #presets is a dict of all presets in a single folder
        #print("presets:", presets)
        for preset in presets:
            #debug
            #print("preset:", preset)
            #print("\n\n")

            #preset is an individual preset such as test1
            #print("preset:", preset)
            #.add is method to add an instance of a class
            new_preset = new_folder_presets.add()
            #new_preset.used = 0
            for k in preset:
                #content will be stored as a string
                #like this: "DBD Roman Noodles Skin": "{\n    \"nodes_list\": [\n        {\n ..."
                #it looks bad, but we must store it this way with \n characters because
                #it must be in a single string
                #a single string is the easiest to store in the Blender add on Preferences
                #as as bpy.types.StringProperty
                content = preset[k]
                new_preset.name = k
                new_preset.content = content
                
                #-----------Not using last used section of code
                #if the key is _used it's going to be something like 1
                #this is when it was last used
                #if k == USED_KEY:
                #    new_preset.used = preset[USED_KEY]
                #else:
                #otherwise if it is not the used key we shall decode it 
                    # content = preset[k]
                    # new_preset.name = k
                    # new_preset.content = content
                #debug
                #print("preset[k]", preset[k])
    #import_10_most_used_presets()
    save_pref(skip_autosave=skip_autosave)

def json_string_to_update_default_presets(json_string, skip_autosave=False):
    default_presets_json_dict = json_to_dict(json_string)
    #debug
    #print("json_dict['Default'][0] ", json_dict["Default"][0])
    #to get {"DBD Roman Noodles Basic": "{\n    \"nodes_list\"...."}
    
    #json_dict look like this
    # {
    #     "Default": [
    #         {
    #             "DBD Roman Noodles Basic": "{\n    \"nodes_list\"...."
    #         },
    #         {
    #             "DBD Roman Noodles Skin": "{\n    \"nodes_list\"...."
    #         }
    #     ],
    #     "folder 1:"[
    #         {
    #              "DBD Roman Noodles Basic": "{\n    \"nodes_list\"...."
    #         },
    #         {
    #              "DBD Roman Noodles Skin": "{\n    \"nodes_list\"...."
    #         }
    #     ]
    # }
    
    preferences = get_preferences()
    folders_presets = preferences.folders_presets

    #this is iterating over the json file containing all the default presets
    #NOT the preferences in userprefs.blend these are two very different things 
    #iterating over folders
    for key in default_presets_json_dict:
        presets = default_presets_json_dict[key]
        if folder_name_exist(key):
            #if the folder exists get the existing folder
            #saved in the userprefs.blend file
            #need to get_folder_presets_by_name because
            #need to retrieve the stored folder collection in userprefs.blend
            new_folder = get_folder_presets_by_name(key)
        else:
            #if the folder doesn't exist create a new one
            new_folder = folders_presets.add()
            new_folder.folder_name = key
        
        new_folder_presets = new_folder.presets
        #iterate over all the presets in the folder
        for preset in presets:
            #iterate over all values within one preset 
            #{
            #    "DBD Roman Noodles Basic": "{\n    \"nodes_list\"...."
            #}
            #this one
            for k in preset:
                #content will be stored as a string
                #like this: "DBD Roman Noodles Skin": "{\n    \"nodes_list\": [\n        {\n ..."
                #it looks bad, but we must store it this way with \n characters because
                #it must be in a single string
                #a single string is the easiest to store in the Blender add on Preferences
                #as as bpy.types.StringProperty
                content = preset[k]

                new_name = k
                #need to get_preset_by_name_if_exist_in_folder 
                #because need to get the preset instance from the 
                #user preferences stored inuserprefs.blend
                is_preset_name_exist_in_folder, preset_from_preferences = get_preset_by_name_if_exist_in_folder(new_folder.folder_name, new_name)

                if is_preset_name_exist_in_folder:
                    updated_preset = preset_from_preferences
                    updated_preset.content = content
                    message = " ".join(("Preset", preset_from_preferences.name, "exists and was updated!"))
                    log(message)
                else:
                    new_preset = new_folder_presets.add()
                    new_preset.name = new_name
                    new_preset.content = content
                    message = " ".join(("Preset", new_name, "does not exist and was created!"))
                    log(message)
    ui_message = "All presets were reset and updated successfully!"
    bpy.ops.ueshaderscript.show_message(message = ui_message)
    log(ui_message)
    save_pref()

    
    

    


# def import_10_last_used_presets(presets_list):
#     pref = get_preferences()
#     pref.ten_last_used_presets.clear()
#     for preset in presets_list:
#         new_preset = pref.ten_last_used_presets.add()
#         new_preset.folder_name = preset[0]
#         new_preset.preset_name = preset[1]

# def import_10_most_used_presets():
#     update_10_most_used_presets()

# def is_preset_added(folder_name, preset_name):
#     preferences = get_preferences()
#     # for preset in preferences.ten_most_used_presets:
#     #go through all presets recorded in the plugin
#     for preset in preferences.all_presets:
#         if preset.folder_name == folder_name and \
#                 preset.preset_name == preset_name:
#             return True
#     return False

# def update_10_most_used_presets():
#     pref = get_preferences()
#     ten_most_used_presets = pref.ten_most_used_presets
#     ten_most_used_presets.clear()
#     folders = pref.folders_presets
#     presets = []
#     for folder in folders:
#         for preset in folder.presets:
#             if hasattr(preset, "used"):
#                 presets.append((folder.folder_name, preset.name, preset.used))

#     def sort_fun(ele):
#         return ele[2]
#     presets = sorted(presets, key=sort_fun, reverse=True)
#     l = len(presets)
#     if l > 10:
#         l = 10
#     for i in range(0, l):
#         preset = presets[i]
#         if not is_preset_added(preset[0], preset[1]):
#             new_preset = pref.ten_most_used_presets.add()
#             new_preset.folder_name = preset[0]
#             new_preset.preset_name = preset[1]
#     if len(pref.ten_most_used_presets) >= 0:
#         pref.ten_most_used_presets_index = 0

#on import but also on blender start update all presets
# def update_all_presets():
#     pref = get_preferences()
#     all_presets = pref.all_presets

#     #reset all presets list so can check
#     #what presets are present before
#     #recording all currently present
#     all_presets.clear()
#     folders = pref.folders_presets
#     for folder in folders:
#         for preset in folder.presets:
#             #add a new collection item to the all_presets list
#             #.add is a built in blender function for preferences 
#             #record all presets in preferences the preferences all_presets list
#             new_preset = pref.all_presets.add()
#             new_preset.folder_name = folder.folder_name
#             new_preset.preset_name = preset.name

    #debug
    # for preset in pref.all_presets:
    #     print("preset.preset_name:", preset.preset_name, "preset.folder_name:", preset.folder_name)

def get_selected_folder_presets(isOverridePackage = False):
    #getting preferences for add on
    #preferences are anything the add on needs 
    #to store permanently for later use
    #such as the JSON strings associated with each preset
    pref = get_preferences(isOverridePackage)
    #print("pref: ", pref)
    if pref.folders == "" or pref.folders == None:
        return None
    #print("pref.folders:", pref.folders)
    index = int(pref.folders)
    #print("index:", index)

    #print("dir(pref)", dir(pref))
    #debug
    #print("pref.folders_presets:", pref.folders_presets)
    #print("dir(pref.folders_presets[index]):", dir(pref.folders_presets[index]))
    return pref.folders_presets[index]


class PresetCollection(PropertyGroup):
    name: StringProperty()
    #content will be stored as a string
    #like this: "DBD Roman Noodles Skin": "{\n    \"nodes_list\": [\n        {\n ..."
    #it looks bad, but we must store it this way with \n characters because
    #it must be in a single string
    #a single string is the easiest to store in the Blender add on Preferences
    #as as bpy.types.StringProperty
    content: StringProperty()
    #used: IntProperty(default=0)


class FolderPresetsCollection(PropertyGroup):
    folder_name: StringProperty()
    presets: CollectionProperty(type=PresetCollection)
    preset_index: IntProperty()


# class TenLastUsedPresetsCollection(PropertyGroup):
#     folder_name: StringProperty()
#     preset_name: StringProperty()


# class TenMostUsedPresetsCollection(PropertyGroup):
#     folder_name: StringProperty()
#     preset_name: StringProperty()

# class AllPresetsCollection(PropertyGroup):
#     folder_name: StringProperty()
#     preset_name: StringProperty()

def update_folders(self, context):
    redraw_all()    


class SavePreferences(bpy.types.AddonPreferences):
    bl_idname = __package__
    folders_presets: CollectionProperty(type=FolderPresetsCollection)
    folders: EnumProperty(name="",
                          description="",
                          items=get_folders_items,
                          update=update_folders,
                          default=None)
    #all_presets is a list that records all the presets present in the plugin
    # all_presets: CollectionProperty(type=AllPresetsCollection)
    #----not using last used or most used functionality
    # ten_last_used_presets: CollectionProperty(type=TenLastUsedPresetsCollection)
    # ten_last_used_presets_index: IntProperty()
    # ten_most_used_presets: CollectionProperty(type=TenMostUsedPresetsCollection)
    # ten_most_used_presets_index: IntProperty()
    # `presets` and `preset_index` are not used
    # `presets` is for the old version
    presets: CollectionProperty(type=PresetCollection)
    preset_index: IntProperty()

    def draw(self, context):
        wm = context.window_manager
        layout = self.layout

#by default use __package__ however, if the function is being imported elsewhere to a different file
#the __package__ variable does not work, allow another parameter to override with the UEShaderScript string
def get_preferences(isOverridePackage = False, package=__package__, context=None):
    """Multi version compatibility for getting preferences"""
    if isOverridePackage:
        #debug
        #print("Override Package!!!!!")
        package = "UEShaderScript"

    if not context:
        context = bpy.context
    prefs = None
    #blender 2.7x
    if hasattr(context, "user_preferences"):
        prefs = context.user_preferences.addons.get(package, None)
    #blender 2.8+
    elif hasattr(context, "preferences"):
        #debug
        #print("package:", package)
        #__package__ is the name of the folder that the add on is in
        #it would be UEShaderScript for this one
        #This line here gets a prefs struct which is not what we 
        #about we want the attribute preferences inside the prefs struct
        prefs = context.preferences.addons.get(package, None)
        #debug
        #print("dir(prefs):", dir(prefs))
        
    if prefs:
        #debug
        #print("prefs.preferences", prefs.preferences)
        #print("dir(prefs.preferences)", dir(prefs.preferences))
        #print("\n\n")
        #this prefs.preferences here 
        #prefs.preferences refers to the subclass/child class SavePreferences
        #SavePreferences is a child class and builds on bpy.types.AddonPreferences
        #adding extra attributes
        #bpy.types.AddonPreferences is when you need to 
        #save something in the domain of your addon, not in the scene of your blend file.
        return prefs.preferences
    else:
        raise Exception("Could not fetch user preferences")



def save_pref(skip_autosave=False):
    #save_userpref will not work for 
    #import_current_or_default_json()
    #when the blender has just started as blender cannot allow
    #to access ops when file starts
    bpy.ops.wm.save_userpref()
    if not skip_autosave:
        export_to_current_json()


def redraw_all():
    """For redraw Slash panel"""
    for area in bpy.context.window.screen.areas:
        for region in area.regions:
            if region.type == "UI":
                region.tag_redraw()


def export_to_current_json():
    """Use this to export to default json file in ~/node_kit_default_json"""
    #we don't use the plugin directory full path as we don't want to save 
    #over the default presets that come with the plugin
    #they should always stay the same
    current_presets_full_path, default_presets_full_path = get_default_and_current_json_paths()

    f = open(current_presets_full_path, "w+")
    json_string = presets_to_json_string()
    f.write(json_string)
    f.close()


def presets_to_json_string():
    JSON = {}
    pref = get_preferences()
    folders_presets = pref.folders_presets
    for folder_presets in folders_presets:
        presets = []
        for preset in folder_presets.presets:
            preset_dict = {}
            preset_dict[preset.name] = preset.content
            #if hasattr(preset, "used"):
            #    preset_dict[USED_KEY] = preset.used
            presets.append(preset_dict)
        JSON[folder_presets.folder_name] = presets
    #JSON[_10_LAST_USED_PRESETS_KEY] = _10_last_used_presets_to_json()
    return dict_to_string(JSON)


#button to reset and update default presets
class ResetAndUpdateDefaultPresetsOperator(bpy.types.Operator):
    bl_idname = "ueshaderscript.reset_update_default_presets"
    bl_label = "Reset & Update Default Presets"
    bl_description = "Reset & Update Default Presets"

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        reset_and_update_default_presets()
        redraw_all()
        return {'FINISHED'}


def reset_and_update_default_presets():
    #only use the default_presets_full_path don't use current presets full path because we don't need it
    current_presets_full_path, default_presets_full_path = get_default_and_current_json_paths()

    default_presets_json_file = pathlib.Path(default_presets_full_path)
    if(default_presets_json_file.exists()):
        with open(default_presets_full_path) as f:
            json_string = f.read()
            json_string_to_update_default_presets(json_string)
    else:
        log("Error: no default JSON File was found in the Plugin Folder, please send a screenshot of the error to the developer.")


#--------------------------------------------import and export json files code
class ImportAndAppendPresetsOperator(bpy.types.Operator):
    bl_idname = "ueshaderscript.import_append_presets"
    bl_label = "Import & Append Presets"
    bl_description = "Import & Append Presets"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        f = open(self.filepath, "r")
        json_string = f.read()
        f.close()
        json_string_to_presets_append(json_string)
        redraw_all()
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


def json_string_to_presets_append(json_string):
    dict = json_to_dict(json_string)
    pref = get_preferences()
    folders_presets = pref.folders_presets
    for key in dict:
        #Not using last used functionality
        # if key == _10_LAST_USED_PRESETS_KEY:
        #     presets_list = dict[key]
        #     import_10_last_used_presets(presets_list)
        #     continue
        presets = dict[key]
        if folder_name_exist(key):
            new_folder = get_folder_presets_by_name(key)
        else:
            new_folder = folders_presets.add()
            new_folder.folder_name = key
        new_folder_presets = new_folder.presets
        for preset in presets:
            new_preset = new_folder_presets.add()
            #new_preset.used = 0
            for k in preset:
                # if k == USED_KEY:
                #     new_preset.used = preset[USED_KEY]
                # else:
                    # Append new preset with a name "XXX-copy" if
                    # this preset have the same name exists
                    # new_name = k
                    # while preset_name_exist_in_folder(
                    #         new_folder.folder_name,
                    #         new_name):
                    #     new_name = new_name + " copy"
                    # new_preset.name = new_name
                    # content = preset[k]
                    # new_preset.content = content
                new_name = k
                while preset_name_exist_in_folder(
                        new_folder.folder_name,
                        new_name):
                    new_name = "".join((new_name, " copy"))
                new_preset.name = new_name

                #content will be stored as a string
                #like this: "DBD Roman Noodles Skin": "{\n    \"nodes_list\": [\n        {\n ..."
                #it looks bad, but we must store it this way with \n characters because
                #it must be in a single string
                #a single string is the easiest to store in the Blender add on Preferences
                #as as bpy.types.StringProperty
                content = preset[k]
                new_preset.content = content
    #import_10_most_used_presets()
    save_pref()

def get_folder_presets_by_name(name):
    pref = get_preferences()
    folder_presets = pref.folders_presets
    for index, folder_preset in enumerate(folder_presets):
        if folder_preset.folder_name == name:
            return folder_preset
    return None


def get_preset_by_name_if_exist_in_folder(folder_name, preset_name):
    pref = get_preferences()
    folders_presets = pref.folders_presets
    for folder in folders_presets:
        if folder.folder_name == folder_name:
            for preset in folder.presets:
                if preset.name == preset_name:
                    return True, preset
    return False, None

class ExportPresetsOperator(bpy.types.Operator):
    bl_idname = "ueshaderscript.export_presets"
    bl_label = "Export Presets"
    bl_description = "Export Presets"

    filepath: bpy.props.StringProperty(subtype="FILE_PATH")

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        f = open(self.filepath, "w+")
        json_string = presets_to_json_string()
        f.write(json_string)
        f.close()
        return {'FINISHED'}

    def invoke(self, context, event):
        self.filepath = "presets.json"
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

#-----------------------------------message and console log related code
VERBOSE = True

def log(msg):
    if VERBOSE:
        print("[UE Shader Script]:", msg)

def report_error(self, message):
    full_message = "%s\n\nPlease report to the add-on developer with this error message (A screenshot is awesome)" % message
    self.report({"ERROR"}, full_message)


class ShowMessageOperator(bpy.types.Operator):
    bl_idname = "ueshaderscript.show_message"
    bl_label = ""
    bl_description = "Show Message for UEShaderScript"
    bl_options = {'REGISTER'}
    message: bpy.props.StringProperty(default="Message Dummy")
    called: bpy.props.BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return True

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self, width=300)

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.label(text=self.message)

    def execute(self, context):
        if not self.called:
            wm = context.window_manager
            self.called = True
            return wm.invoke_props_dialog(self, width=700)
        return {'FINISHED'}

#--------load default suffixes so don't need to type in all the suffixes and node names
class SAVEUESHADERSCRIPT_OT_load_default_suffixes(bpy.types.Operator):
    bl_idname = "saveueshaderscript.load_default_suffixes_operator"
    bl_label = "Load Preset Suffixes and Node Names"
    bl_description = "Load Preset Suffixes and Node Names"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        #store active/selected scene to variable
        scene = context.scene
        
        #allow access to user inputted properties through pointer
        #to properties
        savetool = scene.save_tool

        default_suffix = savetool.default_suffix_enum

        #debug
        #print("default_suffix", default_suffix)

        #load the suffixes into the
        #suffix and node input boxes required 
        #for the different hardcoded cases
        if(default_suffix == "DBD_HAIR"):
            #this first case is written explicitly
            #instead of changing from the default 
            #inputs and node names because
            #it changes so much and is quite confusing
            #without explcitly stating what the inputs are
            savetool.bc_suffix = "_BC _ID _BC_01 _BC_02 _BC_03 _BC_04 _BC_2 _BC_3 _BC_4"
            savetool.bc_node_name = "Diffuse Node"
            savetool.orm_suffix = ""
            savetool.orm_node_name = ""
            savetool.n_suffix = "_N"
            savetool.n_node_name = "Normal Map Node"
            savetool.m_suffix = "_M _A"
            savetool.m_node_name = "Transparency Map Node"
            savetool.bde_suffix = ""
            savetool.bde_node_name = ""
            savetool.hm_suffix = "_Height _Heigth _D _Depth"
            savetool.hm_node_name = "Height Map Node"
            savetool.hair_gradient_suffix = "_verticalGradient _verticalGradient2 _Gradient"
            savetool.hair_gradient_node_name = "Hair Gradient Map Node"
            savetool.specular_suffix = ""
            savetool.specular_node_name = ""
            savetool.gloss_suffix = ""
            savetool.gloss_node_name = ""

            savetool.cust1_suffix = ""
            savetool.cust1_node_name = ""
            savetool.cust2_suffix = ""
            savetool.cust2_node_name = ""
            savetool.cust3_suffix = ""
            savetool.cust3_node_name = ""
            savetool.cust4_suffix = ""
            savetool.cust4_node_name = ""

            savetool.skin_node_name = ""
        elif(default_suffix == "DBD_SKIN"):
            #reason why we are using reset to default is the skin operator
            #is very similar to the default inputs except for the m_suffix,
            #m_node_name and skin_node_name
            bpy.ops.saveueshaderscript.reset_inputs_main_panel_operator()
            savetool.m_suffix = ""
            savetool.m_node_name = ""
            savetool.skin_node_name = "Skin Node"

        elif(default_suffix == "DBD_GENERAL"):
            #the dbd general suffix and node names are the default ones
            #so reset to the default inputs
            bpy.ops.saveueshaderscript.reset_inputs_main_panel_operator()

        else:
            error_message = "".join("Error: the default_suffix", default_suffix, "was not found, please contact the plugin author.")
            bpy.ops.ueshaderscript.show_message(message = error_message)
            log(error_message)

        return {'FINISHED'}

#--------reset save function main panel class
class SAVEUESHADERSCRIPT_OT_reset_inputs_main_panel(bpy.types.Operator):
    bl_idname = "saveueshaderscript.reset_inputs_main_panel_operator"
    bl_label = "Reset All Inputs to Default"
    bl_description = "Reset Save Settings Main Panel for UEShaderScript"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        #store active/selected scene to variable
        scene = context.scene
        
        #allow access to user inputted properties through pointer
        #to properties
        savetool = scene.save_tool

        #don't need to unset the custom map name
        #because don't want user typing in name again and again
        #savetool.property_unset("cust_map_name")
        savetool.property_unset("bc_suffix")
        savetool.property_unset("bc_node_name")
        savetool.property_unset("orm_suffix")
        savetool.property_unset("orm_node_name")
        savetool.property_unset("n_suffix")
        savetool.property_unset("n_node_name")
        savetool.property_unset("m_suffix")
        savetool.property_unset("m_node_name")
        savetool.property_unset("bde_suffix")
        savetool.property_unset("bde_node_name")
        savetool.property_unset("hm_suffix")
        savetool.property_unset("hm_node_name")
        savetool.property_unset("hair_gradient_suffix")
        savetool.property_unset("hair_gradient_node_name")
        savetool.property_unset("specular_suffix")
        savetool.property_unset("specular_node_name")
        savetool.property_unset("gloss_suffix")
        savetool.property_unset("gloss_node_name")

        savetool.property_unset("is_show_custom_textures")
        savetool.property_unset("cust1_suffix")
        savetool.property_unset("cust1_node_name")
        savetool.property_unset("cust2_suffix")
        savetool.property_unset("cust2_node_name")
        savetool.property_unset("cust3_suffix")
        savetool.property_unset("cust3_node_name")
        savetool.property_unset("cust4_suffix")
        savetool.property_unset("cust4_node_name")

        savetool.property_unset("skin_node_name")
        savetool.property_unset("is_add_img_textures")
        return {'FINISHED'}

#don't register SAVEUESHADERSCRIPT_shared_main_panel 
#as it is not a bpy type or panel
# #trying to register it will cause an error 
classes = [SaveProperties, PresetCollection, FolderPresetsCollection, SavePreferences, 

    ResetAndUpdateDefaultPresetsOperator, ImportAndAppendPresetsOperator, ExportPresetsOperator,
    
    SHADER_PRESETS_UL_items, 
     
    SAVEUESHADERSCRIPT_PT_manage_presets_main_panel_1, SAVEUESHADERSCRIPT_PT_save_custom_preset_main_panel_2,

    Shader_ShowFolderActionsOperator, SHADER_MT_FolderActionsMenu, Shader_NewFolderOperator, 
    Shader_RemoveFolderOperator, Shader_RenameFolderOperator, SAVEUESHADERSCRIPT_OT_remove_preset, ShowMessageOperator,
    RenamePresetOperator, MovePresetUpOperator, MovePresetDownOperator, MovePresetOperator, 
    
    SAVEUESHADERSCRIPT_OT_load_default_suffixes, SAVEUESHADERSCRIPT_OT_reset_inputs_main_panel,

    SAVEUESHADERSCRIPT_OT_save_shader_map]
 
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    #register save_tool as a type which has all
    #the user input properties from the properties class 
    bpy.types.Scene.save_tool = bpy.props.PointerProperty(type = SaveProperties)
 
 
def unregister():
    #unregister in reverse order to registered so classes relying on other classes
    #will not lead to an error
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    #unregister save_tool as a type
    del bpy.types.Scene.save_tool
 
 
if __name__ == "__main__":
    register()