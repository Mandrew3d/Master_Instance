addon_name = 'Instance Master'
bl_info = {
    "name": addon_name ,
    "author": "Mandrew3D",
    "version": (2, 0),
    "blender": (5, 0, 1),
    "location": "View3D > UI > M_Instance",
    "description": "Addon that helps to work with various types of instances ",
    "warning": "",
    "doc_url": "",
    "category": "Mods",
}


import bpy
from bpy.types import Operator
from bpy.utils import register_class, unregister_class
from mathutils import Vector
import os
import addon_utils
from mathutils import Vector

import json
import tempfile
import time


def get_z_distance_to_floor(objs):
    ctx = bpy.context
    active = ctx.active_object
    if not active:
        raise RuntimeError("Нет активного объекта")

    depsgraph = ctx.evaluated_depsgraph_get()
    min_z = None

    for obj in ctx.selected_objects:
        if obj.type != 'MESH':
            continue

        eval_obj = obj.evaluated_get(depsgraph)
        mesh = eval_obj.to_mesh()
        mw = eval_obj.matrix_world

        for v in mesh.vertices:
            z = (mw @ v.co).z
            min_z = z if min_z is None else min(min_z, z)

        eval_obj.to_mesh_clear()

    if min_z is None:
        raise RuntimeError("Нет выделенных меш-объектов")

    return min_z - active.matrix_world.to_translation().z


def hide_collection_by_name(col_name: str):
    """
    Скрывает (exclude) коллекцию с именем col_name в текущем View Layer.
    """
    def find_layer_collection(layer_collection, name):
        if layer_collection.collection.name == name:
            return layer_collection
        for child in layer_collection.children:
            result = find_layer_collection(child, name)
            if result:
                return result
        return None

    layer_coll = find_layer_collection(bpy.context.view_layer.layer_collection, col_name)
    if layer_coll:
        layer_coll.exclude = True
    else:
        print(f"Коллекция '{col_name}' не найдена в текущем View Layer")


def move_selected_to_collection(col_name):
    # Получаем или создаём коллекцию
    col = bpy.data.collections.get(col_name)
    if col is None:
        col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(col)
        
    # Перенос объектов
    for obj in bpy.context.selected_objects:
        # Удаляем из всех текущих коллекций
        for c in obj.users_collection:
            c.objects.unlink(obj)
        # Добавляем в целевую
        col.objects.link(obj)
        
def get_root_parent(obj):
    if obj is None:
        return None
    
    p = obj
    while p.parent is not None:
        p = p.parent
    return p

#Make Instance Colletion of selected objects
def make_instance(self, context):
    col_name = self.col_name
    use_floor = self.use_floor
    act_obj = context.object
    iter = self.iter
    
    
    obj = get_root_parent(act_obj)
    
#    if iter:
#        self.col_name = 'MI_Instance_' + obj.name
#        self.iter = False
    
    bpy.ops.object.select_grouped(extend=True, type='CHILDREN_RECURSIVE')
        

    bpy.ops.object.parent_set(type='OBJECT', keep_transform=True)
    sel_objs = bpy.context.selected_objects
    
    move_selected_to_collection(self.col_name)
    
    save_loc = obj.location
    save_rot = obj.rotation_euler
    
#    if use_floor:
#        z_loc = -(get_z_distance_to_floor(sel_objs))
#        print(z_loc)
#    else:
    z_loc = 0
        
    
    inst_obj = bpy.ops.mesh.primitive_plane_add(enter_editmode=False, align='WORLD', location=(save_loc), rotation=(save_rot), scale=(1, 1, 1))
    
    
    obj.rotation_euler = (0,0,0)
    obj.location = (0,0, z_loc)
    
    bpy.ops.object.modifier_add_node_group(asset_library_type='ESSENTIALS', asset_library_identifier="", relative_asset_identifier="nodes\\geometry_nodes_essentials.blend\\NodeTree\\Geometry Input")
    
    inst_obj = context.active_object
    mod = inst_obj.modifiers[0]
    mod["Socket_6"] = 1
    mod["Socket_3"] = bpy.data.collections[self.col_name]
    mod["Socket_1"] = True
    
    #mod['Input Type']
    inst_obj.location = inst_obj.location
    hide_collection_by_name(self.col_name)
    
class MAKE_OT_Instance(Operator):
    bl_idname = "minstance.make_instance"
    bl_label = "Convert to Instance"
    bl_description = "Make Instance Colletion of selected objects"
    bl_options = {'REGISTER', 'UNDO'}
    
    col_name :  bpy.props.StringProperty(default = 'MI_Instance')
    use_floor: bpy.props.BoolProperty(default = True)
    iter: bpy.props.BoolProperty(default = True)
        
    @classmethod
    def poll(cls, context):
        return context.active_object is not None
    
    def draw(self, context):
        layout = self.layout
        layout.prop(self, "col_name", text = 'Name')
        #layout.prop(self, "use_floor", text = 'Drop on Floor')
    
    def invoke(self, context, event):
        self.col_name = 'MI_Instance_' + bpy.context.object.name
        return self.execute(context)
     
    def execute(self, context):
        make_instance(self, context)
        return {'FINISHED'}

#Edit collection 
def has_geometry_input_modifier():
    obj = bpy.context.object
    #print('test')
    return obj is not None and any(m.type == 'NODES' and m.name == "Geometry Input" for m in obj.modifiers)

def geom_input_uses_collection(obj=None, collection=None):
    """
    Проверяет, есть ли у объекта модификатор 'Geometry Input' и стоит ли в Socket_3 указанная коллекция.
    :param obj: объект (по умолчанию bpy.context.object)
    :param collection: объект bpy.types.Collection или имя коллекции
    :return: True/False
    """
    if obj is None:
        obj = bpy.context.object
    if obj is None or collection is None:
        return False

#    # привести collection к объекту Collection
#    if isinstance(collection, str):
#        collection = bpy.data.collections.get(collection)
#    if collection is None:
#        return False

    mod = obj.modifiers.get("Geometry Input")
    if not mod:
        return False

#    # получить Socket_3
#    try:
#        val = mod["Socket_3"]
#    except Exception:
#        val = getattr(mod, "Socket_3", None)

#    if isinstance(val, bpy.types.Collection):
#        return val == collection
#    if isinstance(val, str):
#        return val == collection.name
#    name = getattr(val, "name", None)
    val = mod["Socket_3"]
    print(val)
    if val == collection:
        return True
    else:
        print('falseee')
        return False
    #return name == collection.name if name else False


def get_collection(self, context):
    is_edit = self.is_edit
    
    ctx = bpy.context
    obj = ctx.object
    
    if is_edit:
        if obj.type == 'EMPTY' and context.object.instance_collection != None:
            print('is EMPTY')    
            #get instance col name
            s_col = obj.instance_collection

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
    #    else:
    #        cont_col = cont_ob.users_collection[0]
    #        if cont_col != context.scene.collection:
    #            vl_name = bpy.context.view_layer.name

    #            bpy.context.scene.view_layers[vl_name].layer_collection.children[cont_col.name].exclude = True
    #            
    #            bpy.ops.object.select_all(action='DESELECT')
    #            for ob in bpy.data.objects:
    #                if ob.type == 'EMPTY':
    #                    if ob.instance_collection:
    #                        #print(ob.instance_collection.name)
    #                        if ob.instance_collection.name == cont_col.name:
    #                            bpy.data.objects[ob.name].select_set(True)
    #                            bpy.context.view_layer.objects.active = ob
    #                            bpy.ops.view3d.view_selected(use_all_regions=True)
        else:


            if not obj:
                raise RuntimeError("Нет активного объекта")

            # получить модификатор Geometry Input
            mod_name = "Geometry Input"
            try:
                mod = obj.modifiers[mod_name]
            except KeyError:
                raise RuntimeError(f"Модификатор '{mod_name}' не найден")

            # проверить Socket_6 на "Collection"
            if mod["Socket_6"] != 1:
                raise RuntimeError(f"Socket_6 не равен 'Collection' (текущее значение: {mod['Socket_6']})")

            # получить коллекцию из Socket_3
            coll_val = mod["Socket_3"]
            if isinstance(coll_val, bpy.types.Collection):
                collection = coll_val
            elif isinstance(coll_val, str):
                collection = bpy.data.collections.get(coll_val)
            else:
                collection = None

            if not collection:
                raise RuntimeError(f"Не удалось разрешить коллекцию из Socket_3 (значение: {coll_val})")

            # снять exclude во view layer (рекурсивно)
            def find_layer_collection(layer_col, target):
                if layer_col.collection == target:
                    return layer_col
                for child in layer_col.children:
                    found = find_layer_collection(child, target)
                    if found:
                        return found
                return None

            lc = find_layer_collection(ctx.view_layer.layer_collection, collection)
            if lc:
                lc.exclude = False

            # выделяем все объекты коллекции
            for o in list(ctx.selected_objects):
                o.select_set(False)
            for o in collection.all_objects:
                o.select_set(True)
            
            bpy.ops.view3d.view_selected(use_all_regions=True)
            bpy.context.view_layer.objects.active  = bpy.context.selected_objects[0]
            return collection.name

    else:
        cont_col = obj.users_collection[0]
        if cont_col != context.scene.collection:
            vl_name = bpy.context.view_layer.name

            bpy.context.scene.view_layers[vl_name].layer_collection.children[cont_col.name].exclude = True
            
            bpy.ops.object.select_all(action='DESELECT')
            for ob in bpy.data.objects:
                if ob.type == 'EMPTY' or geom_input_uses_collection(ob, cont_col):
                    if ob.instance_collection:
                        #print(ob.instance_collection.name)
                        if ob.instance_collection.name == cont_col.name:
                            bpy.data.objects[ob.name].select_set(True)
                    else:
                        if geom_input_uses_collection(ob, cont_col):
                            bpy.data.objects[ob.name].select_set(True)
                            
                    bpy.context.view_layer.objects.active = ob
                    bpy.ops.view3d.view_selected(use_all_regions=True)

class GET_OT_Collection(Operator):
    bl_idname = "minstance.get_collection"
    bl_label = "Edit Relative Collection"
    bl_description = "Unhide collection of active instance"
    bl_options = {'REGISTER', 'UNDO'}
    
    is_edit : bpy.props.BoolProperty(name = 'Is_edit', default = False)

    
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



def save_object_source(self,context):
    # проверки
    
    TAG = "MasterInstance_TAG_v1"
    filename = "master_instance.json"
    if not bpy.data.is_saved:
        raise RuntimeError("Current .blend must be saved before saving instance info.")
    obj = context.object
    if obj is None:
        raise RuntimeError("No active object in context.")

    # данные
    blend_path = bpy.path.abspath(bpy.data.filepath)
    collections = [c.name for c in obj.users_collection]  # сохранение всех коллекций
    data = {
        "tag": TAG,
        "blend_path": blend_path,
        "collections": collections,
        "object_name": obj.name,
        "timestamp": int(time.time()),
        "blender_version": bpy.app.version_string
    }

    # каталог для хранения — в user config/ master_instance (кроссплатформенно и стабильно)
    base_dir = os.path.join(bpy.utils.user_resource('CONFIG'), "master_instance")
    os.makedirs(base_dir, exist_ok=True)
    file_path = os.path.join(base_dir, filename)

    # атомарная запись: tmp -> replace (меньше шанса порчи файла)
    fd, tmp_path = tempfile.mkstemp(prefix=filename, dir=base_dir, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, file_path)
    except Exception:
        # попытка удалить временный файл, если что-то пошло не так
        try:
            os.remove(tmp_path)
        except Exception:
            pass
        raise

    # дополнительно — положить JSON в буфер обмена для быстрого доступа
    try:
        bpy.context.window_manager.clipboard = json.dumps(data, ensure_ascii=False)
    except Exception:
        pass

    return file_path
            
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
        save_object_source(self, context)
        return {'FINISHED'}

#Paste Instance
TAG = "MasterInstance_TAG_v1"
FILENAME = "master_instance.json"


def get_storage_file_path():
    base_dir = os.path.join(
        bpy.utils.user_resource('CONFIG'),
        "master_instance"
    )
    return os.path.join(base_dir, FILENAME)

def link_collection_from_file(context):
    file_path = get_storage_file_path()

    if not os.path.exists(file_path):
        raise RuntimeError("Master instance file not found")

    # читаем JSON
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if data.get("tag") != TAG:
        raise RuntimeError("Invalid master instance tag")

    blend_path = data["blend_path"]
    collections = data["collections"]

    if not os.path.exists(blend_path):
        raise RuntimeError("Source .blend file not found")

    # берём первую сохранённую коллекцию
    col_name = collections[0]

    # линк ТОЛЬКО нужной коллекции
    with bpy.data.libraries.load(blend_path, link=True) as (data_from, data_to):
        if col_name not in data_from.collections:
            raise RuntimeError(f"Collection '{col_name}' not found in source file")
        data_to.collections = [col_name]

    linked_col = data_to.collections[0]

    # создаём instance
    instance = bpy.data.objects.new(linked_col.name, None)
    instance.instance_type = 'COLLECTION'
    instance.instance_collection = linked_col

    context.scene.collection.objects.link(instance)

    bpy.ops.object.select_all(action='DESELECT')
    instance.select_set(True)
    context.view_layer.objects.active = instance
        
        
class Paste_OT_Object_As_Instance(bpy.types.Operator):
    bl_idname = "minstance.paste_obj_as_instance"
    bl_label = "Paste Collection As Instance"
    bl_description = "Paste linked collection instance"

    @classmethod
    def poll(cls, context):
        path = get_storage_file_path()
        if not os.path.exists(path):
            return False

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return False

        return (
            isinstance(data, dict)
            and data.get("tag") == TAG
            and os.path.exists(data.get("blend_path", ""))
        )

    def execute(self, context):
        link_collection_from_file(context)
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
        col_edit = False 
        
        if has_geometry_input_modifier():
            col_name = 'Edit: '
            col_edit = True
            
        if bpy.context.object:
            if bpy.context.object.type == 'EMPTY':
                if bpy.context.object.instance_collection != None:
                    col_edit = True
                    col_name = bpy.context.object.instance_collection.name
                    col_name = 'Edit: ' + col_name
                    col_icon = "EDITMODE_HLT"
       
            
        edit = col.operator("minstance.get_collection", icon = col_icon, text = col_name) 
        edit.is_edit = col_edit
        
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
        if bpy.data.is_saved:
            if bpy.data.is_dirty:
                col.label(text='Dont Forget to save Blendfile', icon = 'ERROR')
        #col_name = context.object.users_collection[0]
        c_text = "Save Blend File First"
        if bpy.data.is_saved:
            c_text = "Select Any Object"    
            if bpy.context.active_object is not None and len(context.selected_objects)>0:
                if bpy.context.object.users_collection:
                    if bpy.context.object.users_collection[0] != context.scene.collection:
                        col_name = context.object.users_collection[0]
                        c_text = "Copy '" + col_name.name + "' As Instance"
                    else:
                        c_text = "'Scene Collection' Cannot Be Instanced"
                        
        col.operator("minstance.get_obj_path", icon = "COPYDOWN", text = c_text)  
        col.operator("minstance.paste_obj_as_instance", icon = "PASTEDOWN")  
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
        col_edit = False 
        if has_geometry_input_modifier():
            col_name = 'Edit: '
            col_edit = True
        if bpy.context.object:
            if bpy.context.object.type == 'EMPTY':
                if bpy.context.object.instance_collection != None:
                    col_edit = True
                    col_name = bpy.context.object.instance_collection.name
                    col_name = 'Edit: ' + col_name
                    col_icon = "EDITMODE_HLT"

        
        edit = col.operator("minstance.get_collection", icon = col_icon, text = col_name) 
        edit.is_edit = col_edit
        
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
    self.layout.menu("VIEW3D_MT_object_mode_minstance", icon = "OUTLINER_OB_GROUP_INSTANCE" )
    self.layout.separator()
      
        
           
classes = [
    MAKE_OT_Instance,
    GET_OT_Collection,
    OPEN_OT_Linked,
    RELOAD_OT_Linked,
    Get_OT_Object_Path,
    Paste_OT_Object_As_Instance,
        
    MINSTANCE_PT_Operators,
    VIEW3D_MT_object_mode_minstance,

        
]

def register():
    for cl in classes:
        register_class(cl)
    bpy.types.VIEW3D_MT_object_context_menu.prepend(menu_func_minstance)


def unregister():
    bpy.types.VIEW3D_MT_object_context_menu.remove(menu_func_minstance)
    for cl in reversed(classes):
        unregister_class(cl)


if __name__ == "__main__":
    register()
