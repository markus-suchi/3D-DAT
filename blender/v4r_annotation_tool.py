import os
import sys
import numpy as np
from numpy.linalg import inv
import yaml
import bpy
import mathutils

from . import v4r_dataset_toolkit as v4r
from . import v4r_camera

SCENE_FILE_READER = None


# https://blender.stackexchange.com/questions/45138/buttons-for-custom-properties-dont-refresh-when-changed-by-other-parts-of-the-s
# Auto refresh for custom collection property does not work without tagging a redraw
def tag_redraw(context, space_type="PROPERTIES", region_type="WINDOW"):
    """ Redraws given windows area of specific type """
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.spaces[0].type == space_type:
                for region in area.regions:
                    if region.type == region_type:
                        region.tag_redraw()


def load_objects(id):
    objects = []
    if(SCENE_FILE_READER):
        objects = SCENE_FILE_READER.get_object_poses(id)

    if "objects" not in bpy.data.collections:
        obj_collection = bpy.ops.collection.create(name="objects")
        bpy.context.scene.collection.children.link(
            bpy.data.collections["objects"])
    else:
        # Remove previous loaded objects
        # TODO: do not reimport already loaded objects, just reset position
        for o in bpy.data.collections["objects"].objects:
            m = bpy.data.meshes[o.name]
            bpy.data.objects.remove(o, do_unlink=True)
            bpy.data.meshes.remove(m, do_unlink=True)

    for item in objects:
        mesh = item[0].mesh.as_bpy_mesh()
        obj_id = str(item[0].id)
        mesh.name = obj_id + "_" + item[0].name
        obj = bpy.data.objects.new(mesh.name, mesh)
        obj.matrix_world = mathutils.Matrix(np.asarray(item[1]).reshape(4, 4))
        obj["v4r_id"] = obj_id
        bpy.data.collections["objects"].objects.link(obj)


# class load_pose(bpy.types.Operator):
    # bl_idname = "pose.load"
    # bl_label = "Load Pose"
    # filepath: bpy.props.StringProperty(
        # subtype="FILE_PATH", default="./poses.yaml")

    # def execute(self, context):
        # print("Loading poses from: " + self.filepath)
        # # load object infos from OBJECT_LIBRARY
        # output_list = []
        # # for each entry load the object mesh
        # # transform the object using pose entry
        # # link object with scene in object collection
        # # add/set custom attribute for mesh/object storing the id
        # for obj in bpy.data.collections['objects'].objects:
        # print("obj: ", obj.name)
        # pose = np.zeros((4, 4))
        # pose[:, :] = obj.matrix_world
        # # try to get to same coordinate system as jnb reprojection
        # # pose[:3,:3] = pose[:3, :3] * -1
        # # pose[:3, 0] = pose[:3, 0] * -1
        # pose = pose.reshape(-1)
        # # get id from object mesh property
        # output_list.append(
        # {"path": "-/Test.ply", "id": obj.name, "pose": pose.tolist()})

        # if output_list:
        # print(yaml.dump(output_list, default_flow_style=False))
        # with open(self.filepath, 'w') as f:
        # yaml.dump(output_list, f, default_flow_style=False)

        # return {'FINISHED'}

    # def invoke(self, context, event):
        # # set filepath with default value of property
        # self.filepath = self.filepath
        # context.window_manager.fileselect_add(self)
        # print(self.filepath)
        # return {'RUNNING_MODAL'}


class V4R_PG_scene_ids(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Scene Id",
                                   description="Identifyer for recorder scene."
                                   )


class V4R_PG_infos(bpy.types.PropertyGroup):
    dataset_file: bpy.props.StringProperty(name="Dataset")
    scene_id: bpy.props.StringProperty(name="Scene Id")
    scene_ids: bpy.props.CollectionProperty(
        name="Scene Id List", type=V4R_PG_scene_ids)


class V4R_OT_import_scene(bpy.types.Operator):
    bl_idname = "v4r.import_scene"
    bl_label = "Import Scene"

    def execute(self, context):
        global SCENE_FILE_READER

        if not SCENE_FILE_READER:
            print("You need to open the dataset file first.")
            return {'CANCELLED'}

        id = context.scene.v4r_infos.scene_id
        if(id):
            print("Importing Scene %s" % id)
            camera = SCENE_FILE_READER.get_camera_info()
            camera_path = os.path.join(
                SCENE_FILE_READER.root_dir, SCENE_FILE_READER.scenes_dir,
                id,
                SCENE_FILE_READER.camera_pose_file)
            camera_rgb_path = os.path.join(
                SCENE_FILE_READER.root_dir, SCENE_FILE_READER.scenes_dir,
                id,
                SCENE_FILE_READER.rgb_dir)

            v4r_camera.add_cameras(camera_path=camera_path,
                                   camera_rgb_path=camera_rgb_path,
                                   invert=False,
                                   intrinsics=camera.as_numpy3x3(),
                                   width=camera.width,
                                   height=camera.height,
                                   lens=camera.lens(),
                                   fov=camera.fov(),
                                   sensor_width=camera.sensor_width,
                                   shift_x=camera.shift_x(),
                                   shift_y=camera.shift_y())

            load_objects(id)
            return {'FINISHED'}
        else:
            print("No scene selected. Import canceled.")
            return {'CANCELLED'}


class V4R_OT_load_dataset(bpy.types.Operator):
    """ Loading dataset information """

    bl_idname = "v4r.load_dataset"
    bl_label = "Load Dataset"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH", default="*.yaml")
    loaded: bpy.props.BoolProperty(name="loaded", default=False)

    def execute(self, context):
        global SCENE_FILE_READER

        print("Opening Dataset Library: " + self.filepath)
        SCENE_FILE_READER = v4r.io.SceneFileReader.create(self.filepath)

        context.scene.v4r_infos.dataset_file = self.filepath

        # Fill in CollectionProperty List with scene ids
        context.scene.v4r_infos.scene_ids.clear()
        for item in SCENE_FILE_READER.scene_ids:
            context.scene.v4r_infos.scene_ids.add().name = item

        # Set to first entry
        if context.scene.v4r_infos.scene_ids:
            context.scene.v4r_infos.scene_id = context.scene.v4r_infos.scene_ids[0].name

        # Blender does not update content of dropdownlists for custom property collections
        # Trigger redraw
        tag_redraw(context)

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
                                     SCENE_FILE_READER.scenes_dir,
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
            return {'FINISHED'}
        else:
            print("You need to open the dataset file first and import a scene.")
            return {'CANCELLED'}


class V4R_PT_annotation(bpy.types.Panel):
    bl_label = "V4R Annotation"
    bl_idname = "V4R_PT_annotation"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

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
