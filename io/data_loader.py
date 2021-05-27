import argparse
import pyyaml
import glob


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
    parser.add_argument("-c", "--config", type=str, default="./config/default.yaml",
                        help="Path to dataset information")
    args = parser.parse_args()


if __name__ == "__main__":
    main()
