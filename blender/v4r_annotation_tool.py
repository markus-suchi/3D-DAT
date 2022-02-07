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


def update_alpha(self, context):
    v4r_infos = context.scene.v4r_infos
    v4r_blender_utils.set_alpha(v4r_infos.color_alpha)


def update_color_type(self, context):
    bpy.context.space_data.shading.color_type = self.color_type


class V4R_PG_scene_ids(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Scene Id",
                                   description="Identifyer for recorder scene."
                                   )


class V4R_PG_infos(bpy.types.PropertyGroup):
    dataset_file: bpy.props.StringProperty(name="Dataset")
    scene_id: bpy.props.StringProperty(name="Scene Id")
    scene_ids: bpy.props.CollectionProperty(
        name="Scene Id List", type=V4R_PG_scene_ids)
    color_alpha: bpy.props.FloatProperty(name="Transparency", min=0.0, max=1.0,
                                         default=0.5,
                                         update=update_alpha, options=set())
    color_type:  bpy.props.EnumProperty(name="Display",
                                        items=[('OBJECT', 'COLOR', 'Object Color'),
                                               ('VERTEX', 'VERTEX', 'Vertex Color')],
                                        update=update_color_type, options=set())


class V4R_OT_import_scene(bpy.types.Operator):
    bl_idname = "v4r.import_scene"
    bl_label = "Import Scene"
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(self, context):
        return SCENE_FILE_READER is not None

    def execute(self, context):
        global SCENE_FILE_READER

        if not SCENE_FILE_READER:
            text = "You need to load a dataset file first."
            self.report({'ERROR'}, text)
            print(text)
            return {'CANCELLED'}

        id = context.scene.v4r_infos.scene_id
        if(id):
            bpy.context.window.cursor_set("WAIT")
            print("Importing Scene %s" % id)
            cam_views = v4r_blender_utils.get_cam_views()
            v4r_blender_utils.load_objects(SCENE_FILE_READER, id)
            v4r_blender_utils.load_cameras(SCENE_FILE_READER, id)
            v4r_blender_utils.set_camera(
                bpy.data.collections['cameras'].objects[0])
            for view in cam_views:
                bpy.ops.object.select_all(action='DESELECT')
                view.view_perspective = 'CAMERA'

            bpy.context.window.cursor_set("DEFAULT")
            update_alpha(self, context)
            # set to vertex color
            context.scene.v4r_infos.color_type = "VERTEX"
            return {'FINISHED'}
        else:
            print("No scene selected. Import canceled.")
            return {'CANCELLED'}


class V4R_OT_load_dataset(bpy.types.Operator):
    """ Loading dataset information """

    bl_idname = "v4r.load_dataset"
    bl_label = "Load Dataset"
    bl_options = {'REGISTER', 'UNDO'}
    filepath: bpy.props.StringProperty(subtype="FILE_PATH", default="*.yaml")
    loaded: bpy.props.BoolProperty(name="loaded", default=False)

    def execute(self, context):
        global SCENE_FILE_READER

        bpy.context.window.cursor_set("WAIT")
        print("Opening Dataset Library: " + self.filepath)
        SCENE_FILE_READER = v4r.io.SceneFileReader.create(self.filepath)

        context.scene.v4r_infos.dataset_file = self.filepath
        context.scene.v4r_infos.scene_ids.clear()
        for item in SCENE_FILE_READER.scene_ids:
            context.scene.v4r_infos.scene_ids.add().name = item

        # Set to first entry
        if context.scene.v4r_infos.scene_ids:
            context.scene.v4r_infos.scene_id = context.scene.v4r_infos.scene_ids[0].name

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
    # filepath: bpy.props.StringProperty(
    # subtype="FILE_PATH", default="./poses.yaml")

    def execute(self, context):
        id = bpy.context.scene.v4r_infos.scene_id

        objects_available = bpy.data.collections.get("objects")
        if not objects_available:
            print("No objects to save a pose available.")
            return {'FINISHED'}
        elif SCENE_FILE_READER and id:
            full_path = os.path.join(SCENE_FILE_READER.root_dir,
                                     SCENE_FILE_READER.annotation_dir,
                                     id,
                                     SCENE_FILE_READER.object_pose_file)

            print("Saving poses to: " + full_path)
            output_list = []
            for obj in bpy.data.collections['objects'].objects:
                print("Saving object %s, id %s." % (obj.name, obj["v4r_id"]))
                pose = np.zeros((4, 4))
                pose[:, :] = obj.matrix_world
                pose = pose.reshape(-1)
                # get id from object mesh property
                output_list.append(
                    {"id": int(obj["v4r_id"]), "pose": pose.tolist()})

            if output_list:
                with open(full_path, 'w') as f:
                    yaml.dump(output_list, f, default_flow_style=False)
                    self.report({'INFO'},"Saving successful")
            return {'FINISHED'}
        else:
            print("You need to open the dataset file first and import a scene.")
            return {'CANCELLED'}


class V4R_PT_annotation(bpy.types.Panel):
    bl_label = "V4R Annotation"
    bl_idname = "V4R_PT_annotation"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "3D-SADT"

    @classmethod
    def poll(self, context):
        return context.area.type == 'VIEW_3D'

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        scene = context.scene
        v4r_infos = scene.v4r_infos

        flow = layout.grid_flow(row_major=True, columns=0,
                                even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(v4r_infos, "dataset_file", icon="COLLECTION_NEW")
        col.operator("v4r.load_dataset")

        col.separator()

        col.prop_search(v4r_infos, "scene_id", v4r_infos,
                        "scene_ids", icon="IMAGE_DATA")
        col.operator("v4r.import_scene")

        col.separator()

        col.operator("v4r.save_pose")

        col.separator()

        col.prop(context.area.spaces.active, "camera", icon='CAMERA_DATA')

        col.separator()

        row = col.row()

        row.prop(v4r_infos, "color_type", expand=True)

        row = col.row()

        color_alpha = row.prop(v4r_infos, "color_alpha", slider=True)
        if v4r_infos.color_type == 'VERTEX':
            row.enabled = False
        else:
            row.enabled = True


def register():
    bpy.utils.register_class(V4R_PG_scene_ids)
    bpy.utils.register_class(V4R_PG_infos)
    bpy.utils.register_class(V4R_PT_annotation)
    bpy.utils.register_class(V4R_OT_load_dataset)
    bpy.utils.register_class(V4R_OT_import_scene)
    bpy.utils.register_class(V4R_OT_save_pose)

    bpy.types.Scene.v4r_infos = bpy.props.PointerProperty(type=V4R_PG_infos)


def unregister():
    bpy.utils.unregister_class(V4R_PG_scene_ids)
    bpy.utils.unregister_class(V4R_PG_infos)
    bpy.utils.unregister_class(V4R_PT_annotation)
    bpy.utils.unregister_class(V4R_OT_load_dataset)
    bpy.utils.unregister_class(V4R_OT_import_scene)
    bpy.utils.unregister_class(V4R_OT_save_pose)

    del bpy.types.Scene.v4r_infos

# if __name__ == "__main__":
#    register()
