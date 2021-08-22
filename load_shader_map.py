#import all libraries including re needed for regex matching
#import Path library to search recursively for files
import bpy, re
import glob
from pathlib import Path

import base64

import time

import os

#import with relative imports
#import classes 
from .save_shader_map import SHADER_PRESETS_UL_items, ShowMessageOperator, save_pref
#import functions
from .save_shader_map import get_preferences, get_selected_folder_presets, json_to_nodes_dict, log

#import pathlib for finding current working direction for LOADUESHADERSCRIPT_OT_use_custom_denoising
import pathlib


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


#need scene and context in order to be used within
#the x_color_space, such as the diffuse_color_space
#as a callback function for the items property
def color_spaces_callback(scene, context):
    
    color_spaces = [
        ("sRGB" , "sRGB", ""),
        ("Non-Color" , "Non-Color", ""),
        ("Linear" , "Linear", ""),
        ("Filmic Log" , "Filmic Log", ""),
        ("Linear ACES" , "Linear ACES", ""),
        ("Raw" , "Raw", ""),
        ("XYZ" , "XYZ", "")
    ]

    return color_spaces

#define all user input properties
class PathProperties(bpy.types.PropertyGroup):
    #user input paths for textures and materials
    props_txt_path: bpy.props.StringProperty(name="(!) Select PropsTxt File*", description="Select a props.txt file", subtype="FILE_PATH")
    skin_bump_map_path: bpy.props.StringProperty(name="Select Skin Bump Map File (Optional for Skin Presets)", description="Select a skin bump map image file", subtype="FILE_PATH")
    export_folder_path: bpy.props.StringProperty(name="(!) Select Exported Game Folder*", description="Select a Game folder", subtype="DIR_PATH")

    #used to show the button and box to add a shader map to one material at a time
    is_show_add_one_material_operator: bpy.props.BoolProperty(name="Show Add Shader Map to One Material Operator", default = False)

    #used for the add shader maps to multiple materials operator
    material_indices_list_string: bpy.props.StringProperty(name="(!) Indexes of Material Slots to be Loaded *", description="Enter the indices for the materials to be loaded", default = "0 1 2")

    #--------------loading shader map settings
    is_replace_nodes: bpy.props.BoolProperty(name="Replace Existing Shader Maps", default = True)
   

    texture_file_type_enum: bpy.props.EnumProperty(
        name = "Texture File Type",
        description = "Dropdown List of all the texture file types",
        items = 
        [
            (".tga" , ".tga", ""),
            (".png" , ".png", ""),
            (".jpg", ".jpg", ""),
            (".bmp", ".bmp", ""),
            (".dds", ".dds", "")
        ]
        
    )
    clipping_method_enum: bpy.props.EnumProperty(
        name = "Alpha Clipping Method",
        description = "Dropdown List of all the texture file types",
        items = 
        [
            ("HASHED" , "Alpha Hashed", ""),
            ("CLIP" , "Alpha Clip", "")
        ]
  
        
    )

    is_load_img_textures: bpy.props.BoolProperty(name="Load Image Textures Dynamically", default= True)
    is_delete_unused_img_texture_nodes: bpy.props.BoolProperty(name="Delete Unused Image Texture Nodes", default = True)
    is_delete_unused_related_nodes: bpy.props.BoolProperty(name="Delete Unused Image Texture Nodes AND Related Nodes (Slower)", default = True)

    is_change_principle_bsdf_emission_strength: bpy.props.BoolProperty(name="Change Principled BSDF Node Strength if Emissions Texture Loaded", default = True)
    principled_bsdf_emission_strength_float: bpy.props.FloatProperty(name="Principled BSDF Emission Strength if Emissions Texture Loaded", default = 5.0)
    material_alpha_threshold: bpy.props.FloatProperty(name="Material Clip Threshold if Transparency Texture Loaded", default = 0.3333)

    #options to allow reuse of node groups and image textures
    is_reuse_node_group_with_same_name: bpy.props.BoolProperty(name="Reuse Node Groups With Same Name", default = True)
    is_reuse_img_texture_with_same_name: bpy.props.BoolProperty(name="Reuse Image Textures With Same Name", default = True)
    
    #in case of overlap decide if first or last texture in props
    #txt file takes priority this is done by 
    #reversing or not reversing the match_list
    reverse_match_list_from_props_txt_enum: bpy.props.EnumProperty(
        name = "Overlapping Textures Priority",
        description = "If Dynamically Loaded Textures Overlap Choose Priority",
        items = 
        [
            ("Reverse Match List" , "First in Materials Info File/props.txt Takes Priority (First > Last)", ""),
            ("Don't Reverse Match List" , "Last in Materials Info File/props.txt Takes Priority (Last > First)", "")
        ]
        
    )
  
    is_add_skin_bump_map: bpy.props.BoolProperty(name="Add Skin Bump Texture (Optional for Skin Presets)", default = False)

    is_use_recolor_values: bpy.props.BoolProperty(name="Use Recolor RGB Colour Values", default = True)

    is_add_non_match_textures: bpy.props.BoolProperty(name="Add Non Matching Textures from Props.txt file", default = False)

    #---------------color space settings enums
    #default global variables for the recommended 
    #colour spaces for image textures
    #srgb color space isn't used but it is there for reference purposes
    # srgb_color_space_list = ["diffuse", "tint_base_diffuse", "cust1", "cust2", "cust3", "cust4"]
    # non_color_space_list = ["normal", "packed_orm", "emissive", "tint_mask", "specular", "gloss"]
    # linear_color_space_list = ["transparency", "height", "hair_gradient", "skin_bump"]

    #set default for only those which are not srgb color space
    #because the default color space is srgb the 0th option
    #so if not stated the default is sRGB
    diffuse_color_space: bpy.props.EnumProperty(
        name = "Diffuse Color Space",
        description = "Diffuse Image Texture Color Space",
        #don't call the function immediately with () 
        #but wait for the enum property to be defined
        items = color_spaces_callback
    )

    packed_rgb_color_space: bpy.props.EnumProperty(
        name = "Packed RGB Color Space",
        description = "Packed RGB Image Texture Color Space",
        items = color_spaces_callback,
        #1 means Non-Color
        default = 1
    )

    normal_color_space: bpy.props.EnumProperty(
        name = "Normal Color Space",
        description = "Normal Map Image Texture Color Space",
        items = color_spaces_callback,
        #1 means Non-Color
        default = 1
    )

    alpha_color_space: bpy.props.EnumProperty(
        name = "Alpha Color Space",
        description = "Alpha Image Texture Color Space",
        items = color_spaces_callback,
        #2 means Linear
        default = 2
    )

    emissions_color_space: bpy.props.EnumProperty(
        name = "Emissions Color Space",
        description = "Emissions Map Image Texture Color Space",
        items = color_spaces_callback,
        #1 means Non-Color
        default = 1
    )

    height_color_space: bpy.props.EnumProperty(
        name = "Height Color Space",
        description = "Height Map Image Texture Color Space",
        items = color_spaces_callback,
        #2 means Linear
        default = 2
    )

    hair_gradient_color_space: bpy.props.EnumProperty(
        name = "Hair Gradient Color Space",
        description = "Hair Gradient Image Texture Color Space",
        items = color_spaces_callback,
        #2 means Linear
        default = 2
    )

    specular_color_space: bpy.props.EnumProperty(
        name = "Specular Color Space",
        description = "Specular Image Texture Color Space",
        items = color_spaces_callback,
        #1 means Non-Color
        default = 1
    )

    gloss_color_space: bpy.props.EnumProperty(
        name = "Gloss Color Space",
        description = "Gloss Image Texture Color Space",
        items = color_spaces_callback,
        #1 means Non-Color
        default = 1
    )

    skin_bump_color_space: bpy.props.EnumProperty(
        name = "Skin Bump Color Space",
        description = "Skin Bump Image Texture Color Space",
        items = color_spaces_callback,
        #2 means Linear
        default = 2
    )

    tint_base_diffuse_color_space: bpy.props.EnumProperty(
        name = "Tint Base Diffuse Color Space",
        description = "Tint Base Diffuse Image Texture Color Space",
        items = color_spaces_callback
    )

    tint_mask_color_space: bpy.props.EnumProperty(
        name = "Tint Mask Color Space",
        description = "Tint Mask Image Texture Color Space",
        items = color_spaces_callback,
        #1 means Non-Color
        default = 1
    )

    #all custom textures are by default sRGB color space
    cust1_color_space: bpy.props.EnumProperty(
        name = "Custom1 Color Space",
        description = "Custom1 Image Texture Color Space",
        items = color_spaces_callback
    )

    cust2_color_space: bpy.props.EnumProperty(
        name = "Custom2 Color Space",
        description = "Custom2 Image Texture Color Space",
        items = color_spaces_callback
    )

    cust3_color_space: bpy.props.EnumProperty(
        name = "Custom3 Color Space",
        description = "Custom3 Image Texture Color Space",
        items = color_spaces_callback
    )

    cust4_color_space: bpy.props.EnumProperty(
        name = "Custom4 Color Space",
        description = "Custom4 Image Texture Color Space",
        items = color_spaces_callback
    )

    non_match_color_space: bpy.props.EnumProperty(
        name = "Non Match Textures Color Space",
        description = "Non Match Image Textures Color Space",
        items = color_spaces_callback
    )


    #advanced settings
    regex_pattern_in_props_txt_file: bpy.props.StringProperty(name="Regex Pattern in props.txt (material) files:", 
                description="Regex pattern used in files that describe materials ", default = "Texture2D\'(.*)\.")
    props_txt_file_type: bpy.props.StringProperty(name="File extension for material info files:", 
                description="File extension for material info files, props.txt file equivalents", default = ".props.txt")

    # Debug console options
    #show textures from the props.txt file that did not match suffixes
    #but were added to the shader map anyway for debug purposes
    is_show_no_match_tex_debug: bpy.props.BoolProperty(name="Show Non Suffix Matching Textures in Console (Debug) ", default = False)
    #show the abs_props_txt path in the debug console
    is_show_abs_props_debug: bpy.props.BoolProperty(name="Show props.txt File Path in Console (Debug)", default = False)
    


    #This is NOT a property that will show on any panel and the user
    #cannot interact with this variable
    #it is used to trigger a flag when accessing bpy.ops to save
    #to the default preferences is not possible
    #it will raise this boolean so the next time the user loads
    #any preset it will make the add on preferences for the current file to be
    #the default preferences
    #it is set to true when the plugin is initialised and will be immediately 
    #set to false upon the first load shader map completion
    is_save_to_default_preferences_on_next_load_shader_map: bpy.props.BoolProperty(name="N/A", default = True)




#------------code for drawing main panel in the 3D View
#don't register this class it is not a bpy panel or type so
#it does not need to be registered
class LOADUESHADERSCRIPT_shared_main_panel:
    # bl_label = "Load UE Shaders"
    # bl_idname = "LOADUESHADERSCRIPT_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "Load UE Shaders"


#main panel part 1
#inheriting the shared panel's bl_space_type, bl_region_type and bl_category
class LOADUESHADERSCRIPT_PT_select_preset_main_panel_1(LOADUESHADERSCRIPT_shared_main_panel, bpy.types.Panel):
    bl_label = "Select Preset in Folder"
    bl_idname = "LOADUESHADERSCRIPT_PT_select_preset_main_panel_1"

    def draw(self, context):
        layout = self.layout
        
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


#main panel part 2
#inheriting the shared panel's bl_space_type, bl_region_type and bl_category
class LOADUESHADERSCRIPT_PT_load_settings_main_panel_2(LOADUESHADERSCRIPT_shared_main_panel, bpy.types.Panel):
    bl_label = "Load Shader Map Settings"
    bl_idname = "LOADUESHADERSCRIPT_PT_load_settings_main_panel_2"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        
        #store active/selected scene to variable
        scene = context.scene
        #allow access to user inputted properties through pointer
        #to properties
        pathtool = scene.path_tool

        #--------make load shader map settings section
        layout.prop(pathtool, "is_load_img_textures")

        #option to replace or keep existing nodes in materials
        layout.prop(pathtool, "is_replace_nodes")

        if(pathtool.is_load_img_textures):
            #option to delete image texture nodes which have not had a texture
            #loaded into them
            layout.prop(pathtool, "is_delete_unused_img_texture_nodes")

            #only show this option if delete unused_img_texture_nodes is checked
            if(pathtool.is_delete_unused_img_texture_nodes):
                layout.prop(pathtool, "is_delete_unused_related_nodes")

            layout.prop(pathtool, "texture_file_type_enum")

            layout.prop(pathtool, "is_reuse_node_group_with_same_name")
            layout.prop(pathtool, "is_reuse_img_texture_with_same_name")

            layout.prop(pathtool, "reverse_match_list_from_props_txt_enum")
            
            layout.prop(pathtool, "is_use_recolor_values")
            layout.prop(pathtool, "is_add_non_match_textures")

            #Skin Preset Related Settings
            layout.prop(pathtool, "is_add_skin_bump_map")


#main panel part 3
#inheriting the shared panel's bl_space_type, bl_region_type and bl_category
class LOADUESHADERSCRIPT_PT_alpha_emissive_main_panel_3(LOADUESHADERSCRIPT_shared_main_panel, bpy.types.Panel):
    bl_label = "Alpha and Emissive Settings"
    bl_idname = "LOADUESHADERSCRIPT_PT_alpha_emissive_main_panel_3"
    #put parent id so it knows this is a subpanel of the parent panel
    bl_options = {"DEFAULT_CLOSED"}
    
    #poll function only allows 
    #execute and draw functions to be executed
    #if poll returns true
    #in this case depends upon whether the
    #is_load_img_textures settings is true
    #if false then don't draw the advanced settings panel
    @classmethod
    def poll(self, context):
        #store active scene to variable
        scene = context.scene
        #allow access to user inputted properties through pointer
        #to properties
        pathtool = scene.path_tool

        return pathtool.is_load_img_textures

    def draw(self, context):
        layout = self.layout

        #store active scene to variable
        scene = context.scene
        #allow access to user inputted properties through pointer
        #to properties
        pathtool = scene.path_tool

        layout.prop(pathtool, "clipping_method_enum")
        layout.prop(pathtool, "material_alpha_threshold")

        layout.prop(pathtool, "is_change_principle_bsdf_emission_strength")
            
        if(pathtool.is_change_principle_bsdf_emission_strength):
            layout.prop(pathtool, "principled_bsdf_emission_strength_float")


#main panel part 4
#inheriting the shared panel's bl_space_type, bl_region_type and bl_category
class LOADUESHADERSCRIPT_PT_color_space_main_panel_4(LOADUESHADERSCRIPT_shared_main_panel, bpy.types.Panel):
    bl_label = "Color Space Settings"
    bl_idname = "LOADUESHADERSCRIPT_PT_color_space_main_panel_4"
    bl_options = {"DEFAULT_CLOSED"}
    
    #poll function only allows 
    #execute and draw functions to be executed
    #if poll returns true
    #in this case depends upon whether the
    #is_load_img_textures settings is true
    #if false then don't draw the advanced settings panel
    @classmethod
    def poll(self, context):
        #store active scene to variable
        scene = context.scene
        #allow access to user inputted properties through pointer
        #to properties
        pathtool = scene.path_tool

        return pathtool.is_load_img_textures

    def draw(self, context):
        layout = self.layout

        #store active scene to variable
        scene = context.scene
        #allow access to user inputted properties through pointer
        #to properties
        pathtool = scene.path_tool

        #formatting default blender attribute
        #layout.use_property_split means that it will try and display 
        #the property label fully
        layout.use_property_split = True

        #prevent the animate button appearing to the right side
        #of the enum properties
        layout.use_property_decorate = False

        layout.label(text = "Please do not change these settings unless you know what you are doing.")

        layout.prop(pathtool, "diffuse_color_space")
        layout.prop(pathtool, "packed_rgb_color_space")
        layout.prop(pathtool, "normal_color_space")
        layout.prop(pathtool, "alpha_color_space")
        layout.prop(pathtool, "emissions_color_space")
        layout.prop(pathtool, "height_color_space")
        layout.prop(pathtool, "hair_gradient_color_space")
        layout.prop(pathtool, "specular_color_space")
        layout.prop(pathtool, "gloss_color_space")
        layout.prop(pathtool, "skin_bump_color_space")
        layout.prop(pathtool, "tint_base_diffuse_color_space")
        layout.prop(pathtool, "tint_mask_color_space")
        layout.prop(pathtool, "cust1_color_space")
        layout.prop(pathtool, "cust1_color_space")
        layout.prop(pathtool, "cust2_color_space")
        layout.prop(pathtool, "cust3_color_space")
        layout.prop(pathtool, "cust4_color_space")

        layout.separator()
        layout.label(text = "(Need Load Settings > Add Non Match enabled to do anything)")
        layout.prop(pathtool, "non_match_color_space")
        


#main panel part 5
#inheriting the shared panel's bl_space_type, bl_region_type and bl_category
class LOADUESHADERSCRIPT_PT_advanced_settings_main_panel_5(LOADUESHADERSCRIPT_shared_main_panel, bpy.types.Panel):
    bl_label = "Advanced Settings"
    bl_idname = "LOADUESHADERSCRIPT_PT_advanced_settings_main_panel_5"
    bl_options = {"DEFAULT_CLOSED"}
    
    #poll function only allows 
    #execute and draw functions to be executed
    #if poll returns true
    #in this case depends upon whether the
    #is_load_img_textures settings is true
    #if false then don't draw the advanced settings panel
    @classmethod
    def poll(self, context):
        #store active scene to variable
        scene = context.scene
        #allow access to user inputted properties through pointer
        #to properties
        pathtool = scene.path_tool

        return pathtool.is_load_img_textures

    def draw(self, context):
        layout = self.layout

        #store active scene to variable
        scene = context.scene
        #allow access to user inputted properties through pointer
        #to properties
        pathtool = scene.path_tool

        #showing debug console file path
        #this is if debugging is required

        #enable this option so you can see which textures from
        #the props.txt file never matched anything
        layout.prop(pathtool, "is_show_no_match_tex_debug")

        #enable this option so then you can see which material is causing the problem
        #do this before use_property split so it is not affected by the use_property_spli
        #because it looks bad with use property split
        layout.prop(pathtool, "is_show_abs_props_debug")

        #formatting default blender attribute
        #layout.use_property_split means that it will try and display 
        #the property label fully
        layout.use_property_split = True

        layout.label(text = "Please only change these settings if you know what you are doing")
        layout.prop(pathtool, "regex_pattern_in_props_txt_file")
        layout.prop(pathtool, "props_txt_file_type")

#main panel part 6
#inheriting the shared panel's bl_space_type, bl_region_type and bl_category
class LOADUESHADERSCRIPT_PT_reset_settings_main_panel_6(LOADUESHADERSCRIPT_shared_main_panel, bpy.types.Panel):
    bl_label = "Reset Load Shader Map Settings"
    bl_idname = "LOADUESHADERSCRIPT_PT_reset_settings_main_panel_6"
    #hide header means to hide the title because we 
    #just want to see the button here
    #not the bl_label
    #bl_options = {"HIDE_HEADER"}
    def draw(self, context):
        layout = self.layout
        layout.operator("loadueshaderscript.reset_settings_main_panel_operator")


#main panel part 7
#inheriting the shared panel's bl_space_type, bl_region_type and bl_category
class LOADUESHADERSCRIPT_PT_load_methods_main_panel_7(LOADUESHADERSCRIPT_shared_main_panel, bpy.types.Panel):
    bl_label = "Load Shader Map Methods"
    bl_idname = "LOADUESHADERSCRIPT_PT_load_methods_main_panel_7"

    def draw(self, context):
        layout = self.layout
        
        #store active/selected scene to variable
        scene = context.scene
        #allow access to user inputted properties through pointer
        #to properties
        pathtool = scene.path_tool

        #--------------draw load shader map methods
        #formatting
        #layout.use_property_split means that it will try and display 
        #the property label fully
        layout.use_property_split = True

        
        #create box for all related inputs adding shader map to multiple material
        box = layout.box()
        box.label(text = "ADD SHADER MAP TO MULTIPLE MATERIALS (MULTIPLE MATERIALS)")
        box.label(text = "Select a mesh, enter material indexes separated by a space and add shader maps to multiple materials")
        
        if(pathtool.is_load_img_textures):
            box.prop(pathtool, "material_indices_list_string")
            box.prop(pathtool, "export_folder_path")
            if(pathtool.is_add_skin_bump_map):
                box.prop(pathtool, "skin_bump_map_path")
        else:
            box.prop(pathtool, "material_indices_list_string")
        box.operator("loadueshaderscript.add_to_multiple_materials_operator")
                
        #Create a box for adding shader maps to all materials
        #to the selected mesh with all
        #related inputs and operators 
        box = layout.box()
        box.label(text = "ADD SHADER MAP TO ALL MATERIALS ON SELECTED MESHES (ALL MATERIALS)")
        box.label(text = "Select multiple meshes and add shader maps to all the materials on the selected meshes")
        if(pathtool.is_load_img_textures):
            box.prop(pathtool, "export_folder_path")
            if(pathtool.is_add_skin_bump_map):
                box.prop(pathtool, "skin_bump_map_path")
        box.operator("loadueshaderscript.add_to_selected_meshes_operator" )

        layout.use_property_split = False

        #create box for all related input adding shader map to one selected material
        #should hide by default, but show if is_show_add_one_material_operator is checked
        #use this because some props.txt files do not have the same name as their materials
        layout.prop(pathtool, "is_show_add_one_material_operator")

        #formatting
        #layout.use_property_split means that it will try and display 
        #the property label fully
        layout.use_property_split = True

        if (pathtool.is_show_add_one_material_operator):
            box = layout.box()
            box.label(text = "ADD SHADER MAP TO SELECTED MATERIAL (ONE MATERIAL)")
            box.label(text = "Select a mesh and a material and add a shader map to the selected material")
            box.label(text = "Used for Materials which have different names to their props.txt files")
            if(pathtool.is_load_img_textures):
                box.prop(pathtool, "props_txt_path")
                box.prop(pathtool, "export_folder_path")
                if(pathtool.is_add_skin_bump_map):
                    box.prop(pathtool, "skin_bump_map_path")
            box.operator("loadueshaderscript.add_to_one_material_operator")


#main panel part 8
#inheriting the shared panel's bl_space_type, bl_region_type and bl_category
class LOADUESHADERSCRIPT_PT_solo_material_main_panel_8(LOADUESHADERSCRIPT_shared_main_panel, bpy.types.Panel):
    bl_label = "Solo Material"
    bl_idname = "LOADUESHADERSCRIPT_PT_solo_material_main_panel_8"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        layout = self.layout
        layout.label(text = "Toggle Solo Use Nodes on the active material so it easier to adjust")
        layout.label(text = "Solo Active Material for ALL Meshes")
        layout.operator("loadueshaderscript.solo_material_all_operator")
        layout.operator("loadueshaderscript.use_nodes_mesh_all_operator")
        layout.separator()

        layout.label(text = "Solo Active Material for the Active Mesh")
        layout.operator("loadueshaderscript.solo_material_operator")
        layout.operator("loadueshaderscript.use_nodes_mesh_operator")

#main panel part 9
#inheriting the shared panel's bl_space_type, bl_region_type and bl_category
class LOADUESHADERSCRIPT_PT_custom_denoising_main_panel_9(LOADUESHADERSCRIPT_shared_main_panel, bpy.types.Panel):
    bl_label = "Pit Princess Custom Denoising Setup"
    bl_idname = "LOADUESHADERSCRIPT_PT_custom_denoising_main_panel_9"
    bl_options = {"DEFAULT_CLOSED"}
    
    def draw(self, context):
        layout = self.layout
        layout.label(text = "Press press Use Pit Princess Custom Denoising Setup")
        layout.label(text = "to load a custom compositing tab denoising node setup")
        layout.operator("loadueshaderscript.use_custom_denoising_operator")

#---------------------------code for Operators in Main Panel

class LOADUESHADERSCRIPT_OT_add_to_one_material(bpy.types.Operator):
    bl_label = "Add ONE Shader Map to Active Material"
    bl_description = "Add ONE Shader Map to Active Material on Active Mesh"
    bl_idname = "loadueshaderscript.add_to_one_material_operator"
    def execute(self, context):
        #time how long it takes to create all shader maps for all materials
        #set start time
        time_start = time.time()

        scene = context.scene 
        #allow access to user inputted properties through pointer
        #to properties
        pathtool = scene.path_tool

        #returns the active object, which means the last selected object
        #even if it is not selected at the current moment
        active_object = bpy.context.active_object

        #check if required fields have been filled in
        #or if the load image textures dynamically checkbox is false
        #does not need required fields
        if pathtool.export_folder_path != "" and pathtool.props_txt_path != "" or not(pathtool.is_load_img_textures):
            create_one_material_shader_map(active_object, pathtool, time_start)

        #else if required fields are missing
        else:
            error_message = "Error: One or more Required Fields, marked with (!) have not been filled in."
            bpy.ops.ueshaderscript.show_message(message = error_message)
            log(error_message)
        
        return {"FINISHED"}


def create_one_material_shader_map(active_object, pathtool, time_start):
    if active_object != None:

        if active_object.type == "MESH":
            #shade smooth on the active object
            #may already be shaded smooth if coming from the 
            #create_all_shader_maps
            #but this is just in case the user only runs create_one_shader_map
            mesh = active_object.data
            for f in mesh.polygons:
                f.use_smooth = True

            #find the selected material and 
            #create a basic shader on it
            selected_mat = bpy.context.active_object.active_material
            
            create_one_shader_map(selected_mat, pathtool.props_txt_path, pathtool)

            #print the time taken to finish creating the shader map
            #don't use log so can use new line characters
            #this is inside all the checks because we only print finished if an error hasn't occcured
            print("\n\n\n[UE Shader Script]: Finished create_one_shader_map in: %.4f sec" % (time.time() - time_start), "\n\n\n")


        #if the active_object is not a mesh
        else:
            error_message = "Error: Active Object is not a mesh, please select a mesh before pressing Add ONE Shader Map to Active Material"
            bpy.ops.ueshaderscript.show_message(message = error_message)
            log(error_message)


    #if active_object is None and does not exist
    else:
        error_message = "Error: No Active Object, please select a mesh before pressing Add ONE Shader Map to Active Material"
        bpy.ops.ueshaderscript.show_message(message = error_message)
        log(error_message)



class LOADUESHADERSCRIPT_OT_add_to_multiple_materials(bpy.types.Operator):
    bl_label = "Add Shader Maps to Multiple Materials"
    bl_description = "Add Shader Maps to Multiple Materials by Index"
    bl_idname = "loadueshaderscript.add_to_multiple_materials_operator"
    def execute(self, context):
        #time how long it takes to create all shader maps for all materials
        #set start time
        time_start = time.time()

        scene = context.scene 
        #allow access to user inputted properties through pointer
        #to properties
        pathtool = scene.path_tool

        #check if required fields have been filled in
        if pathtool.export_folder_path != "" and pathtool.material_indices_list_string != "":
            create_multiple_materials_shader_maps(context, pathtool, time_start)
        #or if the load image textures dynamically checkbox is false
        #only need one of the required fields the material indexes to be filled in
        elif pathtool.material_indices_list_string != "" and not(pathtool.is_load_img_textures):
            create_multiple_materials_shader_maps(context, pathtool, time_start)
            
        #else if required fields are missing
        else:
            error_message = "Error: One or more Required Fields, marked with (!) have not been filled in."
            bpy.ops.ueshaderscript.show_message(message = error_message)
            log(error_message)
        
        return {"FINISHED"}


#create multiple materials shader maps function
#just runs the create one shader map function multiple times
#for every material on the active object, checking if they are in the
#pathtool list
def create_multiple_materials_shader_maps(context, pathtool, time_start):
    #To get a specific material you have to use:
    #bpy.context.selected_objects[0].data.materials[0]
    
    #returns the active object, which means the last selected object
    #even if it is not selected at the current moment
    active_object = bpy.context.active_object

    material_indices_list_string = pathtool.material_indices_list_string
    
    #the active object cannot be nothing otherwise active_object.type
    #returns an error
    if active_object != None:
        #also make sure there is something in the material
        #indices input box
        if material_indices_list_string != "":
            #ignore any selected objects that are not meshes
            #because we can't shader maps to non-meshes
            if active_object.type == "MESH":
                #shade smooth on the active mesh
                #must use context.object.data
                #as part of bpy.ops
                #as bpy.ops.object.shade_smooth() as part of bpy.ops
                #not bpy.data
                mesh = active_object.data
                for f in mesh.polygons:
                    f.use_smooth = True
                
                #fetch all materials of the current selected object in a list
                active_object_materials_list = active_object.data.materials[:]

                
                materials_indices_to_add_list = material_indices_list_string.split(" ")

                #debug
                #print("materials_indices_to_add_list:", materials_indices_to_add_list)

                #before for loop set this
                #so it knows to use the normal search
                #as this is the first time calling find_props_txt_and_create_shader_map()
                previous_props_txt_folder = ""

                #create a shader map for each material in the materials list
                #in a loop
                #enumerate creates an index to come along with the each material
                for index, material in enumerate(active_object_materials_list):
                    #debug
                    #print("enumerate(active_object_materials_list)", enumerate(active_object_materials_list))
                    #print("index:", index)
                    #print("material", material)

                    #check if the material is one of the materials
                    #specified by the user to add a shader map to
                    #otherwise ignore it
                    #convert index to string because the indices list is
                    #made up of strings so compare strings to strings
                    string_index = str(index)
                    if string_index in materials_indices_to_add_list:
                        #if the string of the index has been found
                        #we will remove it from the list so we have less items
                        #to search through
                        materials_indices_to_add_list.remove(string_index)

                        #make sure to use nodes before anything else
                        #this is because if you don't have use nodes
                        #enabled, the material and material.name will not work properly
                        material.use_nodes = True
                        if(pathtool.is_load_img_textures):
                            previous_props_txt_folder = find_props_txt_and_create_shader_map(material, pathtool, active_object, previous_props_txt_folder)
                        else:
                            props_txt_path = "Not/Applicable"
                            create_one_shader_map(material, props_txt_path, pathtool)

                #remaining material slots/indexes
                #after all the found items have been 
                #deleted from the materials_indices_to_add_list
                #are the material slots/indexes that have not been found
                #show warning message for material indexes not found
                for not_found_material_index in materials_indices_to_add_list:
                    warning_message = " ".join(("Warning: The", not_found_material_index, "material slot was not found, please note that indexes start from 0."))
                    bpy.ops.ueshaderscript.show_message(message = warning_message)
                    log(warning_message)

                #print the time taken to finish creating shader maps
                #don't use log so can use new line characters
                #this is inside all the checks because we only print finished if an error hasn't occcured
                print("\n\n\n[UE Shader Script]: Finished create_multiple_materials_shader_maps in: %.4f sec" % (time.time() - time_start), "\n\n\n")
            

            #if the active object type is not a mesh
            else:
                error_message = "Error: Active Object is not a mesh, please select a mesh before pressing Add Shader Maps to Multiple Materials"
                bpy.ops.ueshaderscript.show_message(message = error_message)
                log(error_message)
        
        #if the material_indices_list_string is empty
        else:
            error_message = "Error: Material Indices List is empty, please enter integers separated by one space before pressing Add Shader Maps to Multiple Materials"
            bpy.ops.ueshaderscript.show_message(message = error_message)
            log(error_message)
            
    
    #if the active object does not exist
    else:
        error_message = "Error: No Active Object, please select a mesh before pressing Add Shader Maps to Multiple Materials"
        bpy.ops.ueshaderscript.show_message(message = error_message)
        log(error_message)



class LOADUESHADERSCRIPT_OT_add_to_selected_meshes(bpy.types.Operator):
    bl_label = "Add Shader Maps to ALL Selected Meshes"
    bl_description = "Add Shader Maps to all Materials on all Selected Meshes"
    bl_idname = "loadueshaderscript.add_to_selected_meshes_operator"
    def execute(self, context):
        #time how long it takes to create all shader maps for all materials
        #set start time
        time_start = time.time()

        scene = context.scene 
        #allow access to user inputted properties through pointer
        #to properties
        pathtool = scene.path_tool

        #check if required fields have been filled in
        #don't need the required field to be filled in
        #if load image textures is false
        if pathtool.export_folder_path != "" or not(pathtool.is_load_img_textures):
            create_selected_meshes_shader_maps(context, pathtool, time_start)

        #else if required fields are missing
        else:
            error_message = "Error: The Required Exported Game Folder Field, marked with (!) has not been filled in."
            bpy.ops.ueshaderscript.show_message(message = error_message)
            log(error_message)
    
        return {"FINISHED"}





#create selected meshes shader maps function
#just runs the create one shader map function
#for all selected objects, should be meshes and all materials
def create_selected_meshes_shader_maps(context, pathtool, time_start):
    #To get a specific material you have to use:
    #bpy.context.selected_objects[0].data.materials[0]
    
    #this makes a list of all selected objects (can be multiple)
    selected_objects_list = bpy.context.selected_objects
    
    #make sure that there are selected objects
    if selected_objects_list != []:
        #go through each selected object
        #and in every selected object
        #go through all of the selected object's materials
        for selected_obj in selected_objects_list: 
            #debug
            #print("selected_obj.name", selected_obj.name)
            #print("selected_obj.type", selected_obj.type)

            #ignore any selected objects that are not meshes
            #because we can't shader maps to non-meshes
            if selected_obj.type == "MESH":
                #shade smooth on the all selected meshes
                #inside loop
                #must use context.object.data
                #as part of bpy.ops
                #as bpy.ops.object.shade_smooth() as part of bpy.ops
                #not bpy.data
                mesh = selected_obj.data
                for f in mesh.polygons:
                    f.use_smooth = True

                #before for loop set this
                #so it knows to use the normal search
                #as this is the first time calling find_props_txt_and_create_shader_map()
                previous_props_txt_folder = ""
                
                #fetch all materials of the current selected object in a list
                selected_obj_materials_list = selected_obj.data.materials[:]
            
                #create a shader map for each material in the materials list
                #in a loop
                for material in selected_obj_materials_list:
                    #make sure to use nodes before anything else
                    #this is because if you don't have use nodes
                    #enabled, the material and material.name will not work properly
                    material.use_nodes = True
                    if(pathtool.is_load_img_textures):
                        previous_props_txt_folder = find_props_txt_and_create_shader_map(material, pathtool, selected_obj, previous_props_txt_folder)
                    else:
                        props_txt_path = "Not/Applicable"
                        create_one_shader_map(material, props_txt_path, pathtool)
            
            #if it is not a mesh do not show a warning as if the user
            #has a lot of non mesh objects this would issue many warnings
            #which might be very annoying
            #instead just ignore these non mesh objects
        

        #print the time taken to finish creating shader maps
        #don't use log so can use new line characters
        #this is inside all the checks because we only print finished if an error hasn't occcured
        print("\n\n\n[UE Shader Script]: Finished create_selected_meshes_shader_maps in: %.4f sec" % (time.time() - time_start), "\n\n\n")
    
    else:
        #error message if user has selected no meshes or objects
        error_message = "Error: No meshes selected, please select one or more meshes before pressing Add Shader Maps to ALL Selected Meshes"
        bpy.ops.ueshaderscript.show_message(message = error_message)
        log(error_message)

    



def find_props_txt_and_create_shader_map(material, pathtool, selected_obj, previous_props_txt_folder):
    #nested function has access to all the variables of the parent function
    def find_props_txt():
        props_txt_name = "".join((material.name, pathtool.props_txt_file_type))
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

 
        #go straight to checking the Exported Game folder
        props_txt_path = ""
        
        #default assume props txt exists and
        #correct assumption later if it doesn't or cannot be found
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
            
            #if the props_txt_path is still nothing
            #after second search in the game folder
            #show an error message and ignore the material
            #do not create a shader map for it
            if props_txt_path == "":
                warning_message = "".join(("Warning: the props.txt file for object \"", selected_obj.name, "\" material \"", material.name, 
                            "\" was not found in the Game Folder so the material was ignored!"))
                bpy.ops.ueshaderscript.show_message(message = warning_message)
                log(warning_message)
                is_props_txt_exist_for_material = False

                #if the props_txt file wasn't found
                #set the mat folder for the next loop to be nothing
                #so it doesn't try to use the previous_props_txt_folder
                previous_props_txt_folder = ""
            
            #if on the second search 
            #from the export game folder
            #the props_txt file is found 
            #set the props txt folder for
            #the next calling of find_props_txt_and_create_shader_map
            else:
                previous_props_txt_folder = os.path.dirname(props_txt_path)
        #if on the first serach
        #from the materials folder
        #the props_txt file is found
        #the next calling of find_props_txt_and_create_shader_map
        else:
            previous_props_txt_folder = os.path.dirname(props_txt_path)
        
        return props_txt_path, is_props_txt_exist_for_material, previous_props_txt_folder 
        #---------end nested function



    #if a valid props_txt file wasn't found last time or 
    #this is the first time going through the 
    #find_props_txt_and_create_shader_map function
    #do the normal rglob search
    if previous_props_txt_folder == "":
        props_txt_path, is_props_txt_exist_for_material, previous_props_txt_folder = find_props_txt()

    #otherwise check the folder
    #where the previous props_txt file was found 
    #to save time so the recursive glob doesn't need to go through so many folders
    else:
        props_txt_name = "".join((material.name, pathtool.props_txt_file_type))
        gen_obj_match = Path(previous_props_txt_folder).rglob(props_txt_name)
        props_txt_path = get_value_in_gen_obj(gen_obj_match)
        is_props_txt_exist_for_material = True

        #previous_props_txt_folder stays the same

        #if we can't find anything do the normal search
        if props_txt_path == "":
            props_txt_path, is_props_txt_exist_for_material, previous_props_txt_folder = find_props_txt()
        #debug
        #if found props.txt through previous folder
        # else:
        #     print("Found props.txt via previous folder")

    #not needed any more
    #get the current material's name to concatenate
    #a string the path to the props.txt file
    #props_txt_path = abs_mat_folder_path + material.name + ".props.txt"

    if (is_props_txt_exist_for_material):
        create_one_shader_map(material, props_txt_path, pathtool)
    
    #debug
    #print("previous_props_txt_folder:", previous_props_txt_folder)
    return previous_props_txt_folder


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


def create_one_shader_map(material, props_txt_path, pathtool):
    #do a check if saving the current add on preferences 
    #to the default add on preferences is required
    #This will either happen after blender is just opened and
    #the presets have been updated
    #or after the plugin is enabled in the Edit > Preferences > Add Ons panel
    #if so do it
    is_save_default_preferences = pathtool.is_save_to_default_preferences_on_next_load_shader_map
    #debug
    #print("is_save_default_preferences: ", is_save_default_preferences)
    if(is_save_default_preferences):
        save_pref()
        #set it to false as we have now saved to the default preferences
        #once after the plugin has been initialised
        pathtool.is_save_to_default_preferences_on_next_load_shader_map = False

    #only needed if the user selects to load image textures
    if(pathtool.is_load_img_textures):
        #convert windows path to string
        props_txt_path = str(props_txt_path)

        #if the folder path is a relative path
        #turn it into an absolute one
        #as relative paths cause problems
        #when trying to load an image
        #absolute paths will stay as absolute paths
        abs_props_txt_path =  bpy.path.abspath(props_txt_path)
    else:
        abs_props_txt_path = "Not/Applicable"

    #if bool is checked delete all nodes to create a clean slate 
    #for the new node map to be loaded
    if (pathtool.is_replace_nodes):
        tree = material.node_tree
        clear_nodes(tree)
        clear_links(tree)
    
    load_preset(material, abs_props_txt_path, pathtool)


def clear_nodes(tree):
    nodes = tree.nodes
    nodes.clear()


def clear_links(tree):
    links = tree.links
    links.clear()


def load_preset(material, abs_props_txt_path, pathtool):
    #area = context.area
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
        shader_type = nodes_dict["shader_type"]
        if shader_type == "OBJECT":
            #don't need this check because 
            #checks have already happened before it reaches this point
            #in the operators themselves
            # if bpy.context.object is None:
            #     bpy.ops.ueshaderscript.show_message(
            #         message = "Please choose a mesh in the 3D view to restore.")
            #     return {'FINISHED'}
            
            #this is from node kit use own method of loading shader map
            #later
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
        if pathtool.is_load_img_textures:
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

class LOADUESHADERSCRIPT_OT_solo_material(bpy.types.Operator):
    bl_label = "Solo Active Material for Active Mesh (Solo Use Nodes)"
    bl_description = "Use Nodes True for Active Material and False for Other Materials on Active Mesh"
    bl_idname = "loadueshaderscript.solo_material_operator"
    def execute(self, context):
        active_object = bpy.context.active_object

        if active_object != None:

            if active_object.type == "MESH":
                active_material = active_object.active_material

                if active_material != None:
                    
                    #set every material on the active object use_nodes to False
                    for mat_slot in active_object.material_slots:
                        #set all its materials Use Nodes attribute to False to Hide them
                        mat_slot.material.use_nodes = False
                    
                    #change the active material use_nodes back to True
                    active_material.use_nodes = True
                    
                #if the active material does not exist
                else:
                    error_message = "Error: There is no active material, please select a mesh and material before pressing Solo Material."
                    bpy.ops.ueshaderscript.show_message(message = error_message)
                    log(error_message)
            #if the active object is not a mesh
            else:
                error_message = "Error: The Active Object was not a Mesh, please select a mesh before pressing Solo Material."
                bpy.ops.ueshaderscript.show_message(message = error_message)
                log(error_message)
        
        #if the active object does not exist
        else:
            error_message = "Error: No Active Mesh was found, please select a mesh before pressing Solo Material."
            bpy.ops.ueshaderscript.show_message(message = error_message)
            log(error_message)
        
        return {"FINISHED"}


class LOADUESHADERSCRIPT_OT_solo_material_all(bpy.types.Operator):
    bl_label = "Solo Active Material for ALL Meshes (Solo Use Nodes)"
    bl_description = "Use Nodes True for Active Material and False for Other Materials on ALL Meshes"
    bl_idname = "loadueshaderscript.solo_material_all_operator"
    def execute(self, context):
        active_object = bpy.context.active_object

        if active_object != None:

            if active_object.type == "MESH":
                active_material = active_object.active_material

                if active_material != None:
                    #iterate through all objects in the current scene
                    for obj in bpy.context.scene.objects:
                        #if the object is a mesh
                        #set all its materials Use Nodes attribute to False to Hide them
                        if obj.type == 'MESH':
                            #set every material on the mesh use_nodes to False
                            for mat_slot in obj.material_slots:
                                mat_slot.material.use_nodes = False
                        
                    #change the active material use_nodes back to True
                    active_material.use_nodes = True
                    
                #if the active material does not exist
                else:
                    error_message = "Error: There is no active material, please select a mesh and material before pressing Solo Material."
                    bpy.ops.ueshaderscript.show_message(message = error_message)
                    log(error_message)
            #if the active object is not a mesh
            else:
                error_message = "Error: The Active Object was not a Mesh, please select a mesh before pressing Solo Material."
                bpy.ops.ueshaderscript.show_message(message = error_message)
                log(error_message)
        
        #if the active object does not exist
        else:
            error_message = "Error: No Active Mesh was found, please select a mesh before pressing Solo Material."
            bpy.ops.ueshaderscript.show_message(message = error_message)
            log(error_message)
        
        return {"FINISHED"}


class LOADUESHADERSCRIPT_OT_use_nodes_mesh(bpy.types.Operator):
    bl_label = "Use Nodes True for ALL Materials on Active Mesh"
    bl_description = "Make Use Nodes True for ALL Materials on Active Mesh"
    bl_idname = "loadueshaderscript.use_nodes_mesh_operator"
    def execute(self, context):
        active_object = bpy.context.active_object

        if active_object != None:

            if active_object.type == "MESH":
                active_material = active_object.active_material

                #need to check if there is no material slots
                #otherwise trying to use_nodes will cause an error
                if len(active_object.material_slots) != 0:
                    
                    #set every material on the active object use_nodes to False
                    for mat_slot in active_object.material_slots:
                        mat_slot.material.use_nodes = True

                #if there are no material slots on the active mesh
                else:
                    error_message = "Error: There are no materials on the active mesh, please select a mesh with materials before pressing Use Nodes."
                    bpy.ops.ueshaderscript.show_message(message = error_message)
                    log(error_message)
            #if the active object is not a mesh
            else:
                error_message = "Error: The Active Object was not a Mesh, please select a mesh before pressing Use Nodes."
                bpy.ops.ueshaderscript.show_message(message = error_message)
                log(error_message)
        
        #if the active object does not exist
        else:
            error_message = "Error: No Active Mesh was found, please select a mesh before pressing Use Nodes."
            bpy.ops.ueshaderscript.show_message(message = error_message)
            log(error_message)
        
        return {"FINISHED"}


class LOADUESHADERSCRIPT_OT_use_nodes_mesh_all(bpy.types.Operator):
    bl_label = "Use Nodes True for ALL Materials on ALL Meshes"
    bl_description = "Make Use Nodes True for ALL Materials on ALL Meshes"
    bl_idname = "loadueshaderscript.use_nodes_mesh_all_operator"
    def execute(self, context):
        scene_objects_list = bpy.context.scene.objects
        #if there are objects in the scene
        if len(scene_objects_list) != 0:
            #iterate through all the objects in the scene
            for obj in scene_objects_list:
                #if the object is a mesh
                #set all the material Use Nodes attributes to True to show them
                if obj.type == 'MESH':
                    #set every material on the mesh use_nodes to True
                    for mat_slot in obj.material_slots:
                        mat_slot.material.use_nodes = True
        else:
            #if the length of the scene objects list is 0
            #which means there are no scene objects send a warning
            #since nothing will happen
            error_message = "Error: There are no Meshes in the scene, make sure there are before pressing Use Nodes."
            bpy.ops.ueshaderscript.show_message(message = error_message)
            log(error_message)

        return {"FINISHED"}

#-----------------------------------Load Compositing Node Setup
class LOADUESHADERSCRIPT_OT_use_custom_denoising(bpy.types.Operator):
    bl_label = "Use Pit Princess Custom Denoising Setup"
    bl_description = "Use Pit Princess Compositor Denoising Setup"
    bl_idname = "loadueshaderscript.use_custom_denoising_operator"
    def execute(self, context):
        #change render engine to Cycles and GPU Compute
        bpy.context.scene.render.engine = 'CYCLES'
        bpy.context.scene.cycles.device = 'GPU'

        #change to branched path tracing
        #and assign samples to each
        bpy.context.scene.cycles.progressive = 'BRANCHED_PATH'
        bpy.context.scene.cycles.aa_samples = 8
        bpy.context.scene.cycles.preview_aa_samples = 8
        bpy.context.scene.cycles.diffuse_samples = 3
        bpy.context.scene.cycles.glossy_samples = 5
        bpy.context.scene.cycles.transmission_samples = 7
        bpy.context.scene.cycles.ao_samples = 1
        bpy.context.scene.cycles.mesh_light_samples = 1
        bpy.context.scene.cycles.volume_samples = 1
        bpy.context.scene.cycles.subsurface_samples = 9

        #turn on the required render passes
        #have to use bpy.context.view_layer.cycles.denoising_store_passes = False
        #even though the info console does not show it properly
        #as there are different settings for eevee and cycles
        bpy.context.scene.view_layers["View Layer"].use_pass_combined = True
        bpy.context.scene.view_layers["View Layer"].use_pass_z = False
        bpy.context.scene.view_layers["View Layer"].use_pass_mist = False
        bpy.context.scene.view_layers["View Layer"].use_pass_normal = True
        bpy.context.scene.view_layers["View Layer"].use_pass_vector = False
        bpy.context.scene.view_layers["View Layer"].use_pass_uv = False
        bpy.context.view_layer.cycles.denoising_store_passes = False
        bpy.context.scene.view_layers["View Layer"].use_pass_object_index = False
        bpy.context.scene.view_layers["View Layer"].use_pass_material_index = False
        bpy.context.view_layer.cycles.pass_debug_render_time = False
        bpy.context.view_layer.cycles.pass_debug_sample_count = False
        bpy.context.scene.view_layers["View Layer"].use_pass_diffuse_direct = True
        bpy.context.scene.view_layers["View Layer"].use_pass_diffuse_indirect = True
        bpy.context.scene.view_layers["View Layer"].use_pass_diffuse_color = True
        bpy.context.scene.view_layers["View Layer"].use_pass_glossy_direct = True
        bpy.context.scene.view_layers["View Layer"].use_pass_glossy_indirect = True
        bpy.context.scene.view_layers["View Layer"].use_pass_glossy_color = True
        bpy.context.scene.view_layers["View Layer"].use_pass_transmission_direct = True
        bpy.context.scene.view_layers["View Layer"].use_pass_transmission_indirect = True
        bpy.context.scene.view_layers["View Layer"].use_pass_transmission_color = True
        bpy.context.view_layer.cycles.use_pass_volume_direct = True
        bpy.context.view_layer.cycles.use_pass_volume_indirect = True
        bpy.context.scene.view_layers["View Layer"].use_pass_emit = True
        bpy.context.scene.view_layers["View Layer"].use_pass_environment = True
        bpy.context.scene.view_layers["View Layer"].use_pass_shadow = True
        bpy.context.scene.view_layers["View Layer"].use_pass_ambient_occlusion = True

        #make use nodes true in the compositor
        bpy.context.scene.use_nodes = True

        #this gets the path of the currently running file
        #load_shader_map and then gets it's parent
        #and then converts the relative path into an absolute path
        path_lib = pathlib.Path(__file__).parent.absolute()

        compositing_file_path= os.path.join(path_lib, "ue_shader_script_compositing_json.json")
        
        #------------load the compositing node setup to the compositor window
        #reading string from file because it would take up too much space in the code
        #will read from the file compositing json in the current directory by default
        file = open(compositing_file_path)
        pit_princess_compositing_json = file.read()

        file.close()
        nodes_dict = json_to_nodes_dict(pit_princess_compositing_json)
        node_tree = bpy.context.scene.node_tree
        
        clear_nodes(node_tree)
        clear_links(node_tree)

        nodes = dict_to_nodes(nodes_dict["nodes_list"], node_tree)
        list_to_links(nodes_dict["links_list"], node_tree, nodes)

        #show feedback to user
        success_message = "Custom Denoising Setup was added succesfully!"
        bpy.ops.ueshaderscript.show_message(
            message = success_message)
        #show success message in blender console
        log(success_message)

        return {'FINISHED'}


def get_active_world():
    world = bpy.context.scene.world
    if world:
        world.use_nodes = True
        return world
    new_world = bpy.data.worlds.new(name="World")
    new_world.use_nodes = True
    bpy.context.scene.world = new_world
    return new_world


# def add_material_to_active_object():
#     obj_data = bpy.context.object.data
#     obj = bpy.context.object
#     if obj.active_material:
#         obj.active_material.use_nodes = True
#         return obj.active_material
#     new_mat = bpy.data.materials.new("Material")
#     new_mat.use_nodes = True
#     obj_data.materials.append(new_mat)
#     obj.active_material = new_mat
#     return new_mat

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
        # Special handling ShaderNodeGroup
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
    #nested function so that don't have to copy all 
    #attributes
    def check_should_load_image():
        #nested function inside nested function so that don't have to copy all 
        #attributes
        def if_tex_location_suffix_match_load_image():
            #by default assume no image has been loaded
            is_img_loaded = False
            #check what the last two/three characters are of the id
            #and look for the specific ids we are interested in
            #identifier
            #tex_location is from the props txt file comparing against 
            #suffix which is what is recorded from the node_dict
            #the suffix also cannot be an accidental empty space
            if tex_location.endswith(suffix) and suffix != "":
                #looks like this normally
                #node_to_load = bpy.context.active_object.active_material.node_tree.nodes["Diffuse Node"]
                #node_to_load.image = bpy.data.images.load("C:\Seabrook\Dwight Recolor\Game\Characters\Campers\Dwight\Textures\Outfit01\T_DFHair01_BC.tga")

                #use node_tree which is the current node tree
                #we're trying to texture
                #and node_name which is the Node Name in the Items panel in the shader editor
                #this will uniquely identify a single node
                node_to_load = node_tree.nodes[node_name]
                load_image_texture(node_to_load, complete_path, pathtool)

                #change the color space to the user selected color space
                change_colour_space(textures["texture"], node_to_load, pathtool)

                #this handles special nodes e.g.
                #a Transparency node has been loaded 
                #we might need to make the material Alpha Clip or Alpha hashed
                #special handler does that
                img_textures_special_handler(textures, pathtool, material, node_to_load, node_tree, abs_props_txt_path)
                
                    
                #if an image texture node has been loaded
                #and the option to delete image texture nodes who
                #have not had an image loaded to them is True
                #then we will add it to a whitelist
                #so it does not get deleted
                if pathtool.is_delete_unused_img_texture_nodes:
                    not_delete_img_texture_node_name_list.append(node_to_load.name)
                
                is_img_loaded = True
            if suffix == "":
                warning_message = " ".join(("Warning:", node_name, "has an empty suffix that was ignored, likely from an extra space, please remake this shader map!"))
                bpy.ops.ueshaderscript.show_message(message = warning_message)
            return is_img_loaded


        
        complete_path = get_complete_path_to_texture_file(pathtool, tex_location)


        is_img_loaded = False

        #If the texture is listed in the 
        #props.txt file and it is one of the
        #image textures we are interested in we will
        #load the corresponding image
        
        #this for loop will load all image textures
        #via reading the img_textures_list
        #recorded in the node_dict when the dictionary is saved
        #it will iterate through the preset's recorded suffixes
        #one by one and check if the tex location from the props.txt file is matches it
        for textures in img_textures_list:
            suffix_list = textures["suffix_list"]
            node_name = textures["node_name"]

            #we must check a match against all the suffixes in the suffix list
            #one texture may have one to many suffixes e.g. transparency might have "_M", "_A"
            for suffix in suffix_list:
                is_img_loaded = if_tex_location_suffix_match_load_image()

                #break out of current loop of for tex_location in match_list 
                #because the image for the tex_location has been found
                #there is no need to check against the next suffixes
                #e.g for tex_location '/Game/Characters/Slashers/Doctor/Textures/Outfit011/T_DOStraps011_BC'
                #in the suffix_list 'suffix_list': ['_BC', '_BC_01', '_BC_02', '_BC_03', '_BC_04'], '_BC' was a
                #match, thus, the image was T_DOStraps011_BC.tga/png was loaded to the image texture node
                if is_img_loaded:
                    return is_img_loaded
            
        #if the image file name wasn't found in the suffix lists for any of Diffuse, ORM, or any other one 
        #so the image from the props.txt file was NOT loaded to an image texture node
        #this is an extra protection because if it's the opposite and is_img_loaded
        #is true it should've returned to the calling function before this point
        #and the settings boolean to add the image texture to an unconnected
        #node is enabled
        #create an empty image texture node
        #load the image texture to it  
        if ((not is_img_loaded) and pathtool.is_add_non_match_textures):
            #create an empty image texture node
            img_tex_node = node_tree.nodes.new("ShaderNodeTexImage")

            #move the empty node to the left so it doesn't mix with other nodes
            img_tex_node.location.x = -1200
            
            #load the image texture to the empty image texture node
            load_image_texture(img_tex_node, complete_path, pathtool)

            #change the image texture node color 
            #space to the user selected color space
            img_tex_node.image.colorspace_settings.name = pathtool.non_match_color_space

        #if no match was found for the specific texture and
        #the boolean to show the textures that had no suffix match is enabled
        #print these to console for debugging purposes so can create better 
        if ((not is_img_loaded) and pathtool.is_show_no_match_tex_debug):
            print("\nNo match for texture:", complete_path, "in material:", abs_props_txt_path)

                





    #now outside the nested function
    #show the props txt path in the system console
    #if the option to show it is enabled
    if pathtool.is_show_abs_props_debug:
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
        #match_list = re.findall("Texture2D\'(.*)\.", data)
        match_list = re.findall(pathtool.regex_pattern_in_props_txt_file, data)

        #reverse match list as in the case of overlap the most 
        #important materials are listed first
        #want the final image textures on the object to be the 
        #most important ones
        #convention says the most important textures that want to be last
        #in the case of overlap should be written first in the props.txt file
        if pathtool.reverse_match_list_from_props_txt_enum == "Reverse Match List":
            match_list = reversed(match_list)
        #if it is false Don't Reverse Match List don't do anything

    #---------------------add image texture nodes 
    

    #-------used if delete unused image texture nodes is true
    #list of the possible nodes that may be deleted
    #use this because we only want delete image texture nodes
    #that might have had something loaded to them but didn't
    #not random image texture nodes
    interested_node_name_list = []
    #whitelist for image texture nodes that have been loaded
    not_delete_img_texture_node_name_list = []

    #use loop to go through all locations
    #specified in props.txt file
    #and create image texture nodes + 
    #load all images for image textures
    #debug
    #print("match_list:", match_list, "\n")
    #print("img_textures_list:", img_textures_list, "\n")
    
    #if either of these conditions is true we must iterate 
    #through the image textures list
    #once
    if (pathtool.is_delete_unused_img_texture_nodes or pathtool.is_add_skin_bump_map):
        #go through the textures list once to load all the node_names to interested_node_name_list
        #we are interested in that might have something loaded to them
        #if nothing is loaded to the nodes from interested_node_name_list
        #we know they should be deleted
        #also go through textures list to load the skin texture if it is needed
        for textures in img_textures_list:
            node_name = textures["node_name"]
            texture_id = textures["texture"]
            #list of the possible nodes that may be deleted
            #use this because we only want delete image texture nodes
            #that could have had something in them
            #not random image texture nodes
            if pathtool.is_delete_unused_img_texture_nodes:
                interested_node_name_list.append(node_name)
            
            if (pathtool.is_add_skin_bump_map):
                load_skin_bump_texture_if_needed(node_tree, pathtool, img_textures_list, not_delete_img_texture_node_name_list, node_name, texture_id)

    #iterate through texture locations
    #reminder match list looks like
    #match_list ['/Game/Characters/Slashers/Doctor/Textures/Outfit011/T_DOStraps011_BC', 
    #'/Game/Characters/Slashers/Doctor/Textures/Outfit011/T_DOStraps011_ORM', 
    # '/Game/Characters/Slashers/Doctor/Textures/Outfit011/T_DOStraps011_N']
    for tex_location in match_list:
        check_should_load_image()
    
    #will delete img_texture_nodes if needed
    delete_unused_img_texture_nodes_and_related_nodes(not_delete_img_texture_node_name_list, 
            interested_node_name_list, pathtool, node_tree)
       


def get_complete_path_to_texture_file(pathtool, tex_location):
    #if the folder path is a relative path
    #turn it into an absolute one
    #as relative paths cause problems
    #when trying to load an image
    #looks like C:\Nyan\Dwight Recolor\Game\
    abs_export_folder_path = bpy.path.abspath(pathtool.export_folder_path)
    
    #replace forward slash with backslash reason why is
    #when concatenating complete path looks like this
    #if no replace path looks like e.g. C:\Nyan\Dwight Recolor\/Game/Characters/Slashers/Bear/Textures/Outfit01/T_BEHead01_BC
    #which is weird
    #backslash is used to escape backslash character
    #if no forward slash is found this does nothing
    #so it is still okay
    tex_location = tex_location.replace("/","\\")


    #now abs_export_folder_path looks like
    #C:\Nyan\Dwight Recolor\Game\
    #and tex_location looks like \Game\Characters\Slashers\Bear\Textures\Outfit01\T_BEHead01_BC
    #concatenate the two strings merging overlapping parts
    texture_path = overlap_concat_string(abs_export_folder_path, tex_location)
    
    #debug
    #print("texture_path", texture_path)

    #must string concatenate the user specified texture location path to 
    #the texture location
    #as the tex_location will only be 
    #e.g /Game/Characters/Slashers/Bear/Textures/Outfit01/T_BEHead01_BC
    #this does not provide a complete path to where the user exported
    #the texture
    #we need e.g. C:\Nyan\Dwight Recolor\Game\Characters
    #\Slashers\Bear\Textures\Outfit01\T_BEHead01_BC
    #using pathtool.texture_file_type_enum because it may be ".tga" or ".png"
    complete_path = "".join((texture_path, pathtool.texture_file_type_enum))
    return complete_path

#concatenates two strings by merging overlapping parts
#at the end of the string 1 and the start of string 2
def overlap_concat_string(string1, string2):
    len_s1 = len(string1)
    len_s2 = len(string2)

    #create sequence from 0 to len_s1 - 1
    #iterate over string 1 indexes
    #use reversed so we're iterating through the 
    #first string backwards where the match should be
    for current_index_s1 in range(len_s1):
        char_index_s1 = current_index_s1
        #checking from the start of string 2 for a match
        char_index_s2 = 0

        # #debug
        # current_char_s1 = string1[char_index_s1]
        # current_char_s2 =  string2[char_index_s2]
        # print("current_char_s1:", current_char_s1)
        # print("current_char_s2:", current_char_s2)

        #repeat while loop
        #we are iterating forwards through
        #so we must make sure that char_index_s1 does not reach the length of string 1
        #we are iterating forwards through string 2
        #so char_index_s2 must not reach the length of string 2
        #because otherwise we would be checking for non existent indexes 
        #in strings
        #we must also check whether to continue based on if the current character
        #for string 1 is equal to the current character for string 2
        #so we know if we're encountering a matched part
        while (char_index_s1 < len_s1 and char_index_s2 < len_s2 and 
                     string1[char_index_s1] == string2[char_index_s2]):
            char_index_s1 = char_index_s1 + 1
            char_index_s2 = char_index_s2 + 1
            
            # #debug
            # #even the debug needs a check otherwise will try to print
            # #a char that is out of range
            # if (char_index_s1 < len_s1 and char_index_s2 < len_s2):
            #     current_char_s1 = string1[char_index_s1]
            #     current_char_s2 =  string2[char_index_s2]
            #     print("current_char_s1:", current_char_s1)
            #     print("current_char_s2:", current_char_s2)

        
        #if the index is equal to the length of the string
        #all characters have been checked in the string
        #and there are two cases: 
        #1. It was a match until the end of the string
        #so char_index_s2 is not 0 and we are only
        #taking the part that is unique from string 2
        if char_index_s1 == len_s1:
            n = char_index_s2

            #break from for loop
            #if the full match has been found
            break
    
        else:
            #2. else is only reached if there was no matching parts
            #in string 1 and string 2 to merge
            #so n = 0 so that we can take the full string 2
            n = 0
    return string1 + string2[n:]


#default global variables for the recommended 
#colour spaces for image textures
#srgb color space isn't used but it is there for reference purposes
# srgb_color_space_list = ["diffuse", "tint_base_diffuse", "cust1", "cust2", "cust3", "cust4"]
# non_color_space_list = ["normal", "packed_orm", "emissive", "tint_mask", "specular", "gloss"]
# linear_color_space_list = ["transparency", "height", "hair_gradient", "skin_bump"]
# using the names defined in save_shader_map.py in the suffix_and_node_name_to_list() function

def change_colour_space(texture, node_to_load, pathtool):
    if texture == "diffuse":
        node_to_load.image.colorspace_settings.name = pathtool.diffuse_color_space
    elif texture == "packed_orm":
        node_to_load.image.colorspace_settings.name = pathtool.packed_rgb_color_space
    elif texture == "normal":
        node_to_load.image.colorspace_settings.name = pathtool.normal_color_space
    elif texture == "transparency":
        node_to_load.image.colorspace_settings.name = pathtool.alpha_color_space
    elif texture == "emissive":
        node_to_load.image.colorspace_settings.name = pathtool.emissions_color_space
    elif texture == "height":
        node_to_load.image.colorspace_settings.name = pathtool.height_color_space
    elif texture == "hair_gradient":
        node_to_load.image.colorspace_settings.name = pathtool.hair_gradient_color_space
    elif texture == "specular":
        node_to_load.image.colorspace_settings.name = pathtool.specular_color_space
    elif texture == "gloss":
        node_to_load.image.colorspace_settings.name = pathtool.gloss_color_space
    elif texture == "tint_base_diffuse":
        node_to_load.image.colorspace_settings.name = pathtool.tint_base_diffuse_color_space
    elif texture == "tint_mask":
        node_to_load.image.colorspace_settings.name = pathtool.tint_mask_color_space
    elif texture == "skin_bump":
        node_to_load.image.colorspace_settings.name = pathtool.skin_bump_color_space
    elif texture == "cust1":
        node_to_load.image.colorspace_settings.name = pathtool.cust1_color_space
    elif texture == "cust2":
        node_to_load.image.colorspace_settings.name = pathtool.cust2_color_space
    elif texture == "cust3":
        node_to_load.image.colorspace_settings.name = pathtool.cust3_color_space
    elif texture == "cust4":
        node_to_load.image.colorspace_settings.name = pathtool.cust4_color_space
    else:
        error_message = " ".join(("Error: No texture called:", texture, "was found to change the color space!"))
        bpy.ops.ueshaderscript.show_message(message = error_message)
        log(error_message)



# using the names defined in save_shader_map.py in the suffix_and_node_name_to_list() function
def img_textures_special_handler(textures, pathtool, material, node_to_load, node_tree, abs_props_txt_path):
    #special case if the node that was loaded was a transparency node _M
    #we need to set the material blend_method to alpha clip
    #and set the alpha threshold to 0 which looks best
    #with the least clipped
    if textures["texture"] == "transparency":        
        #change clipping method + threshold to clip
        clipping_method = pathtool.clipping_method_enum
        if clipping_method == "HASHED":
            material.blend_method = "HASHED"
            material.shadow_method = "HASHED" 
        elif clipping_method == "CLIP":
            material.blend_method = "CLIP"
            material.shadow_method = "CLIP"
            material.alpha_threshold = pathtool.material_alpha_threshold
        else:
            error_message = "Error: could not find clipping method"
            bpy.ops.ueshaderscript.show_message(message = error_message)
            log(error_message)

    #special case if the node loaded was an emissive BDE
    #check through the props.txt file for emissive RGB values
    #and if they exist use those rgb values
    #find the principled BSDF node
    #and turn the emission strength to 5
    elif textures["texture"] == "emissive":
        use_props_txt_emissive_rgb_values(node_tree, abs_props_txt_path)
        #only change the emission strength if the bool checkbox is checked
        if (pathtool.is_change_principle_bsdf_emission_strength):
            change_emission_strength_principled_bsdf(node_tree, "BSDF_PRINCIPLED", pathtool.principled_bsdf_emission_strength_float)
    
    #so this is only for one specific 
    #preset DBD Pit Princess's Clothing Recolor Preset
    #if it is being used we want to read the props.txt file
    #for more details specifically the RGB colours used for the recolor
    #we will only look for the occurence of the tint_base_diffuse
    #and not the tint mask
    #because one will tell us the preset is the recolor preset
    #and we only need to adjust the values of the dye group node
    elif textures["texture"] == "tint_base_diffuse":
        #if the user has checked the option to use
        #the values that come from the props.txt file
        #then change the dye group values
        #to match the props.txt values
        if pathtool.is_use_recolor_values:
            change_dye_group_values(node_tree, abs_props_txt_path)

#this has to deal with two cases
def use_props_txt_emissive_rgb_values(node_tree, abs_props_txt_path):
    is_frutto_roman_emissive_group_found, frutto_roman_emissive_node_group = search_return_node_by_name(node_tree, "Frutto Roman DBD BDE")
    is_pit_princess_emissive_group_found, pit_princess_emissive_node_group = search_return_node_by_name(node_tree, "Pit Princess Lazy DBD BDE")

    if is_frutto_roman_emissive_group_found or is_pit_princess_emissive_group_found:
        #open the propstxt file for the material and find the
        #texture locations from it
        #with just means open and close file
        with open(abs_props_txt_path, 'r') as f:
            #read entire file to one string
            data = f.read()
            #find all matches through regex to the string:
            #EM Color }
            #ParameterValue = { R=1, G=1, B=1, A=1 }
            #Syntax:
            #[\s\S] any whitespace or non whitespace character to jump over new lines
            #[\s\S]* previous line zero to unlimited times
            #[\s\S]*? previous line non greedy match as little as possible
            #.* match any character zero to unlimited times
            #.+ any character one to unlimited times 
            #Explaining how it works:
            #1st[0] capture group is Red value
            #2nd[1] capture group is Green value
            #3rd[2] capture group is Blue value
            #4th[3] capture group is Alpha value
            match_list = re.findall("EM Color[\s\S]*?ParameterValue.*R=(.+), G=(.+), B=(.+), A=(.+) }", data)

        #debug
        #print("match_list", match_list)

        #if didn't find anything in the regex match
        #re.findall will return an empty list []
        #so will iterate zero times and will NOT try 
        #to change any values

        #iterate over all capture groups in match list
        #and put all the values found from the regular expression
        #into the group node
        for capture_group in match_list:
            #example of how to assign colour
            #bpy.data.materials["Example Clothing"].node_tree.nodes["Pit Princess Lazy DBD BDE"].inputs["Secondary Colour"].default_value = (0.5, 0.125, 0.125, 1)

            #set the RGB values for the default emissive node groups 

            #the four elements in the tuple for default_value are the (Red, Green, Blue and Alpha) 
            
            #always use default of value of 1 for alpha, the fourth value because RGB Alpha values
            #since alpha value doesn't do much in blender leave it at it's default 1
            #need to convert strings to float so use float()
            if is_frutto_roman_emissive_group_found:
                frutto_roman_emissive_node_group.inputs["Emission Colour"].default_value = (float(capture_group[0]), float(capture_group[1]), float(capture_group[2]), float(capture_group[3]))

            if is_pit_princess_emissive_group_found:
                pit_princess_emissive_node_group.inputs["Secondary Colour"].default_value = (float(capture_group[0]), float(capture_group[1]), float(capture_group[2]), float(capture_group[3]))




def change_dye_group_values(node_tree, abs_props_txt_path):
    is_dye_node_group_found, dye_node_group = search_return_node_by_name(node_tree, "Pit Princess Lazy DBD Clothing (Dye)")

    #print("abs_props_txt_path: ", abs_props_txt_path)
    
    #if the dye group node is found we will
    #read the props txt file for the RChannel GChannel and 
    #BChannel values and put the values into the group node
    #if the dye group node is not found do nothing
    if is_dye_node_group_found:
        #open the propstxt file for the material and find the
        #texture locations from it
        #with just means open and close file
        with open(abs_props_txt_path, 'r') as f:
            #read entire file to one string
            data = f.read()
            #find all matches through regex to the string:
            #Channel_Tint }
            #ParameterValue = { R=1, G=1, B=1, A=1 }
            #Syntax:
            #[A-Z] capital A-Z
            #[\s\S] any whitespace or non whitespace character to jump over new lines
            #[\s\S]* previous line zero to unlimited times
            #[\s\S]*? previous line non greedy match as little as possible
            #.* match any character zero to unlimited times
            #.+ any character one to unlimited times 
            #Explaining how it works:
            #1st[0] capture group is capital A-Z telling you what channel it is for Red, Green, Blue or Alpha
            #2nd[1] capture group is Red value
            #3rd[2] capture group is Green value
            #4th[3] capture group is Blue value
            #5th[4] capture group is Alpha value

            match_list = re.findall("([A-Z])Channel_Tint[\s\S]*?ParameterValue.*R=(.+), G=(.+), B=(.+), A=(.+) }", data)



        #debug
        #print("match_list", match_list)

        #if didn't find anything in the regex match
        #re.findall will return an empty list []
        #so will iterate zero times and will NOT try 
        #to change any values

        #iterate over all capture groups in match list
        #and put all the values found from the regular expression
        #into the group node
        for capture_group in match_list:
            colour_channel = ""
            if capture_group[0] == "R":
                colour_channel = "(R) Primary"
            elif capture_group[0] == "G":
                colour_channel = "(G) Secondary"
            elif capture_group[0] == "B":
                colour_channel = "(B) Tertiary"
            elif capture_group[0] == "A":
                colour_channel = "(A) Quaternary"

            #using .join to concatenate strings as it's faster
            #and more efficient remember using .join you always need a tuple
            #so two circular brackets one for tuple one for function

            #example of how to assign colour
            #bpy.data.materials["Example Clothing"].node_tree.nodes["Clothing Dye"].inputs[3].default_value = (0.5, 0.125, 0.125, 1)

            #set the RGB values on pit princess's dye node to match what the props.txt file
            #RGB colours should be for the specific preset
            #The inputs to pit princess's dye group node are labelled 
            #"(R) Primary Colour", "(G) Secondary Colour", "(B) Tertiary Colour" and "(A) Quaternary Colour" 
            #following the system BHVR uses to recolour Dead By Daylight meshes  

            #the four elements in the tuple for default_value are the (Red, Green, Blue and Alpha) 
            #values for each Primary, Secondary, Tertiary and Quaternary Channel
            
            #always use default of value of 1 for alpha, the fourth value because RGB Alpha values
            #since alpha value doesn't do much in blender leave it at it's default 1
            #need to convert strings to float so use float()
            dye_node_group.inputs["".join((colour_channel, " Colour"))].default_value = (float(capture_group[1]), float(capture_group[2]), float(capture_group[3]), 1)
            #commented out this because there is no longer an alpha input for the
            #dye node group because the A value was deemed unhelpful
            #for recolors
            #only here so that float(capture_group[4]) that 
            #might possibly be useful in future
            #dye_node_group.inputs["".join((colour_channel, " Alpha"))].default_value = float(capture_group[4])


#works for both node groups and nodes
#searches by name 
#if it finds the node in the node tree it will:
#return True for is_node_found and also return the found_node as a class
#if it does NOT find the node in the node tree it will:
#return False for is_node_found and the found_node as None
def search_return_node_by_name(node_tree, node_name):
    is_node_found = False

    #give default value for found_node
    #just in case a node is not found
    found_node = None

    for node in node_tree.nodes:
            #so if a group node exists that is the Lazy DBD X.X Clothing Dye
            #which is identified by the node.name of Clothing Dye
            #we will read the props.txt file for the RGB colours
            if (node.name == node_name):
                is_node_found = True
                found_node = node
                #debug
                #print("Node exists")
                

                #break from for loop
                break
     
    #debug
    #if the node is not found 
    #if (not is_node_found):
    # print("Node does not exist")
    
    return is_node_found, found_node


def load_image_texture(node_to_load, complete_path_to_image, pathtool):
    #if the user has chosen to reuse node groups we must check 
    #whether a node group exists to be reused 
    if(pathtool.is_reuse_img_texture_with_same_name):
        check_if_should_reuse_img_texture(node_to_load, complete_path_to_image, pathtool.texture_file_type_enum)
    else:
        #else if the user has chosen not to reuse node groups create new node groups
        #whether or not they already exist
        create_a_new_img_texture(node_to_load, complete_path_to_image, pathtool.texture_file_type_enum)


def delete_unused_img_texture_nodes_and_related_nodes(not_delete_img_texture_node_name_list, interested_node_name_list, pathtool, node_tree):
    #debug
    #print("not_delete_img_texture_node_name_list:", not_delete_img_texture_node_name_list)
    #print("interested_node_name_list:", interested_node_name_list)

    #only start deleting nodes after all textures have been
    #loaded for one shader map
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
            node_name = node.name
            #if it's not in the whitelist and it's in our interested nodes list which means 
            #an image wasn't loaded to the interested image texture node, delete the image texture node
            if node.type == "TEX_IMAGE" and not(node_name in not_delete_img_texture_node_name_list) and (node_name in interested_node_name_list): 
                #delete node and mark all related nodes to delete list
                #that is mark all nodes which starts with the same name
                prefix_of_related_nodes_to_delete.append(node_name)
                nodes.remove(node)

                #special case for emissive nodes
                #because the emissive group nodes for the default presets are called
                #"Frutto Roman DBD BDE" and "Pit Princess Lazy DBD BDE"
                #and they should be added to the list of nodes to be deleted
                #if no image texture was loaded to the emissions map node
                if node_name == "Emissions Map Node":
                    #debug
                    #print("Frutto Roman and Pit Princess's nodes were added to be delete list")

                    prefix_of_related_nodes_to_delete.append("Frutto Roman DBD BDE")
                    prefix_of_related_nodes_to_delete.append("Pit Princess Lazy DBD BDE")
        
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



def load_skin_bump_texture_if_needed(node_tree, pathtool, img_textures_list, not_delete_img_texture_node_name_list, node_name, texture_id):
    #turn the path to the skin bump map to an absolute path instead of a relative one
    #to avoid errors
    abs_skin_bump_map_path = bpy.path.abspath(pathtool.skin_bump_map_path)
    #if the node is a skin texture node
    #always load skin height map texture regardless
    #because it doesn't come from the props.txt file
    #it is externally added from skin_bump_map_path
    #and the skin_bump_map path is not empty
    #so do not need to check the suffix for a match against the propstxt file
    #always load
    #also require that is_add_skin_bump_map is checked by the user to add a skin bump map
    if  texture_id == "skin_bump" and abs_skin_bump_map_path !="" and pathtool.is_add_skin_bump_map:
        node_to_load = node_tree.nodes[node_name]
        #bpy.data.images.load(abs_skin_bump_map_path)
        load_image_texture(node_to_load, abs_skin_bump_map_path, pathtool)
        #add to whitelist
        if pathtool.is_delete_unused_img_texture_nodes:
            not_delete_img_texture_node_name_list.append(node_to_load.name)



def check_if_should_reuse_img_texture(node_to_load, complete_path_to_image, texture_file_type):
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
        create_a_new_img_texture(node_to_load, complete_path_to_image, texture_file_type)


def create_a_new_img_texture(node_to_load, complete_path_to_image, texture_file_type):
    #do a try and exception because some files 
    #do not always match the texture_file_type_enum
    #some will be not be whatever extension the user selected .tga/.png 
    #but instead .hdr or something else

    #We do it only in this function and not in reuse_the_img_texture() because if it is going into
    #reuse_the_img_texture() there is no need to look for the img texture it has already
    #been successfully added to the blend file
    try:
        node_to_load.image = bpy.data.images.load(complete_path_to_image)
    except:
        #replace texture_file_type_enum with nothing to get rid of extension
        file_no_ext = replace_ending(complete_path_to_image, texture_file_type, "")
        #use .join() as it is more efficient 
        #need two brackets because .join only acccepts tuples
        #tuples defined by another set of brackets and commas ()
        glob_wildcard_file_path = "".join((file_no_ext, "*"))
        #will return a list of matching files with matching file name with extensions
        #e.g. ['C:/Blender/xxx/images/White_Linear.hdr', 'C:/Blender/xxx/images/doc.dds']
        complete_path_match_list = glob.glob(glob_wildcard_file_path)

        #debug
        #print("complete_path_match_list", complete_path_match_list)

        #if the match returned some results and
        #not nothing then load the image texture
        if complete_path_match_list != []:
            #for every item in the complete_path_match_list
            #load it to the image texture
            #even though it should only be one item in the list
            for path in complete_path_match_list:
                node_to_load.image = bpy.data.images.load(path)
        
        #if nothing was found by the glob and it the match list is an empty list
        else:
            warning_message = " ".join(("Error: No matching textures with file path", file_no_ext, "was found to load!"))
            bpy.ops.ueshaderscript.show_message(message = warning_message)
            log(warning_message)
        
        if len(complete_path_match_list) > 1:
            #-1 is the last item in the list in python syntax
            warning_message = " ".join(("Warning: >1 matching texture, texture:", complete_path_match_list[-1], "was loaded."))
            bpy.ops.ueshaderscript.show_message(message = warning_message)
            log(warning_message)
                


#function only replaces the end of the string
#so if we had a string called "mytgafile.tga"
#and old = ".tga" and new = "" then it would 
#just replace the end of the string returning "mytgafile"
def replace_ending(in_string, old, new):
    if in_string.endswith(old):
        #-len(old) refers to pythons counting from the end of the string(-)
        return in_string[:-len(old)] + new
    return in_string

def reuse_the_img_texture(node_to_load, img_texture_file_name):
    node_to_load.image = bpy.data.images[img_texture_file_name]


#if more than one principled bsdf changes all of them to the same strength
#have to change this manually as there is not always a _BDE image texture
#so we only increase emission strength as required when there is a _BDE texture
def change_emission_strength_principled_bsdf(node_tree, node_type, emission_strength):
    count = 0
    for node in node_tree.nodes:
        if (node.type == node_type):
            count = count + 1
            #print("node:", node)
            #print("dir(node):", dir(node))
            node.inputs["Emission Strength"].default_value = emission_strength
    
    if count > 1:
        warning_message = " ".join(("Warning: More than one Principled BSDF so changed all P BSDF node Emission Strengths to", emission_strength, "!"))
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


#--------reset settings for load function main panel class
class LOADUESHADERSCRIPT_OT_reset_settings_main_panel(bpy.types.Operator):
    bl_idname = "loadueshaderscript.reset_settings_main_panel_operator"
    bl_label = "Reset All Settings to Default"
    bl_description = "Reset Load Settings Main Panel for UEShaderScript"
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        #store active/selected scene to variable
        scene = context.scene
        #allow access to user inputted properties through pointer
        #to properties
        pathtool = scene.path_tool

        #don't reset the paths or inputs otherwise
        #user has to set them again and again
        #pathtool.property_unset("props_txt_path")
        #pathtool.property_unset("skin_bump_map_path")
        #pathtool.property_unset("export_folder_path")
        #pathtool.property_unset("material_indices_list_string")

        pathtool.property_unset("is_show_add_one_material_operator")
        pathtool.property_unset("is_replace_nodes")
        pathtool.property_unset("texture_file_type_enum")
        pathtool.property_unset("clipping_method_enum")
        pathtool.property_unset("is_load_img_textures")
        pathtool.property_unset("is_delete_unused_img_texture_nodes")
        pathtool.property_unset("is_delete_unused_related_nodes")
        pathtool.property_unset("is_change_principle_bsdf_emission_strength")
        pathtool.property_unset("principled_bsdf_emission_strength_float")
        pathtool.property_unset("material_alpha_threshold")
        pathtool.property_unset("is_reuse_node_group_with_same_name")
        pathtool.property_unset("is_reuse_img_texture_with_same_name")
        pathtool.property_unset("reverse_match_list_from_props_txt_enum")
        pathtool.property_unset("is_add_skin_bump_map")
        pathtool.property_unset("is_use_recolor_values")
        pathtool.property_unset("is_add_non_match_textures")
        pathtool.property_unset("is_show_no_match_tex_debug")
        pathtool.property_unset("is_show_abs_props_debug")

        pathtool.property_unset("diffuse_color_space")
        pathtool.property_unset("packed_rgb_color_space")
        pathtool.property_unset("normal_color_space")
        pathtool.property_unset("alpha_color_space")
        pathtool.property_unset("emissions_color_space")
        pathtool.property_unset("height_color_space")
        pathtool.property_unset("hair_gradient_color_space")
        pathtool.property_unset("specular_color_space")
        pathtool.property_unset("gloss_color_space")
        pathtool.property_unset("tint_base_diffuse_color_space")
        pathtool.property_unset("tint_mask_color_space")
        pathtool.property_unset("skin_bump_color_space")
        pathtool.property_unset("cust1_color_space")
        pathtool.property_unset("cust2_color_space")
        pathtool.property_unset("cust3_color_space")
        pathtool.property_unset("cust4_color_space")

        pathtool.property_unset("non_match_color_space")

        #reset advanced settings as well in case
        #they were changed accidentally
        pathtool.property_unset("regex_pattern_in_props_txt_file")
        pathtool.property_unset("props_txt_file_type")
        return {'FINISHED'}



#don't register LOADUESHADERSCRIPT_shared_main_panel
#because that is not a bpy class and trying to register
#something that is not a panel or bpy class will result in an error
classes = [PathProperties, 

LOADUESHADERSCRIPT_PT_select_preset_main_panel_1,

LOADUESHADERSCRIPT_PT_load_settings_main_panel_2, LOADUESHADERSCRIPT_PT_alpha_emissive_main_panel_3, 
LOADUESHADERSCRIPT_PT_color_space_main_panel_4, LOADUESHADERSCRIPT_PT_advanced_settings_main_panel_5,
LOADUESHADERSCRIPT_PT_reset_settings_main_panel_6, 

LOADUESHADERSCRIPT_PT_load_methods_main_panel_7,
LOADUESHADERSCRIPT_PT_solo_material_main_panel_8,
LOADUESHADERSCRIPT_PT_custom_denoising_main_panel_9, 

LOADUESHADERSCRIPT_OT_solo_material, LOADUESHADERSCRIPT_OT_solo_material_all,
LOADUESHADERSCRIPT_OT_use_nodes_mesh, LOADUESHADERSCRIPT_OT_use_nodes_mesh_all,

LOADUESHADERSCRIPT_OT_use_custom_denoising,

LOADUESHADERSCRIPT_OT_add_to_one_material, LOADUESHADERSCRIPT_OT_add_to_multiple_materials, 
LOADUESHADERSCRIPT_OT_add_to_selected_meshes, LOADUESHADERSCRIPT_OT_reset_settings_main_panel]
 
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
    #register path_tool as a type which has all
    #the user input properties from the properties class 
    bpy.types.Scene.path_tool = bpy.props.PointerProperty(type = PathProperties)
 
def unregister():
    #unregister in reverse order to registered so classes relying on other classes
    #will not lead to an error
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
        
    #unregister path_tool as a type
    del bpy.types.Scene.path_tool
 
 
if __name__ == "__main__":
    register()
