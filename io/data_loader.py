import argparse
import yaml
import glob
import open3d as o3d

from collections import UserDict
import itertools


class Object:
    def __init__(self, id=None, name=None, class_id=None, description=None, mesh_file=None):
        self.id = id
        self.name = name
        self.class_id = class_id
        self.description = description
        self.mesh_file = mesh_file

    def get_mesh():
        return o3d.io.read_triangle_mesh(mesh_file)

    def get_mesh_blender():
        # import bpy
        # load the file depending pn extension ply obj something else?
        # set some attributes depending on name / id?
        pass


class ObjectLibrary(UserDict):
    """
    Contains a library of ObjectType objects and adds some convenience methods to it.
    Acts like a regular python dict.
    """

    @classmethod
    def create(cls, path):
        with open(path) as fp:
            return cls(yaml.load(fp, Loader=yaml.FullLoader))

    def get_object(self, id):
        obj = self.get(id)
        return Object(id=id,
                      name=obj['name'],
                      class_id=obj['class'],
                      description=obj['description'],
                      mesh_file=obj['mesh'])

    def get_objects(self, ids):
            return list(map(self.get_object, ids))

class DataLoader:
    def __init__(self, root_dir=None, camera_file=None, scene_dirs=None,
                 rgb_files=None, depth_files=None, camera_poses_files=None, 
                 associations_file=None, object_poses_files=None):
        self.root_dir= root_dir
        self.scene_dirs= scene_dirs or []
        self.rgb_files= rgb_files or []
        self.depth_files= depth_files or []
        self.camera_poses_files= camera_poses_files or []
        self.object_poses_files= object_poses_files or []
        self.camera_file= camera_file
        self.associations_file= associations_file
        # reference to ObjectLib ???


def main():
    # run data loader with command line parameters
    parser= argparse.ArgumentParser(
        "Example: loading dataset items.")
    parser.add_argument("-c", "--config", type=str, default="../objects/objects.yaml",
                        help="Path to dataset information")
    args= parser.parse_args()
    print(args.config)
    object_lib= ObjectLibrary.create(args.config)

    # single object access
    obj = object_lib.get_object(1)
    print(obj.id, obj.name, obj.mesh_file)

    # list object access
    for obj in object_lib.get_objects([2, 3]):
        print(obj.id, obj.name, obj.mesh_file)


if __name__ == "__main__":
    main()
