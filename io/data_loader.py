import argparse
import configargparse
import yaml
import glob
import open3d as o3d
import os
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


class ObjectLibrary(UserDict):
    @classmethod
    def create(cls, path):
        with open(path) as fp:
            root, _ = os.path.split(path)
            object_dict = cls()
            for obj in yaml.load(fp, Loader=yaml.FullLoader):
                object_dict[obj['id']] = Object(id=obj['id'],
                                         name=obj['name'],
                                         class_id=obj['class'],
                                         description=obj['description'],
                                         color=obj['color'],
                                         mesh_file=os.path.join(root, obj['mesh']))
            return object_dict

    def as_list(self, ids=None):
        return list(map(self.__getitem__, ids or [])) or list(self.values())


class DataLoader:
    def __init__(self, root_dir=None, camera_file=None, scene_dirs=None,
                 rgb_files=None, depth_files=None, camera_poses_files=None,
                 associations_file=None, object_poses_files=None):
        self.root_dir = root_dir
        self.scene_dirs = scene_dirs or []
        self.rgb_files = rgb_files or []
        self.depth_files = depth_files or []
        self.camera_poses_files = camera_poses_files or []
        self.object_poses_files = object_poses_files or []
        self.camera_file = camera_file
        self.associations_file = associations_file
        # reference to ObjectLib ???


def main():
    # run data loader with command line parameters
    parser = argparse.ArgumentParser(
        "Example: loading dataset items.")
    parser.add_argument("-c", "--config", type=str, default="../objects/objects.yaml",
                        help="Path to dataset information")
    args = parser.parse_args()
    print(args.config)
    object_lib = ObjectLibrary.create(args.config)

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
    #filter by class
    for obj in [val for val in object_lib.values() if val.class_id in ['tool']]:
        print(obj)


if __name__ == "__main__":
    main()
