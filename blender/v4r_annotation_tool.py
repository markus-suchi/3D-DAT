import os
import sys
import numpy as np
from numpy.linalg import inv
import yaml
import bpy

from . import v4r_dataset_toolkit as v4r

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


class save_pose(bpy.types.Operator):
    bl_idname = "pose.save"
    bl_label = "Save Pose"
    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH", default="./poses.yaml")

    def execute(self, context):
        print("Saving poses to: " + self.filepath)
        output_list = []
        for obj in bpy.data.collections['objects'].objects:
            print("obj: ", obj.name)
            pose = np.zeros((4, 4))
            pose[:, :] = obj.matrix_world
            # try to get to same coordinate system as jnb reprojection
            # pose[:3,:3] = pose[:3, :3] * -1
            # pose[:3, 0] = pose[:3, 0] * -1
            pose = pose.reshape(-1)
            # get id from object mesh property
            output_list.append(
                {"path": "-/Test.ply", "id": obj.name, "pose": pose.tolist()})

        if output_list:
            print(yaml.dump(output_list, default_flow_style=False))
            with open(self.filepath, 'w') as f:
                yaml.dump(output_list, f, default_flow_style=False)

        return {'FINISHED'}

    def invoke(self, context, event):
        # set filepath with default value of property
        self.filepath = self.filepath
        context.window_manager.fileselect_add(self)
        print(self.filepath)
        return {'RUNNING_MODAL'}


class load_pose(bpy.types.Operator):
    bl_idname = "pose.load"
    bl_label = "Load Pose"
    filepath: bpy.props.StringProperty(
        subtype="FILE_PATH", default="./poses.yaml")

    def execute(self, context):
        print("Loading poses from: " + self.filepath)
        # load object infos from OBJECT_LIBRARY
        output_list = []
        # for each entry load the object mesh
        # transform the object using pose entry
        # link object with scene in object collection
        # add/set custom attribute for mesh/object storing the id
        for obj in bpy.data.collections['objects'].objects:
            print("obj: ", obj.name)
            pose = np.zeros((4, 4))
            pose[:, :] = obj.matrix_world
            # try to get to same coordinate system as jnb reprojection
            # pose[:3,:3] = pose[:3, :3] * -1
            # pose[:3, 0] = pose[:3, 0] * -1
            pose = pose.reshape(-1)
            # get id from object mesh property
            output_list.append(
                {"path": "-/Test.ply", "id": obj.name, "pose": pose.tolist()})

        if output_list:
            print(yaml.dump(output_list, default_flow_style=False))
            with open(self.filepath, 'w') as f:
                yaml.dump(output_list, f, default_flow_style=False)

        return {'FINISHED'}

    def invoke(self, context, event):
        # set filepath with default value of property
        self.filepath = self.filepath
        context.window_manager.fileselect_add(self)
        print(self.filepath)
        return {'RUNNING_MODAL'}


class print_objects(bpy.types.Operator):
    bl_idname = "objects.print"
    bl_label = "Print Object Library"

    def execute(self, context):
        print('Printing v4r_infos')
        global SCENE_FILE_READER

        if SCENE_FILE_READER:
            print("Retrieving Object Library: ")
            OBJECT_LIBRARY = SCENE_FILE_READER.get_object_library()
            for items in OBJECT_LIBRARY.values():
                print(items)
        else:
            print("You need to open the dataset file first.")

        return {'FINISHED'}


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
        id = context.scene.v4r_infos.scene_id

        if(id):
            print("Importing Scene %s" % id)
            # remove cameras
            # get new cameras and images
            # remove objects and poses
            # maybe check if objects are already imported
            # just reset or reload poses
            # get the objects and poses
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

        tag_redraw(context)

        return {'FINISHED'}

    def invoke(self, context, event):
        # set filepath with default value of property
        self.filepath = self.filepath
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class V4R_PT_annotation(bpy.types.Panel):
    bl_label = "V4R Annotation"
    bl_idname = "V4R_PT_annotation"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split=True

        scene = context.scene
        v4r_infos = scene.v4r_infos
    
        flow = layout.grid_flow(row_major=True, columns=0, even_columns=True, even_rows=False, align=True)

        col = flow.column()
        col.prop(v4r_infos, "dataset_file", icon="COLLECTION_NEW")
        col.operator("v4r.load_dataset")

        col.separator()

        col.prop_search(v4r_infos, "scene_id", v4r_infos,
                        "scene_ids", icon="IMAGE_DATA")
        col.operator("v4r.import_scene")

        col.separator()

        col.operator("objects.print")
        col.operator("pose.save")


def register():
    print('registered')
    bpy.utils.register_class(V4R_PG_scene_ids)
    bpy.utils.register_class(V4R_PG_infos)
    bpy.utils.register_class(V4R_PT_annotation)
    bpy.utils.register_class(V4R_OT_load_dataset)
    bpy.utils.register_class(V4R_OT_import_scene)

    bpy.utils.register_class(save_pose)
    bpy.utils.register_class(load_pose)
    bpy.utils.register_class(print_objects)

    bpy.types.Scene.v4r_infos = bpy.props.PointerProperty(type=V4R_PG_infos)


def unregister():
    bpy.utils.unregister_class(V4R_PG_scene_ids)
    bpy.utils.unregister_class(V4R_PG_infos)
    bpy.utils.unregister_class(V4R_PT_annotation)
    bpy.utils.unregister_class(V4R_OT_load_dataset)
    bpy.utils.unregister_class(V4R_OT_import_scene)

    bpy.utils.unregister_class(save_pose)
    bpy.utils.unregister_class(load_pose)
    bpy.utils.unregister_class(print_objects)

    del bpy.types.Scene.v4r_infos

# if __name__ == "__main__":
#    register()
