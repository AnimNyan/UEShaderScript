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

bl_info = {
    "name": "UE Shader Map Setups",
    "author": "Anime Nyan",
    "version": (1, 0, 0),
    "blender": (2, 92, 0),
    "location": "TO BE ADDED",
    "description": "Adds different preset shader maps for Unreal Engine games Dead By Daylight and Home Sweet Home Survive characters that have already been imported into blender",
    "warning": "",
    "wiki_url": "TO BE ADDED",
    "category": "Material",
    "tracker_url": "TO BE ADDED"
}

"""
Version': '1.0.0' written by Anime Nyan

Adds a panel in the 3D view to add different preset shader maps to materials for Unreal Engine Dead By Daylight and Home Sweet Home Survive characters that have already been imported into Blender
       
"""

#import all libraries including re needed for regex matching
#import Path library to search recursively for files
import bpy, re
import glob
from pathlib import Path

#define all user input properties
class PathProperties(bpy.types.PropertyGroup):
    props_txt_path: bpy.props.StringProperty(name="Select PropsTxt File", description="Select a props.txt file", subtype="FILE_PATH")
    height_map_path: bpy.props.StringProperty(name="Select Height Map File", description="Select a height map image file", subtype="FILE_PATH")
    material_folder_path: bpy.props.StringProperty(name="Select Materials Folder", description="Select a Materials folder", subtype="DIR_PATH")
    export_folder_path: bpy.props.StringProperty(name="Select Exported Game Folder", description="Select a Game folder", subtype="DIR_PATH")
    shader_type_enum: bpy.props.EnumProperty(
        name = "Shader Map Type",
        description = "Dropdown List of all the types of Shader Maps",
        items = 
        [
            ("DBDRomanNoodlesYanima" , "DBD Roman Noodles & YanimaDBD Shader Maps", ""),
            ("DBDFrutto" , "DBD Frutto Shader Maps", ""),
            ("HSHSTico" , "HSHS Tico Shader Maps", "")
        ]
        
    )
    is_add_img_textures: bpy.props.BoolProperty(name="Add Image Textures", default= True)
    is_material_skin: bpy.props.BoolProperty(name="Add Skin Related Nodes", default= False)
    is_add_height_map: bpy.props.BoolProperty(name="Add Height Map Skin Texture", default= False)


#code for drawing main panel in the 3D View
class UEShaderScript_PT_main_panel(bpy.types.Panel):
    bl_label = "UE Shader Maps"
    bl_idname = "UEShaderScript_PT_main_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = "DBD Shaders"
    
    def draw(self, context):
        layout = self.layout
        
        #store active/selected scene to variable
        scene = context.scene
        #allow access to user inputted properties through pointer
        #to properties
        mytool = scene.my_tool
        
        layout.prop(mytool, "shader_type_enum")
        layout.prop(mytool, "is_add_img_textures")
        row = layout.row()
        if mytool.is_add_img_textures == True:
            row.prop(mytool, "is_material_skin")
            
            if mytool.shader_type_enum == "DBDRomanNoodlesYanima" and mytool.is_material_skin == True:
                row.prop(mytool, "is_add_height_map")
        
        
        #Create a box for all related inputs and operators 
        #for adding the shader maps one by one to
        #selected material
        box = layout.box()
        
        #----------draw user input boxes
        #create box for all related boxes adding shader map to selected material
        box.label(text = "ADD SHADER MAP TO ACTIVE MATERIAL (ONE MATERIAL)",)
        box.label(text = "Select a mesh and a material and add a shader map to the selected material")
        if mytool.is_add_img_textures == True:
            box.prop(mytool, "props_txt_path")
            box.prop(mytool, "export_folder_path")
        
        if mytool.shader_type_enum == "DBDRomanNoodlesYanima" and mytool.is_add_img_textures == True and mytool.is_material_skin == True and mytool.is_add_height_map == True:
            box.prop(mytool, "height_map_path")
        
        #add operators
        #change the text for operators
        #if it is not a Roman Noodles setup
        #as other shader map setups have the same
        #shader map for all materials, hair and body included
        if mytool.shader_type_enum != "DBDRomanNoodlesYanima":
            box.operator("UEShaderScript.addbasic_operator", text = "Add Shader Map (Every Material)" )
        
        if mytool.shader_type_enum == "DBDRomanNoodlesYanima":  
            #do not change text because by default text on operator
            #is for Roman Noodles' setup
            box.operator("UEShaderScript.addbasic_operator")
            box.operator("UEShaderScript.addhair_operator")
        
        #Create a box for the function adding all 
        #related inputs and operators 
        #for adding shader maps to all materials for
        #selected mesh
        box = layout.box()
        box.label(text = "ADD SHADER MAP TO ALL MATERIALS ON ACTIVE MESHES (ALL MATERIALS)")
        box.label(text = "Select multiple meshes and add shader maps to all the materials on the selected meshes")
        
        #only show user input boxes if add image textures is checked 
        #because the user path input boxes are not needed if it is unchecked
        if mytool.is_add_img_textures == True:
            box.prop(mytool, "material_folder_path")
            box.prop(mytool, "export_folder_path")
        
        if mytool.shader_type_enum == "DBDRomanNoodlesYanima" and mytool.is_add_img_textures == True and mytool.is_material_skin == True and mytool.is_add_height_map == True:
            box.prop(mytool, "height_map_path")
        
        if mytool.shader_type_enum != "DBDRomanNoodlesYanima":
            box.operator("UEShaderScript.addbasicall_operator", text = "Add ALL Shader Maps (Every Material)" )
        
        if mytool.shader_type_enum == "DBDRomanNoodlesYanima":
            box.operator("UEShaderScript.addbasicall_operator")
            box.operator("UEShaderScript.addhairall_operator")
        
        


class UEShaderScript_OT_add_basic(bpy.types.Operator):
    #default name is for Roman Noodles label
    #text is changed for other Shader Map Types
    bl_label = "Add Roman Noodles Basic Shader Map (Every Material Except Hair)"
    bl_idname = "UEShaderScript.addbasic_operator"
    def execute(self, context):
        scene = context.scene 
        #allow access to user inputted properties through pointer
        #to properties
        mytool = scene.my_tool
        
        #find the selected material and 
        #create a basic shader on it
        selected_mat = bpy.context.active_object.active_material
        
        create_one_basic_shader_map(context, selected_mat, mytool.props_txt_path, mytool)
        
        return {"FINISHED"}


class UEShaderScript_OT_add_basic_all(bpy.types.Operator):
    bl_label = "Add Roman Noodles ALL Basic Shader Maps (Every Material Except Hair)"
    bl_idname = "UEShaderScript.addbasicall_operator"
    def execute(self, context):
        scene = context.scene 
        #allow access to user inputted properties through pointer
        #to properties
        mytool = scene.my_tool
        
        create_all_shader_maps(context, mytool, "Basic")
        
    
        return {"FINISHED"}


class UEShaderScript_OT_add_hair(bpy.types.Operator):
    bl_label = "Add YanimaDBD Hair Shader Map (Only For Hair Materials)"
    bl_idname = "UEShaderScript.addhair_operator"
    def execute(self, context):
        #make reference to user inputted file name
        #so that can use the user inputted props txt location
        #and exported game folder location
        scene = context.scene
        mytool = scene.my_tool
        
        #find the selected material and 
        #create a basic shader on it
        selected_mat = bpy.context.active_object.active_material
        selected_mat.use_nodes = True
        
        #store new link function to variable
        link = s_mat.node_tree.links.new
        
        #store new node function to variable
        new_node = s_mat.node_tree.nodes.new
        
        #delete all nodes except the material output node
        nodes = s_mat.node_tree.nodes
        for node in nodes:
            if node.type != 'OUTPUT_MATERIAL': # skip the material output node as we'll need it later
                nodes.remove(node)
        
        #start adding all nodes
        
        
        return {"FINISHED"}


class UEShaderScript_OT_add_hair_all(bpy.types.Operator):
    bl_label = "Add ALL YanimaDBD Hair Shader Maps (Only For Hair Materials)"
    bl_idname = "UEShaderScript.addhairall_operator"
    def execute(self, context):
        scene = context.scene 
        #allow access to user inputted properties through pointer
        #to properties
        mytool = scene.my_tool
        
        create_all_shader_maps(context, mytool, "Hair")
            
        return {"FINISHED"}


#create all basic shader maps function
#just runs the create one basic shader map function
#for all selected objects and all materials
def create_all_shader_maps(context, mytool, type):
    #if the folder path is a relative path
    #turn it into an absolute one
    #as relative paths cause problems
    #when trying to load an image
    abs_mat_folder_path =  bpy.path.abspath(mytool.material_folder_path)
    
    
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
            gen_obj_match = Path(abs_mat_folder_path).rglob(material.name + ".props.txt")
            
            props_txt_path = ""
            
            for file_path in gen_obj_match:
                props_txt_path = file_path
                       
            #not needed any more
            #get the current material's name to concatenate
            #a string the path to the props.txt file
            #props_txt_path = abs_mat_folder_path + material.name + ".props.txt"
            
            #create shader maps for all the materials 
            #inside the selected meshes
            #either a Basic or Hair shader map based on 
            #the type passed to the function
            if (type == "Basic"):
                create_one_basic_shader_map(context, material, props_txt_path, mytool)
            elif(type == "Hair"):
                create_one_hair_shader_map(context, material, props_txt_path, mytool)
            
    return {"FINISHED"}  


def create_one_basic_shader_map(context, material, props_txt_path, mytool):
    #if the folder path is a relative path
    #turn it into an absolute one
    #as relative paths cause problems
    #when trying to load an image
    abs_props_txt_path =  bpy.path.abspath(props_txt_path)
        
    #delete all nodes except the material 
    #output node and principled BSDF node
    #to start from a clean slate
    #and delete any preexisting nodes
    nodes = material.node_tree.nodes
    for node in nodes:
        #check what the node types are called by printing it 
        #print("This is the node.type", node.type)
        
        # skip deleting the material output and principled bsdf node as we'll need it later
        if not(node.type == 'OUTPUT_MATERIAL' or node.type == "BSDF_PRINCIPLED"): 
            nodes.remove(node)
    
    #choose which shader map type to be be using
    if (mytool.shader_type_enum == "DBDRomanNoodlesYanima"):
        roman_noodles_basic_shader_map(material, abs_props_txt_path, mytool)
        
    elif (mytool.shader_type_enum == "DBDFrutto"):
        frutto_basic_shader_map(material, abs_props_txt_path, mytool)
        
    elif (mytool.shader_type_enum == "HSHSTico"):
        tico_basic_shader_map(material, abs_props_txt_path, mytool)


def roman_noodles_basic_shader_map(material, props_txt_path, mytool):
    #store new link function to variable
    link = material.node_tree.links.new
    
    #store new node function to variable
    new_node = material.node_tree.nodes.new
    
    #assign Principled BSDF to a variable so can be referenced later
    #so that nodes can link to it
    principled_node = material.node_tree.nodes.get('Principled BSDF')
    #add subsurface skin settings to principled BSDF node
    #if the material is for skin
    if mytool.is_material_skin == True:
        principled_node.subsurface_method = "RANDOM_WALK"
        principled_node.inputs[1].default_value = 0.03
        principled_node.inputs["Subsurface Color"].default_value = (0.8, 0, 0, 1)
        
    principled_node.inputs["Specular"].default_value = 0.064

    #start adding all nodes and respective links to shader map
    #--------------add everything except image texture nodes
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
    if mytool.is_material_skin == True:
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
    if mytool.is_add_img_textures == True:
        #---------------add image texture nodes    
        #example loading image
        #texImage.image = bpy.dat.images.load(
        #"C:\Users\myName\Downloads\Textures\Downloaded\flooring5.jpg")
        
        #add height map if Add Skin Related Nodes is checked and 
        #add Height Map Skin Texture is checked
        #add the height map image texture and load the user defined
        #height map image
        
        if mytool.is_add_img_textures == True and mytool.is_material_skin == True and mytool.is_add_height_map == True:
            height_map_path = mytool.height_map_path
            
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
            abs_export_folder_path = bpy.path.abspath(mytool.export_folder_path)
            
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
            complete_path = user_tex_folder + tex_location + ".tga"

            #If the texture is listed in the 
            #props.txt file and it is one of the
            #image textures we are interested in we will add the node
            #and load the corresponding image
                 
            #check what the last two/three characters are of the id
            #and look for the specific ids we are interested in
            #identifier
            if "_BC" == tex_id[-3:]:
                bc_node = new_node('ShaderNodeTexImage')
                bc_node.location = (-300,450) #x,y
                bc_node.image = bpy.data.images.load(complete_path)
                link(bc_node.outputs[0], principled_node.inputs[0])
                link(bc_node.outputs[0], rgbbw_node.inputs[0])
                bc_node.interpolation = "Cubic"
                
            elif "_ORM" in tex_id[-4:]:
                orm_node = new_node('ShaderNodeTexImage')
                orm_node.location = (-750, 300) #x,y
                orm_node.image = bpy.data.images.load(complete_path)
                link(orm_node.outputs[0], srgb_node.inputs[0])
                orm_node.image.colorspace_settings.name = "Non-Color"
                
            elif "_N" in tex_id[-2:]:
                n_node = new_node('ShaderNodeTexImage')
                n_node.location = (-800,-200) #x,y
                n_node.image = bpy.data.images.load(complete_path)
                link(n_node.outputs[0], normap_node.inputs[1])
                n_node.image.colorspace_settings.name = "Non-Color"
                
            elif "_M" in tex_id[-2:]:
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



def frutto_basic_shader_map(material, props_txt_path, mytool):
    print("PLACEHOLDER")
    

def tico_basic_shader_map(material, props_txt_path, mytool):
    print("PLACEHOLDER")


def create_one_hair_shader_map(context, material, props_txt_path, mytool):
    
    #delete all nodes except the material output node
    #to start from a clean slate
    nodes = material.node_tree.nodes
    for node in nodes:
        # skip the material output as we'll need it later
        if node.type != 'OUTPUT_MATERIAL': 
            nodes.remove(node)
    
    #do not need to choose which shader map type to be be using
    #as only DBDRomanNoodlesYanima has the option to create a
    #hair shader, but check just in case of errors
    if (mytool.shader_type_enum == "DBDRomanNoodlesYanima"):
        yanima_hair_shader_map(material, props_txt_path, mytool)


def yanima_hair_shader_map(material, props_txt_path, mytool):
    #store new link function to variable
    link = material.node_tree.links.new
    
    #store new node function to variable
    new_node = material.node_tree.nodes.new

    #start adding all nodes and respective links to shader map
    #--------------add everything except image texture nodes
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
    if mytool.is_material_skin == True:
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
    if mytool.is_add_img_textures == True:
        #---------------add image texture nodes    
        #example loading image
        #texImage.image = bpy.dat.images.load(
        #"C:\Users\myName\Downloads\Textures\Downloaded\flooring5.jpg")
        
        #add height map if Add Skin Related Nodes is checked and 
        #add Height Map Skin Texture is checked
        #add the height map image texture and load the user defined
        #height map image
        
        if mytool.is_add_img_textures == True and mytool.is_material_skin == True and mytool.is_add_height_map == True:
            height_map_path = mytool.height_map_path
            
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
            abs_export_folder_path = bpy.path.abspath(mytool.export_folder_path)
            
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
            complete_path = user_tex_folder + tex_location + ".tga"

            #If the texture is listed in the 
            #props.txt file and it is one of the
            #image textures we are interested in we will add the node
            #and load the corresponding image
                 
            #check what the last two/three characters are of the id
            #and look for the specific ids we are interested in
            #identifier
            if "_BC" == tex_id[-3:]:
                bc_node = new_node('ShaderNodeTexImage')
                bc_node.location = (-300,450) #x,y
                bc_node.image = bpy.data.images.load(complete_path)
                link(bc_node.outputs[0], principled_node.inputs[0])
                link(bc_node.outputs[0], rgbbw_node.inputs[0])
                bc_node.interpolation = "Cubic"
                
            elif "_ORM" in tex_id[-4:]:
                orm_node = new_node('ShaderNodeTexImage')
                orm_node.location = (-750, 300) #x,y
                orm_node.image = bpy.data.images.load(complete_path)
                link(orm_node.outputs[0], srgb_node.inputs[0])
                orm_node.image.colorspace_settings.name = "Non-Color"
                
            elif "_N" in tex_id[-2:]:
                n_node = new_node('ShaderNodeTexImage')
                n_node.location = (-800,-200) #x,y
                n_node.image = bpy.data.images.load(complete_path)
                link(n_node.outputs[0], normap_node.inputs[1])
                n_node.image.colorspace_settings.name = "Non-Color"
                
            elif "_M" in tex_id[-2:]:
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


classes = [PathProperties, UEShaderScript_PT_main_panel, UEShaderScript_OT_add_basic, UEShaderScript_OT_add_basic_all, UEShaderScript_OT_add_hair, UEShaderScript_OT_add_hair_all]
 
def register():
    for cls in classes:
        bpy.utils.register_class(cls)
        
        #register my_tool as a type which has all
        #the user input properties from the properties class 
        bpy.types.Scene.my_tool = bpy.props.PointerProperty(type = PathProperties)
 
def unregister():
    for cls in classes:
        bpy.utils.unregister_class(cls)
        
        #unregister my_tool as a type
        del bpy.types.Scene.my_tool
 
 
if __name__ == "__main__":
    register()