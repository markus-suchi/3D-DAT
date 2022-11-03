import os
import sys
import numpy as np
from numpy.linalg import inv
import yaml
import bpy
import mathutils

from .. import v4r_dataset_toolkit as v4r
from . import v4r_blender_utils

SCENE_FILE_READER = None
SCENE_MESH = None


def update_alpha(self, context):
    v4r_infos = context.scene.v4r_infos
    v4r_blender_utils.set_alpha(v4r_infos.color_alpha)


def update_color_type(self, context):
    bpy.context.space_data.shading.color_type = self.color_type


def update_show_cameras(self, context):
    if 'cameras' in bpy.data.collections:
        cameras = [
            ob for ob in bpy.data.collections['cameras'].objects if ob.type == 'CAMERA']

        if not context.scene.v4r_infos.show_cameras:
            for items in cameras:
                items.hide_viewport = True
            # only current camera is viewable
            context.area.spaces.active.camera.hide_viewport = False
        else:
            for items in cameras:
                items.hide_viewport = False


def update_show_reconstruction(self, context):
    if 'reconstruction' in bpy.data.collections:
        objects = [
            ob for ob in bpy.data.collections['reconstruction'].objects if ob.type == 'MESH']

        for items in objects:
            items.hide_viewport = not context.scene.v4r_infos.show_reconstruction


class V4R_UL_object_selector(bpy.types.UIList):
    """
    List of available objects
    """

    first_run: bpy.props.BoolProperty(name="first_run", default=True)

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        if self.first_run:
            self.use_filter_show = True
            self.use_filter_sort_alpha = True
            self.first_run = False

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.label(text=item.id)
            layout.label(text=item.name)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.label(text=item.id)


class V4R_PG_scene_ids(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Scene Id",
                                   description="Identifyer for recorder scene."
                                   )


class V4R_PG_object_list(bpy.types.PropertyGroup):
    id: bpy.props.StringProperty(name="Object Id",
                                 description="Object identifyer."
                                 )

    pose: bpy.props.FloatVectorProperty(name="Pose",
                                        description="Object pose.",
                                        size=16
                                        )


class V4R_PG_object_selector_entry(bpy.types.PropertyGroup):
    id: bpy.props.StringProperty(name="Object Id",
                                 description="Object identifyer."
                                 )
    name: bpy.props.StringProperty(name="Name",
                                   description="Object name."
                                   )


class V4R_PG_object_selector(bpy.types.PropertyGroup):
    objects: bpy.props.CollectionProperty(type=V4R_PG_object_selector_entry)
    index: bpy.props.IntProperty()


class V4R_PG_infos(bpy.types.PropertyGroup):
    dataset_file: bpy.props.StringProperty(name="Dataset")
    # the current imported scene_id
    scene_id: bpy.props.StringProperty(name="Scene Id")
    # the scene_id selected from the Scene Id List
    selected_scene_id: bpy.props.StringProperty(name="Selected Scene Id")
    scene_ids: bpy.props.CollectionProperty(
        name="Scene Id List", type=V4R_PG_scene_ids)
    color_alpha: bpy.props.FloatProperty(name="Transparency", min=0.0, max=1.0,
                                         default=0.5,
                                         update=update_alpha, options=set())
    color_type:  bpy.props.EnumProperty(name="Display",
                                        items=[('OBJECT', 'COLOR', 'Object Color'),
                                               ('VERTEX', 'VERTEX', 'Vertex Color')],
                                        update=update_color_type, options=set())
    show_cameras: bpy.props.BoolProperty(name="Show cameras", default=True,
                                         update=update_show_cameras, options=set())
    show_reconstruction: bpy.props.BoolProperty(name="Show reconstruction", default=True,
                                         update=update_show_reconstruction, options=set())
    object_list: bpy.props.CollectionProperty(
        name="Loaded Objects", type=V4R_PG_object_list)


class V4R_OT_import_scene(bpy.types.Operator):
    bl_idname = "v4r.import_scene"
    bl_label = "Import Scene"
    bl_options = {'REGISTER', 'UNDO'}
    draw: bpy.props.BoolProperty(name="draw", default=False)

    @classmethod
    def poll(self, context):
        return SCENE_FILE_READER is not None

    def execute(self, context):
        global SCENE_FILE_READER
        global SCENE_MESH

        if not SCENE_FILE_READER:
            text = "You need to load a dataset file first."
            self.report({'ERROR'}, text)
            print(text)
            return {'CANCELLED'}

        id = context.scene.v4r_infos.selected_scene_id
        if(id):
            bpy.context.window.cursor_set("WAIT")
            context.scene.v4r_infos.scene_id = id
            print("Importing Scene %s" % id)
            cam_views = v4r_blender_utils.get_cam_views()
            v4r_blender_utils.load_objects(SCENE_FILE_READER, id)
            v4r_blender_utils.load_cameras(SCENE_FILE_READER, id)
            v4r_blender_utils.set_camera(
                bpy.data.collections['cameras'].objects[0])
            for view in cam_views:
                bpy.ops.object.select_all(action='DESELECT')
                view.view_perspective = 'CAMERA'

            update_alpha(self, context)
            update_show_cameras(self, context)
            # set to vertex color
            context.scene.v4r_infos.color_type = "VERTEX"
            SCENE_MESH = v4r_blender_utils.load_reconstruction(
                SCENE_FILE_READER, id)

            v4r_blender_utils.remove_reconstruction_visual()
            update_show_reconstruction(self, context)

            bpy.context.window.cursor_set("DEFAULT")

            return {'FINISHED'}
        else:
            print("No scene selected. Import canceled.")
            return {'CANCELLED'}

    def invoke(self, context, event):
        # check if poses of objects has changed since import
        # compare current objects with loaded_object list
        doit = v4r_blender_utils.has_scene_changed() 
        if doit:
            return context.window_manager.invoke_props_dialog(self)
        else:
            return self.execute(context)

    def draw(self, context):
        row = self.layout.column(align=True)
        row.label(text="There are unsaved changes!", icon='ERROR')
        row.label(text="Press 'OK' to proceed loading and loose changes.")
        row.label(text="Press 'Esc' to cancel.")


class V4R_OT_load_dataset(bpy.types.Operator):
    """ Loading dataset information """

    bl_idname = "v4r.load_dataset"
    bl_label = "Load Dataset"
    bl_options = {'REGISTER', 'UNDO'}
    filepath: bpy.props.StringProperty(subtype="FILE_PATH", default="*.yaml")
    loaded: bpy.props.BoolProperty(name="loaded", default=False)

    def populate_object_selector(self, context):
        context.scene.object_selector.objects.clear()
        if SCENE_FILE_READER:
            objects = SCENE_FILE_READER.get_object_library().as_list()
            if objects:
                # add items
                for obj in objects:
                    item = context.scene.object_selector.objects.add()
                    item.name = obj.name
                    item.id   = obj.id
            else:
                self.report({'Error'}, 'Opening Object Libraray failed.')
               
 
    def execute(self, context):
        global SCENE_FILE_READER

        bpy.context.window.cursor_set("WAIT")
        print("Opening Dataset Library: " + self.filepath)
        SCENE_FILE_READER = v4r.io.SceneFileReader.create(self.filepath)
        if(SCENE_FILE_READER):
            print(SCENE_FILE_READER)

        context.scene.v4r_infos.dataset_file = self.filepath
        context.scene.v4r_infos.scene_ids.clear()
        for item in SCENE_FILE_READER.scene_ids:
            context.scene.v4r_infos.scene_ids.add().name = item

        # Set to first entry
        if context.scene.v4r_infos.scene_ids:
            context.scene.v4r_infos.selected_scene_id = context.scene.v4r_infos.scene_ids[0].name

        # Populate object list for adding models
        self.populate_object_selector(context)

        # Blender does not update content of dropdownlists for custom property collections
        v4r_blender_utils.tag_redraw_all()
        bpy.context.window.cursor_set("DEFAULT")
        return {'FINISHED'}

    def invoke(self, context, event):
        # set filepath with default value of property
        self.filepath = self.filepath
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class V4R_OT_save_pose(bpy.types.Operator):
    bl_idname = "v4r.save_pose"
    bl_label = "Save Objects"

    def execute(self, context):
        global SCENE_FILE_READER

        id = bpy.context.scene.v4r_infos.scene_id
        objects_available = bpy.data.collections.get("objects")
        if not objects_available:
            print("No objects to save a pose available.")
            return {'FINISHED'}
        elif SCENE_FILE_READER and id:
            v4r_blender_utils.save_pose(SCENE_FILE_READER, id)
            return {'FINISHED'}
        else:
            print("You need to open the dataset file first and import a scene.")
            return {'CANCELLED'}


class V4R_OT_align_object(bpy.types.Operator):
    """ Align selected object to scene. """

    bl_idname = "v4r.align_object"
    bl_label = "Align"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        global SCENE_FILE_READER
        global SCENE_MESH
        return (v4r_blender_utils.has_active_object_id() and context.area.type == 'VIEW_3D' and
                SCENE_FILE_READER and SCENE_MESH)

    def execute(self, context):
        global SCENE_FILE_READER
        global SCENE_MESH
        bpy.context.window.cursor_set("WAIT")
        v4r_blender_utils.align_current_object(SCENE_FILE_READER, SCENE_MESH)
        bpy.context.window.cursor_set("DEFAULT")
        return {'FINISHED'}


class V4R_OT_import_reconstruction(bpy.types.Operator):
    """ Import reconstruction of scene. """

    bl_idname = "v4r.import_reconstruction"
    bl_label = "Import Reconstruction"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return SCENE_FILE_READER is not None

    def execute(self, context):
        global SCENE_FILE_READER

        bpy.context.window.cursor_set("WAIT")
        id = context.scene.v4r_infos.scene_id
        if(id):
            v4r_blender_utils.load_reconstruction_visual(SCENE_FILE_READER, id)
            update_show_reconstruction(self, context)
 
        bpy.context.window.cursor_set("DEFAULT")
        return {'FINISHED'}

class V4R_OT_add_object(bpy.types.Operator):
    """ Add object to scene. """

    bl_idname = "v4r.add_object"
    bl_label = "Add Object"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return SCENE_FILE_READER is not None

    def execute(self, context):
        global SCENE_FILE_READER

        bpy.context.window.cursor_set("WAIT")
        scene = context.scene
        scene_id = scene.v4r_infos.scene_id
        if(scene_id):
            object = scene.object_selector.objects[scene.object_selector.index]
            v4r_blender_utils.add_object(SCENE_FILE_READER, object.id) 
        bpy.context.window.cursor_set("DEFAULT")
        return {'FINISHED'}


class V4R_PT_annotation(bpy.types.Panel):
    bl_label = "Annotate"
    bl_idname = "V4R_PT_annotation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "3D-SADT"

    @classmethod
    def poll(self, context):
        scene = context.scene
        v4r_infos = scene.v4r_infos
        return context.area.type == 'VIEW_3D' and v4r_infos.scene_id

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        v4r_infos = scene.v4r_infos
        
        col = layout.column(align=True)

        row = col.row(align=True)
        row.prop(v4r_infos, "scene_id", text="Scene:", icon='IMAGE_DATA')
        row.enabled = False

        col.separator()

        col.operator("v4r.align_object")

        col.separator()

        col.operator("v4r.save_pose")

        col.separator()

        row = col.row(align=True)
        row.label(text="Camera:")
        row.prop(context.area.spaces.active, "camera", text="", icon='CAMERA_DATA')
        row.prop(v4r_infos, "show_cameras", toggle=True, expand=False, icon='HIDE_OFF', icon_only=True)
        
        col.separator()

        row = col.row(align=True)
        row.label(text="Display:")
        row.prop(v4r_infos, "color_type", expand=True)
        
        col.separator()

        row = col.row(align=True)
        row.label(text="Scene Alpha:")
        color_alpha = row.prop(v4r_infos, "color_alpha", text="", slider=True, expand=True)
        if v4r_infos.color_type == 'VERTEX':
            row.enabled = False
        else:
            row.enabled = True

        col.separator()

        row = col.row(align=True)
        obj = context.active_object
        if obj: 
            row.prop(obj,"color", text="Object Color:")
        else:
            row.label(text="Object Color:")

        if v4r_infos.color_type == 'VERTEX':
            row.enabled = False
        else:
            row.enabled = True

        col.separator()

        row = col.row(align=True)
        row.label(text="Reconstruction:")
        row.operator("v4r.import_reconstruction", text="Import")
        row.prop(v4r_infos, "show_reconstruction", toggle=True, icon='HIDE_OFF', icon_only=True)

class V4R_PT_object_library(bpy.types.Panel):
    bl_label = "Object Library"
    bl_idname = "V4R_PT_object_library"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "3D-SADT"

    @classmethod
    def poll(self, context):
        return context.area.type == 'VIEW_3D'

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        v4r_infos = scene.v4r_infos

        col = layout.column(align=True)
        col.template_list("V4R_UL_object_selector", "", scene.object_selector, "objects", scene.object_selector, "index")
        col.operator("v4r.add_object", text="Add Object")  
        
class V4R_PT_import(bpy.types.Panel):
    bl_label = "Import"
    bl_idname = "V4R_PT_import"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "3D-SADT"

    @classmethod
    def poll(self, context):
        return context.area.type == 'VIEW_3D'

    def draw(self, context):
        layout = self.layout

        scene = context.scene
        v4r_infos = scene.v4r_infos

        col = layout.column(align=True)
        col.prop(v4r_infos, "dataset_file", icon="COLLECTION_NEW")
        col.operator("v4r.load_dataset")

        col.separator()

        col.prop_search(v4r_infos, "selected_scene_id", v4r_infos,
                        "scene_ids", icon="IMAGE_DATA",text="Scene")
        col.operator("v4r.import_scene")


def register():
    bpy.utils.register_class(V4R_PG_object_list)
    bpy.utils.register_class(V4R_PG_object_selector_entry)
    bpy.utils.register_class(V4R_PG_object_selector)
    bpy.utils.register_class(V4R_PG_scene_ids)
    bpy.utils.register_class(V4R_PG_infos)
    bpy.utils.register_class(V4R_PT_import)
    bpy.utils.register_class(V4R_PT_annotation)
    bpy.utils.register_class(V4R_PT_object_library)
    bpy.utils.register_class(V4R_OT_load_dataset)
    bpy.utils.register_class(V4R_OT_import_scene)
    bpy.utils.register_class(V4R_OT_save_pose)
    bpy.utils.register_class(V4R_OT_align_object)
    bpy.utils.register_class(V4R_OT_import_reconstruction)
    bpy.utils.register_class(V4R_OT_add_object)
    bpy.utils.register_class(V4R_UL_object_selector)

    bpy.types.Scene.object_selector = bpy.props.PointerProperty(
                name="Objects",
                type=V4R_PG_object_selector
            )

    bpy.types.Scene.v4r_infos = bpy.props.PointerProperty(type=V4R_PG_infos)


def unregister():
    bpy.utils.unregister_class(V4R_PG_object_selector)
    bpy.utils.unregister_class(V4R_PG_object_selector_entry)
    bpy.utils.unregister_class(V4R_PG_object_list)
    bpy.utils.unregister_class(V4R_PG_scene_ids)
    bpy.utils.unregister_class(V4R_PG_infos)
    bpy.utils.unregister_class(V4R_PT_import)
    bpy.utils.unregister_class(V4R_PT_annotation)
    bpy.utils.unregister_class(V4R_PT_object_library)
    bpy.utils.unregister_class(V4R_OT_load_dataset)
    bpy.utils.unregister_class(V4R_OT_import_scene)
    bpy.utils.unregister_class(V4R_OT_save_pose)
    bpy.utils.unregister_class(V4R_OT_align_object)
    bpy.utils.unregister_class(V4R_OT_import_reconstruction)
    bpy.utils.unregister_class(V4R_OT_add_object)
    bpy.utils.unregister_class(V4R_UL_object_selector)

    del bpy.types.Scene.v4r_infos
    del bpy.types.Scene.object_selector

# if __name__ == "__main__":
#    register()
