bl_info = {
    "name": 'Instance Master',
    "author": "Mandrew3D",
    "version": (1, 7),
    "blender": (3, 6, 5),
    "location": "View3D > UI > M_Instance",
    "description": "Addon that helps to work with various types of instances ",
    "warning": "",
    "doc_url": "https://github.com/Mandrew3d/Master_Instance",
    "category": "Mods",
}



import bpy
from bpy.types import Operator
from bpy.utils import register_class, unregister_class
from mathutils import Vector
import os
import addon_utils
import requests
import sys
from urllib.parse import urlencode

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

#Open Linked File
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
    addon_name = bl_info['name']
    s_path =''
    #s_path =  bpy.path.abspath(bpy.utils.user_resource("SCRIPTS") + '\\Master_Instance-main\\')
    #modu = addon_utils.modules()
    
    #print(modu)
    for mod in addon_utils.modules():
        #print(mod)
        #print(mod.bl_info['name'])
        
        if mod.bl_info['name'] == 'Instance Master':
            
            filepath = mod.__file__
            
            s_path = filepath[:-len(bpy.path.basename(filepath))]
            
        else:
            pass
    if add_buffer:
       s_path += 'MasterInstance_Buffer.txt'   
        
    return s_path
    
def get_object_path(self, context):
    obj = context.object
    
    
    
    o_tag = 'MasterInstance_TAG'
    o_path = bpy.data.filepath
    
    cols_to_get = []
    objs = context.selected_objects
    for obj in objs:
        if obj.users_collection[0].name not in cols_to_get:
            if obj.users_collection[0] != context.scene.collection:
                cols_to_get.append(obj.users_collection[0].name)
                
    o_col_name = cols_to_get
    
    o_buffer = [o_tag,o_path,o_col_name]
    o_buffer = str(o_buffer)
    
    s_path = get_addon_folder(True)
    
    
    file_path = s_path
    

    with open(file_path, "w") as file:
        file.write(o_buffer)

            
class Get_OT_Object_Path(Operator):
    bl_idname = "minstance.get_obj_path"
    bl_label = "Copy Collections As Instances"
    bl_description = "Copy selected objects as instances"
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
    
    #blendFile = c_path

    ref_cols = c_name
    print(ref_cols)
    bpy.ops.object.select_all(action='DESELECT')

    col_for_instance = []
    with bpy.data.libraries.load(c_path, link = True) as (data_from, data_to):
        print(data_from.collections)
        i = 0
        for col in data_from.collections:
            print(col)
            if col in ref_cols:
                col_for_instance.append(col)
                #data_to.collections.append(col)
                # if col not in bpy.data.collections:
                data_to.collections.append(col)
                #     print('Exist')
                
                    
                    
    for colection in col_for_instance:
        instance = bpy.data.objects.new(colection, None)
        instance.instance_type = 'COLLECTION'
        instance.instance_collection = bpy.data.collections[colection]
        master_collection.objects.link(instance)
        instance.select_set(True)
        bpy.context.view_layer.objects.active = instance 
           
    
    #bpy.data.libraries.load(c_path) 
#    with bpy.data.libraries.load(c_path) as (data):
#        data = data.collection
     
#    for col in  data_to.collections:
#        print(col)  
#    bpy.ops.object.select_all(action='DESELECT')
#    for collection in data_to.collections:
#        print(collection.name)
#        col_name = collection.name
#        i = 0
#        col_ind = 0
#        for col in data_to.collections:
#            if col.name in ref_cols:
#                col_ind = i
#                
#                new_coll = data_to.collections[col_ind]
#                instance = bpy.data.objects.new(new_coll.name, None)
#                instance.instance_type = 'COLLECTION'
#                instance.instance_collection = new_coll
#                master_collection.objects.link(instance)
#                instance.select_set(True)
#                bpy.context.view_layer.objects.active = instance 
#            
#            i +=1
#            #print(col_name)
#            #print(col.name)
                
     

          
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
    
    @classmethod
    def poll(cls, context):
        
        return True
        
    def execute(self, context):
        paste_object(self, context)
        return {'FINISHED'}    
    
        
class Save_OT_File(Operator):
    bl_idname = "minstance.save_file"
    bl_label = "Save File"
    bl_description = "Don't forget to save Blend file before copy. Press to Save"
    
    @classmethod
    def poll(cls, context):                        
        return bpy.data.is_saved
        
    def execute(self, context):
        paste_object(self, context)
        return {'FINISHED'}    

#Addon Updater
def update_addon(self):
    #get raw from git
    url = 'https://raw.githubusercontent.com/Mandrew3d/Master_Instance/main/__init__.py'
    response = requests.get(url, stream=True)
    
#    #YD
#    base_url = 'https://cloud-api.yandex.net/v1/disk/public/resources/download?'
#    public_key = 'https://disk.yandex.ru/d/zi8DD3Duq8qA-g'  # Сюда вписываете вашу ссылку

#    # Получаем загрузочную ссылку
#    final_url = base_url + urlencode(dict(public_key=public_key))
#    response = requests.get(final_url)
#    download_url = response.json()['href']

#    # Загружаем файл и сохраняем его
#    response = requests.get(download_url, stream=True)
    
    addon_path = get_addon_folder(False)
    path = os.path.join(addon_path, '__init__.py')
    
    if response.status_code == 200:

        #read instaled addon init        
        f_path = path

        file = open(f_path, "r")
        
        inst_addon = file.read()
        file.close()   
        
        #read git addon init   
        git_addon = response.text

        
        t1 = inst_addon
        t2 = git_addon
        
        if t1 == t2:
            self.report({'INFO'}, 'Is the latest version')   
            #print('Git = Inst')
        else:
            
            
            filePath = addon_path

            
            newFile = open(os.path.join(filePath, "__init__UPD.py"), "w")
            newFile.write(git_addon)
            newFile.close()

 
            
            os.replace(os.path.join(filePath, "__init__UPD.py"), os.path.join(filePath, "__init__.py"))
            bpy.ops.script.reload()
            #sys.modules['Master_Instance-main'].update_addon() 
    else:
        print('Error downloading file')
         
class MInstance_Addon_Updater(Operator):
    bl_idname = "minstance.addon_upd"
    bl_label = "Update Addon"
    bl_description = "Update Addon from Github"
    #bl_options = {'REGISTER', 'UNDO'} 
    
        
    def execute(self, context):
        update_addon(self)
        return {'FINISHED'}   
 

#Menu Settings
class VIEW3D_MT_InstanceM_Settings(bpy.types.Menu):
    bl_label = "Instance Master Settings"
    
    def draw(self, context):
        
        layout = self.layout

        scene = context.scene

        layout.label(text="Settings:")
        
        
        layout.separator()
        col = layout.column()
         
        col.operator("minstance.addon_upd", icon = "URL") 
         
        op = col.operator(
            'wm.url_open',
            text='Contact Me',
            icon='CURRENT_FILE'
            )
        op.url = 'https://t.me/Mandrew3d'
                
class MINSTANCE_PT_Operators(bpy.types.Panel):
    addon_name = 'Master_Instance-main'
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
        #c_text = ''
        row = col.row(align = True)
        row.operator("minstance.get_obj_path", icon = "COPYDOWN", text = c_text)  
        if bpy.data.is_saved:
            if bpy.data.is_dirty:
                row.operator("minstance.save_file", icon = "ERROR", text = '')  
        
        file_path = get_addon_folder(True)
        #file_path = bpy.path.abspath(bpy.utils.user_resource("SCRIPTS") + '\\Master_Instance-main\\MasterInstance_Buffer.txt')
        
        with open(file_path, "r") as file:
            clipboard = file.read()   
        clipboard = try_convert_to_list(clipboard)
        c_name = 'No Object in Copy'
        if clipboard is not None:
            c_name = clipboard[2]                        
        #c_name = ''
        text = "Link '" + str(c_name) + "' Collection"
        #col.alert  = True
        col.operator("minstance.paste_obj_as_instance", icon = "PASTEDOWN", text = text)  
        
        
        #settings
        row = layout.row()
        row.menu("VIEW3D_MT_InstanceM_Settings", icon = "PREFERENCES", text = '' )
        ver = bl_info.get('version')
        ver = str(ver[0])+('.')+str(ver[1])
        
        row.label(text = 'Version: ' + ver)  
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
        

class MInstance_Preferences(bpy.types.AddonPreferences):
    bl_idname = __name__

 
    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("minstance.addon_upd", icon = "URL")
                   
classes = [
    MAKE_OT_Instance,
    GET_OT_Collection,
    OPEN_OT_Linked,
    RELOAD_OT_Linked,
    Get_OT_Object_Path,
    Save_OT_File,
    Paste_OT_Object_As_Intance,
       
    MINSTANCE_PT_Operators,
    MInstance_Addon_Updater,
    VIEW3D_MT_InstanceM_Settings,
    VIEW3D_MT_object_mode_minstance,
    MInstance_Preferences,
        
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
