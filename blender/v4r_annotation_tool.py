import os
import sys
import numpy as np
from numpy.linalg import inv
import yaml
import bpy

from . import v4r_dataset_toolkit as v4r

OBJECT_LIBRARY = None


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
            #pose[:3,:3] = pose[:3, :3] * -1
            #pose[:3, 0] = pose[:3, 0] * -1
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
            #pose[:3,:3] = pose[:3, :3] * -1
            #pose[:3, 0] = pose[:3, 0] * -1
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


class load_object_library(bpy.types.Operator):
    bl_idname = "object.load"
    bl_label = "Load Object Library"
    filepath: bpy.props.StringProperty(subtype="FILE_PATH", default="*.yaml")
    loaded: bpy.props.BoolProperty(name="loaded", default=False)

    def execute(self, context):
        global OBJECT_LIBRARY
        print("Opening Object Library: " + self.filepath)
        OBJECT_LIBRARY = v4r.objects.ObjectLibrary.create(self.filepath)
        for items in OBJECT_LIBRARY.values():
            print(items)
        return {'FINISHED'}

    def invoke(self, context, event):
        # set filepath with default value of property
        self.filepath = self.filepath
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class PoseAnnotationPanel(bpy.types.Panel):
    bl_label = "Pose Annotation"
    bl_idname = "3D_VIEW_PT_annotation"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "scene"

    def draw(self, context):
        layout = self.layout
        row=layout.row()
        row.alignment = 'LEFT'
        row.operator("object.load")
        row = layout.row()
        row.alignment = 'LEFT'
        row.operator("pose.save")


def register():
    bpy.utils.register_class(save_pose)
    bpy.utils.register_class(load_pose)
    bpy.utils.register_class(load_object_library)
    bpy.utils.register_class(PoseAnnotationPanel)


def unregister():
    bpy.utils.unregister_class(save_pose)
    bpy.utils.unregister_class(load_pose)
    bpy.utils.unregister_class(load_object_library)
    bpy.utils.unregister_class(PoseAnnotationPanel)

# if __name__ == "__main__":
#    register()
