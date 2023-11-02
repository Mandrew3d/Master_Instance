bl_info = {
    "name": 'Instance Master' ,
    "author": "Mandrew3D",
    "version": (1, 0),
    "blender": (3, 6, 5),
    "location": "View3D > UI > M_Instance",
    "description": "Addon that helps to work with various types of instances ",
    "warning": "",
    "doc_url": "https://github.com/Mandrew3d/Master_Instance",
    "category": "Mods",
}

addon_name = 'Instance Master'

import bpy
from bpy.types import Operator
from bpy.utils import register_class, unregister_class
from mathutils import Vector
import os
import addon_utils

langs = {
    'es': {
        ('*', 'Test text in Blender UI'): 'Prueba de texto en la interfaz de usuario de Blender',
        ('Operator', 'Operator name'): 'Nombre del operador',
        ('*', 'Test text for printing in system console'): 'Prueba de texto para imprimir en la consola del sistema',
        ('*', 'Panel Header'): 'Encabezado del panel',
        ('*', 'Localization test'): 'Prueba de localización'
    },
    'ja_JP': {
        ('*', 'Test text in Blender UI'): 'Blender ユーザーインターフェースでテキストをテストする',
        ('Operator', 'Operator name'): 'オペレーター名',
        ('*', 'Test text for printing in system console'): 'システムコンソールで印刷するためのテストテキスト',
        ('*', 'Panel Header'): 'パネルヘッダー',
        ('*', 'Localization test'): 'ローカリゼーションテスト'
    }
}

#Make Instance Colletion of selected objects
def make_instance(self, context):
    col_name = self.col_name
    use_floor = self.use_floor
    
    act_obj_loc = bpy.context.object.matrix_world.to_translation()
    
    add_floor = 0
    
    if use_floor == True:
        obj = bpy.context.object
        bbox = obj.bound_box
        bbox_world = [obj.matrix_world @ Vector(corner) for corner in bbox]
        min_z = min(v.z for v in bbox_world)
        add_floor = act_obj_loc[2]-min_z
    else:
        add_floor = 0
        
            
    
    
    
    selected_objects = bpy.context.selected_objects
    
    #Move objs to center  
    offset = -act_obj_loc
    offset[2] += add_floor 
    bpy.ops.transform.translate(value=offset)
    
    #create new collection with name from col_name and link to scene
    new_collection = bpy.data.collections.new(col_name)
    bpy.context.scene.collection.children.link(new_collection)
   
    #get new name usefull than name dubles    
    end_name = new_collection.name 
    
    #remove objs from main col and add in new col
    for obj in selected_objects:
        old_collection = obj.users_collection[0]
        old_collection.objects.unlink(obj)
    
    for obj in selected_objects:
        new_collection.objects.link(obj)
    
    #get contex vl  
    vl_name = bpy.context.view_layer.name
    
    bpy.context.scene.view_layers[vl_name].layer_collection.children[end_name].exclude = True
    
    
    #make instance
    name_f_instance = end_name + '_Instance'
    bpy.ops.object.collection_instance_add(name=name_f_instance, collection=end_name , align='WORLD', location=(0, 0, 0), rotation=(0, 0, 0), scale=(0, 0, 0), session_uuid=0, drop_x=0, drop_y=0)
    #old_col_name = context.object
    context.object.name = name_f_instance
   
    #Move new instance to relative location
    act_obj_loc[2] -= add_floor
    context.object.location = act_obj_loc

class MAKE_OT_Instance(Operator):
    bl_idname = "minstance.make_instance"
    bl_label = "Make Instance Collection"
    bl_description = "Make Instance Colletion of selected objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    col_name :  bpy.props.StringProperty(default = 'Collection')
    use_floor: bpy.props.BoolProperty(default = True)
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "col_name", text = 'Name')
        layout.prop(self, "use_floor", text = 'Drop on Floor')
        
    def execute(self, context):
        make_instance(self, context)
        return {'FINISHED'}

#Edit collection 
def get_collection(self, context):
    cont_ob = context.object
    if cont_ob.type == 'EMPTY' and context.object.instance_collection != None:
            
        #get instance col name
        s_col = cont_ob.instance_collection

        #Unhide Collection
        vl_name = bpy.context.view_layer.name

        bpy.context.scene.view_layers[vl_name].layer_collection.children[s_col.name].exclude = False

        #select objects
        bpy.ops.object.select_all(action='DESELECT')

        col_objs = bpy.data.collections[s_col.name].objects
        for ob in col_objs:
            bpy.data.objects[ob.name].select_set(True)
        bpy.context.view_layer.objects.active = col_objs[0]
        bpy.ops.view3d.view_selected(use_all_regions=True)
    else:
        cont_col = cont_ob.users_collection[0]
        if cont_col != context.scene.collection:
            vl_name = bpy.context.view_layer.name

            bpy.context.scene.view_layers[vl_name].layer_collection.children[cont_col.name].exclude = True
            
            bpy.ops.object.select_all(action='DESELECT')
            for ob in bpy.data.objects:
                if ob.type == 'EMPTY':
                    if ob.instance_collection:
                        #print(ob.instance_collection.name)
                        if ob.instance_collection.name == cont_col.name:
                            bpy.data.objects[ob.name].select_set(True)
                            bpy.context.view_layer.objects.active = ob
                            bpy.ops.view3d.view_selected(use_all_regions=True)

class GET_OT_Collection(Operator):
    bl_idname = "minstance.get_collection"
    bl_label = "Edit Relative Collection"
    bl_description = "Unhide collection of active instance"
    bl_options = {'REGISTER', 'UNDO'}
    

    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    

        
    def execute(self, context):
        get_collection(self, context)
        return {'FINISHED'}

#Open Linced File
def open_linked(self, context):
    open_f = self.open_f
    
    obj = context.object
    
    if bpy.context.object.instance_collection.library:
        if bpy.context.object.instance_collection.library.filepath:
            
            
            filepath = obj.instance_collection.library.filepath
            
            root_path = bpy.path.abspath(filepath)
            if open_f == False:
                os.startfile(root_path)
            else:
                path =  os.path.dirname(root_path)
                os.startfile(path)
            
            
    else:
        self.report({'ERROR'}, 'Instance collection is not a reference to an external file')

class OPEN_OT_Linked(Operator):
    bl_idname = "minstance.open_linked"
    bl_label = "Open Relative File"
    bl_description = "Open .blend file on your computer"
    bl_options = {'REGISTER', 'UNDO'}
    
    open_f : bpy.props.BoolProperty(default = False,  options={'HIDDEN'})
    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.object.type == 'EMPTY'
    

        
    def execute(self, context):
        open_linked(self, context)
        return {'FINISHED'}

#Reload Linced File
def reload_linked(self, context):
    
    obj = context.object
    col =obj.instance_collection
    col.library.reload()

class RELOAD_OT_Linked(Operator):
    bl_idname = "minstance.reload_linked"
    bl_label = "Update Instance"
    bl_description = "Reload Linked file in your scene"
    bl_options = {'REGISTER', 'UNDO'}
    

    
    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.object.type == 'EMPTY'
    

        
    def execute(self, context):
        reload_linked(self, context)
        return {'FINISHED'}

#Get Path Of Selected Object
def get_addon_folder(add_buffer):
    for mod in addon_utils.modules():
        if mod.bl_info['name'] == addon_name:
            filepath = mod.__file__
            #print (filepath)
            s_path = filepath[:-len(bpy.path.basename(filepath))]
            #print(s_path)
        else:
            pass
    if add_buffer:
       s_path += 'MasterInstance_Buffer.txt'   
        
    return s_path
    
def get_object_path(self, context):
    obj = context.object
    
    
    
    o_tag = 'MasterInstance_TAG'
    o_path = bpy.data.filepath
    o_col_name = context.object.users_collection[0].name
    
    o_buffer = [o_tag,o_path,o_col_name]
    o_buffer = str(o_buffer)
    
    s_path = get_addon_folder(True)
    
    
    file_path = s_path
    

    with open(file_path, "w") as file:
        file.write(o_buffer)

            
class Get_OT_Object_Path(Operator):
    bl_idname = "minstance.get_obj_path"
    bl_label = "Copy Collection As Instance"
    bl_description = "Copy active object as instance"
    #bl_options = {'REGISTER', 'UNDO'}
    

    
    @classmethod
    def poll(cls, context):
        chek = False
        
        if context.active_object is not None and len(context.selected_objects)>0:
            if context.object.users_collection:
                if context.object.users_collection[0] != context.scene.collection:
                    if bpy.data.is_saved:
                        chek = True
        return chek

        
    def execute(self, context):
        get_object_path(self, context)
        return {'FINISHED'}

#Paste Instance

def link_collection(c_path,c_name):
    
    master_collection = bpy.context.scene.collection
    
    blendFile = c_path
    
    with bpy.data.libraries.load(blendFile) as (data_from, data_to):
        data_to.collections = data_from.collections
        
    col_name = c_name

    i = 0
    col_ind = 0
    for col in data_to.collections:
        if col.name == col_name:
            col_ind = i
            break
        i +=1
        print(col_name)
        print(col.name)
            
    bpy.ops.object.select_all(action='DESELECT')
    new_coll = data_to.collections[col_ind]
    instance = bpy.data.objects.new(new_coll.name, None)
    instance.instance_type = 'COLLECTION'
    instance.instance_collection = new_coll
    master_collection.objects.link(instance)
    instance.select_set(True)
    bpy.context.view_layer.objects.active = instance  

          
def try_convert_to_list(list):
    try:
        value_list = eval(list)
    except:
        return None
    
    
    return value_list

def paste_object(self, context):
    file_path = get_addon_folder(True)
    
    with open(file_path, "r") as file:
        clipboard = file.read()   
    clipboard = try_convert_to_list(clipboard)
            
    if isinstance(clipboard, list):   
        if clipboard[0] == 'MasterInstance_TAG':
            
            print(clipboard)
            c_path = clipboard[1]
            c_name = clipboard[2]
            if c_path != bpy.data.filepath:
                link_collection(c_path,c_name)
            
            else:
                self.report({'ERROR'}, 'Cannot link instance, as its source is in the same file')
        else:
            print("Not Intance")
    else:
        print("Not LIst")
        
        
class Paste_OT_Object_As_Intance(Operator):
    bl_idname = "minstance.paste_obj_as_instance"
    bl_label = "Paste Collection As Instance"
    bl_description = "Paste copyed collection as instance"
    #bl_options = {'REGISTER', 'UNDO'} 
    
    @classmethod
    def poll(cls, context):
        chek = False
        file_path = get_addon_folder(True)
        
        with open(file_path, "r") as file:
            clipboard = file.read() 
        clipboard = try_convert_to_list(clipboard)            
        if isinstance(clipboard, list):   
            if clipboard[0] == 'MasterInstance_TAG':
                chek = True
                        
        return chek
        
    def execute(self, context):
        paste_object(self, context)
        return {'FINISHED'}    
    
        
class Save_OT_File(Operator):
    bl_idname = "minstance.save_file"
    bl_label = "Save File"
    bl_description = "Don't forget to save Blend file before copy. Press to Save"
    #bl_options = {'REGISTER', 'UNDO'} 
    
    @classmethod
    def poll(cls, context):                        
        return bpy.data.is_saved
        
    def execute(self, context):
        paste_object(self, context)
        return {'FINISHED'}    
        
class MINSTANCE_PT_Operators(bpy.types.Panel):
    
    bl_label = addon_name
    bl_category = "M-Instance"
    bl_space_type = 'VIEW_3D'
    bl_region_type = "UI"
    

    def draw(self, context):

        layout = self.layout

        scene = context.scene

        layout.label(text="Scene Instances:")
        
        
        col = layout.column() 
        col.operator("minstance.make_instance", icon = "OUTLINER_OB_GROUP_INSTANCE") 
        
        col_name = 'Hide Collection'
        col_icon = 'HIDE_ON'
        if bpy.context.object:
            if bpy.context.object.type == 'EMPTY':
                if bpy.context.object.instance_collection != None:
                    col_name = bpy.context.object.instance_collection.name
                    col_name = 'Edit: ' + col_name
                    col_icon = "EDITMODE_HLT"

        col.operator("minstance.get_collection", icon = col_icon, text = col_name) 

        
        layout.separator()
        layout.label(text="Linked Instances:")
        col = layout.column(align = True)
        col.operator("wm.link", text = 'Link from file', icon= 'LINK_BLEND')
        
        row = col.row(align = True)
        o_file = row.operator("minstance.open_linked", icon = "LINKED")
        o_file.open_f = False
        o_path = row.operator("minstance.open_linked", text = '' ,icon = "FILEBROWSER")
        o_path.open_f = True
        #col.operator("minstance.open_linked", icon = "OUTLINER_OB_GROUP_INSTANCE")
        #col = layout.column() 
        col.operator("minstance.reload_linked", icon = "FILE_REFRESH")  
        
        col = layout.column(align = True)

        #col_name = context.object.users_collection[0]
        c_text = "Save Blend File First"
        if bpy.data.is_saved:
            c_text = "Select Any Object"    
            if bpy.context.active_object is not None and len(context.selected_objects)>0:
                if bpy.context.object.users_collection:
                    if bpy.context.object.users_collection[0] != context.scene.collection:
                        col_name = context.object.users_collection[0]
                        c_text = "Get '" + col_name.name + "' Collection"
                    else:
                        c_text = "'Scene Collection' Cannot Be Instanced"
        
        row = col.row(align = True)
        row.operator("minstance.get_obj_path", icon = "COPYDOWN", text = c_text)  
        if bpy.data.is_saved:
            if bpy.data.is_dirty:
                row.operator("minstance.save_file", icon = "ERROR", text = '')  
        
        file_path = get_addon_folder(True)
        
        with open(file_path, "r") as file:
            clipboard = file.read()   
        clipboard = try_convert_to_list(clipboard)
        c_name = 'No Object in Copy'
        if clipboard is not None:
            c_name = clipboard[2]                        
        
        text = "Link '" + str(c_name) + "' Collection"
        col.operator("minstance.paste_obj_as_instance", icon = "PASTEDOWN", text = text)  
#Menu
# menu containing all tools
class VIEW3D_MT_object_mode_minstance(bpy.types.Menu):
    bl_label = "Instance Master"
    
    def draw(self, context):
        
        layout = self.layout

        scene = context.scene

        layout.label(text="    Scene Instances:")
        
        
        col = layout.column()
        layout.separator()
         
        col.operator("minstance.make_instance", icon = "OUTLINER_OB_GROUP_INSTANCE") 
        
        col_name = 'Hide Collection'
        col_icon = 'HIDE_ON'
        if bpy.context.object:
            if bpy.context.object.type == 'EMPTY':
                if bpy.context.object.instance_collection != None:
                    col_name = bpy.context.object.instance_collection.name
                    col_name = 'Edit: ' + col_name
                    col_icon = "EDITMODE_HLT"

        col.operator("minstance.get_collection", icon = col_icon, text = col_name) 
        
        
        layout.label(text="    Linked Instances:")
        
        row = layout.row()
        row.operator("wm.link", text = 'Link from file', icon= 'LINK_BLEND')
        
        row = layout.row(align = True)
        o_file = row.operator("minstance.open_linked", icon = "LINKED")
        o_file.open_f = False
        o_path = row.operator("minstance.open_linked", text = '' ,icon = "FILEBROWSER")
        o_path.open_f = True
        #col.operator("minstance.open_linked", icon = "OUTLINER_OB_GROUP_INSTANCE")
        col = layout.column() 
        col.operator("minstance.reload_linked", icon = "FILE_REFRESH")  
        
             
# draw function for integration in menus
def menu_func_minstance(self, context):
    layout = self.layout
    layout.menu("VIEW3D_MT_object_mode_minstance", icon = "OUTLINER_OB_GROUP_INSTANCE" )
    #self.layout.separator()
    #Copy Paste

    #col_name = context.object.users_collection[0]
    c_text = "Save Blend File First"
    if bpy.data.is_saved:
        c_text = "Select Any Object"    
        if bpy.context.active_object is not None and len(context.selected_objects)>0:
            if bpy.context.object.users_collection:
                if bpy.context.object.users_collection[0] != context.scene.collection:
                    col_name = context.object.users_collection[0]
                    c_text = "Get  '" + col_name.name + "' Collection"
                else:
                    c_text = "'Scene Collection' Cannot Be Instanced"
    
    #row = col.row(align = True)
    layout.operator("minstance.get_obj_path", icon = "COPYDOWN", text = c_text)                     
    
    text = 'Link Collection'
    layout.operator("minstance.paste_obj_as_instance", icon = "PASTEDOWN", text = text)  
    self.layout.separator() 
        
           
classes = [
    MAKE_OT_Instance,
    GET_OT_Collection,
    OPEN_OT_Linked,
    RELOAD_OT_Linked,
    Get_OT_Object_Path,
    Save_OT_File,
    Paste_OT_Object_As_Intance,
       
    MINSTANCE_PT_Operators,
    VIEW3D_MT_object_mode_minstance,

        
]


def register():       
    #bpy.app.translations.register(__name__, langs)
    for cl in classes:
        register_class(cl)
  
    bpy.types.VIEW3D_MT_object_context_menu.prepend(menu_func_minstance)        
                
def unregister():
    for cl in reversed(classes):
        unregister_class(cl)
    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_func_minstance)
    #bpy.app.translations.unregister(__name__)
    
if __name__ == "__main__":
    register()