import argparse
import yaml
import glob

from collections import UserDict
import itertools


class ObjectLibrary(UserDict):
    """
    Contains a library of ObjectType objects and adds some convenience methods to it.
    Acts like a regular python dict.
    """

    def yell(self):
        print( [self[key] for key in self.data.keys()])

    @classmethod
    def create(cls, path):
      with open(path) as fp:
        return cls(yaml.load(fp, Loader=yaml.FullLoader))

    def filter(self, ids):
        return list(map(self.get, ids))

class DataLoader:
    def __init__(self, root_dir=None, camera_file=None, scene_dirs=None, rgb_files=None, depth_files=None,
                 camera_poses_files=None, associations_file=None, object_poses_files=None):
        self.root_dir = root_dir
        self.scene_dirs = scene_dirs or []
        self.camera_file = camera_file
        self.rgb_files = rgb_files or []
        self.depth_files = depth_files or []
        self.camera_poses_files = camera_poses_files or []
        self.associations_file = associations_file
        self.object_poses_files = object_poses_files or []


def main():
    # run data loader with command line parameters
    parser = argparse.ArgumentParser(
        "Example: loading dataset items.")
    parser.add_argument("-c", "--config", type=str, default="../objects/objects.yaml",
                        help="Path to dataset information")
    args = parser.parse_args()
    print(args.config)
    object_lib = ObjectLibrary.create(args.config)
    print([(id, data["name"]) for id, data in object_lib.items()])
    print(object_lib.filter([1,2]))
    print(object_lib.get(0))

if __name__ == "__main__":
    main()
