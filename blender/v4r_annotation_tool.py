import os
import sys
import numpy as np
from numpy.linalg import inv
import yaml
import bpy

from . import v4r_dataset_toolkit as v4r

SCENE_FILE_READER = None
scene_ids = []


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


class load_dataset(bpy.types.Operator):
    bl_idname = "dataset.load"
    bl_label = "Load Dataset Library"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH", default="*.yaml")
    loaded: bpy.props.BoolProperty(name="loaded", default=False)

    def execute(self, context):
        global SCENE_FILE_READER
        global scene_ids

        print("Opening Dataset Library: " + self.filepath)
        SCENE_FILE_READER = v4r.io.SceneFileReader.create(self.filepath)

        # Fill in dropdown box with scene ids
        list_scene_ids = SCENE_FILE_READER.scene_ids
        scene_ids.clear()
        for i, item in enumerate(list_scene_ids):
            scene_ids.append((item, str(item), "", i))

        return {'FINISHED'}

    def invoke(self, context, event):
        # set filepath with default value of property
        self.filepath = self.filepath
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class print_objects(bpy.types.Operator):
    bl_idname = "objects.print"
    bl_label = "Print Object Library"

    def execute(self, context):
        print('Printing v4r_infos')
        test = context.scene.v4r_infos
        print(test)
        print(dir(test))
        print(type(test))
        print('Printing scene_ids')
        test = context.scene.v4r_infos.scene_ids
        print(test)
        print(dir(test))
        print(type(test))
        print('Printing scene_id_update')
        test = context.scene.v4r_infos.scene_id_update
        print(test)
        print(dir(test))
        print(type(test))






        global SCENE_FILE_READER

        if SCENE_FILE_READER:
            print("Retrieving Object Library: ")
            OBJECT_LIBRARY = SCENE_FILE_READER.get_object_library()
            for items in OBJECT_LIBRARY.values():
                print(items)
        else:
            print("You need to open the dataset file first.")

        return {'FINISHED'}

    # def invoke(self, context, event):
        # set filepath with default value of property
     #   print('invoke')
      #  return {'RUNNING_MODAL'}

def update_scene_ids(self, context):
    global scene_ids
    return scene_ids


class PG_v4r_infos(bpy.types.PropertyGroup):
    scene_id_update: bpy.props.BoolProperty()

    scene_ids: bpy.props.EnumProperty(
        name="Scene Id",
        description="Choose scene to load",
        items=update_scene_ids
    )


class PoseAnnotationPanel(bpy.types.Panel):
    bl_label = "Pose Annotation"
    bl_idname = "3D_VIEW_PT_annotation"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        v4r_infos = scene.v4r_infos
        row = layout.row()
        row.alignment = 'LEFT'
        row.operator("dataset.load")
        row.operator("objects.print")
        row.operator("pose.save")
        row = layout.row()
        row.alignment = 'LEFT'
        row.prop(v4r_infos, "scene_ids")

def register():
    print('registered')
    bpy.utils.register_class(PG_v4r_infos)
    bpy.utils.register_class(save_pose)
    bpy.utils.register_class(load_pose)
    bpy.utils.register_class(load_dataset)
    bpy.utils.register_class(print_objects)
    bpy.utils.register_class(PoseAnnotationPanel)

    bpy.types.Scene.v4r_infos = bpy.props.PointerProperty(type=PG_v4r_infos)


def unregister():
    bpy.utils.unregister_class(PG_v4r_infos)
    bpy.utils.unregister_class(save_pose)
    bpy.utils.unregister_class(load_pose)
    bpy.utils.unregister_class(load_dataset)
    bpy.utils.unregister_class(print_objects)
    bpy.utils.unregister_class(PoseAnnotationPanel)

    del bpy.types.Scene.v4r_infos

# if __name__ == "__main__":
#    register()
