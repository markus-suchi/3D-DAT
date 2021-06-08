import argparse
import configparser
import yaml
import glob
import open3d as o3d
import os
import numpy as np
import trimesh

from collections import UserDict
import itertools


class Object:
    def __init__(self, id=None, name=None, class_id=None, description=None, mesh_file=None, color=[0, 0, 0]):
        self.id = id
        self.name = name
        self.class_id = class_id
        self.description = description
        self.mesh_file = mesh_file
        self.color = color

    def __str__(self):
        return f'object id: {self.id}\n' \
               f'object name: {self.name}\n' \
               f'object class: {self.class_id}\n' \
               f'object description: {self.description}\n' \
               f'object color: {self.color}\n' \
               f'object mesh file: {self.mesh_file}'

    def load_mesh_o3d(self):
        return o3d.io.read_triangle_mesh(self.mesh_file)

    def load_mesh_trimesh(self):
        return trimesh.load_mesh(self.mesh_file)

    def load_mesh_blender(self):
        # import bpy
        # load the file depending pn extension ply obj something else?
        # set some attributes depending on name / id?
        pass


class ObjectPose():
    def __init__(self, object=None, pose=np.eye(4)):
        self.object = object
        self.pose = pose


class ObjectLibrary(UserDict):
    @classmethod
    def create(cls, path):
        with open(path) as fp:
            root, _=os.path.split(path)
            object_dict=cls()
            for obj in yaml.load(fp, Loader=yaml.FullLoader):
                object_dict[obj['id']] = Object(id=obj['id'],
                                         name=obj.get('name'),
                                         class_id=obj.get('class'),
                                         description=obj.get('description'),
                                         color=obj.get('color'),
                                         mesh_file=os.path.join(root, obj['mesh']))
            return object_dict

    def as_list(self, ids=None):
        return list(map(self.__getitem__, ids or [])) or list(self.values())


class Scene:
    def __init__(self, scene_id=None, rgb=None, depth=None, cameras=None, objects=None, markers=None):
        self.scene_id = scene_id
        self.rgb_files = rgb_files or [] # o3d image
        self.depth_files = depth_files or [] # o3d image
        self.cameras = cameras or [] # o3d camera trajectory
        self.objects = objects or [] # either objects/object id with numpy 4x4 array (saved as quaternion)
        self.markers = markers or [] # numpy 4x4 array (saved as quaternion)


class SceneFileReader:
    def __init__(self, root_dir, config):
        self.root_dir = root_dir
        self.scenes_dir = config.get('scenes_dir')
        self.rgb_dir = config.get('rgb_dir')
        self.depth_dir = config.get('depth_dir')
        self.camera_pose_file = config.get('camera_pose_file')
        self.camera_intrinsics_file = config.get('camera_intrinsics_file')
        self.object_pose_file = config.get('object_pose_file')
        self.object_library_file =config.get('object_library_file')
        self.associations_file = config.get('associations_file')

    def __str__(self):
        return f'root_dir: {self.root_dir}\n'\
               f'scenes_dir: {self.scenes_dir}\n'\
               f'rgb_dir: {self.rgb_dir}\n'\
               f'depth_dir: {self.depth_dir}\n'\
               f'camera_pose_file: {self.camera_pose_file}\n'\
               f'camera_intrinsics_file: {self.camera_intrinsics_file}\n'\
               f'object_pose_file: {self.object_pose_file}\n'\
               f'object_library_file: {self.object_library_file}\n'\
               f'associations_file: {self.associations_file}\n'

    def readScenes():
        pass

    def readCameraInfo():
        pass

    def readObjectLibrary():
        pass

    def loadPose():
        pass



def main():
    # run data loader with command line parameters
    parser = argparse.ArgumentParser(
        "Example: loading dataset items.")
    parser.add_argument("-c", "--config", type=str, default="../objects/objects.yaml",
                        help="Path to dataset information")
    args = parser.parse_args()

    #Test Scene File Loader
    cfg = configparser.ConfigParser()
    cfg.read(args.config)
    reader = SceneFileReader('/temp', cfg['General'])
    object_lib = ObjectLibrary.create(reader.object_library_file)

    #Test Object Library
    # single object access
    print("--- Single access.")
    obj = object_lib[1]
    print(obj)
    # list object access
    print("--- Multi access with indices.")
    for obj in object_lib.as_list([2, 3]):
        print(obj.id, obj.name, obj.mesh_file)
    print("--- Multi access without indices.")
    for obj in object_lib.as_list():
        print(obj.id, obj.name, obj.mesh_file)
    print("--- Filter by class.")
    # filter by class
    for obj in [val for val in object_lib.values() if val.class_id in ['bottle']]:
        print(obj.id, obj.name, obj.class_id)

    # testing SceneFileReader
    print("--- SceneFileReader.")
    print(reader)

if __name__ == "__main__":
    main()
