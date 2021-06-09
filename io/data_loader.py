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
        self.mesh = MeshReader(mesh_file)
        self.color = color

    def __str__(self):
        return f'id: {self.id}\n' \
            f'name: {self.name}\n' \
            f'class: {self.class_id}\n' \
            f'description: {self.description}\n' \
            f'color: {self.color}\n' \
            f'mesh file: {self.mesh.file}'


class ObjectPose():
    def __init__(self, object=None, pose=np.eye(4)):
        self.object = object
        self.pose = pose


class ObjectLibrary(UserDict):
    @classmethod
    def create(cls, path):
        with open(path) as fp:
            root, _ = os.path.split(path)
            object_dict = cls()
            for obj in yaml.load(fp, Loader=yaml.FullLoader):
                object_dict[obj['id']] = Object(id=obj['id'],
                                                name=obj.get('name'),
                                                class_id=obj.get('class'),
                                                description=obj.get(
                                                    'description'),
                                                color=obj.get('color'),
                                                mesh_file=os.path.join(root, obj['mesh']))
            return object_dict

    def as_list(self, ids=None):
        return list(map(self.__getitem__, ids or [])) or list(self.values())


class Scene:
    def __init__(self, scene_id=None, rgb=None, depth=None, cameras=None, objects=None, markers=None, mesh_file=None):
        self.scene_id = scene_id
        self.rgb_files = rgb_files or []  # o3d image
        self.depth_files = depth_files or []  # o3d image
        self.cameras = cameras or []  # o3d camera trajectory
        # TODO: objects/object id with numpy 4x4 array (saved as quaternion)
        self.objects = objects or []
        self.markers = markers or []  # numpy 4x4 array (saved as quaternion)
        self.mesh = MeshReader(mesh_file)

# poses from groundtruth text file, each line
# groundtruth/ros/scipy:   tx, ty, tz, rx, ry, rz, rw
# ->
# to open3d/blender/Eigen: tx, ty, tz, rw, rx, ry, rz
# poses from objects pose yaml file
# translation(tx,ty,tz) & rotation(rx, ry, rz, rw)
# get rotation as quaternion (x, y, z, w) or (w, x, y, z)
# get rotation as 3x3 numpy array
# get translation as 3x1 numpy array
# get transformation matrix as 4x4 numpy array


class Pose:
    def __init__(self, values=None):
        if type(values) == list:
            self.set_list(values)
        elif type(values) == np.ndarray:
            self.set_numpy4x4(values)
        elif values == None:
            self.tf = np.eye(4)
        else:
            raise ValueError("Pose unsupported type.")

    def set_list(self, tf):
        if(len(tf) == 7):
            self.tf = np.zeros((4, 4))
            self.tf[3, 3] = 1
            self.tf[:3, -1] = tf[0:3]
            self.tf[:3, :3] = o3d.geometry.get_rotation_matrix_from_quaternion(
                tf[3:])
        else:
            raise ValueError("Pose unsupported type.")

    def set_numpy4x4(self, tf):
        if(np.shape(tf) == (4, 4)):
            self.tf = tf
        else:
            raise ValueError("Pose unsupported type.")

    def __str__(self):
        return self.tf.__str__()


def get_poses(path_groundtruth):
    with open(path_groundtruth) as fp:
        groundtruth = fp.readlines()
    groundtruth = [line.strip().split() for line in groundtruth]

    trans = [line[1:4] for line in groundtruth]
    quat = [line[4:] for line in groundtruth]

    poses = []
    for i in range(len(groundtruth)):
        pose = np.zeros((4, 4))
        pose[3, 3] = 1
        # quaternions groundtruth -> open3d (same as Eigen): xyzw -> wxyz
        rot = np.array([quat[i][3], quat[i][0], quat[i][1], quat[i][2]])
        pose[:3, :3] = o3d.geometry.get_rotation_matrix_from_quaternion(rot)
        pose[:3, -1] = trans[i]
        poses.append(pose)

    return poses


class CameraIntrinsic:
    def __init__(self, w, h, fx, fy, cx, cy, sensor_width_mm):
        self.width = w
        self.height = h
        self.fx = fx
        self.fy = fy
        self.cx = cx
        self.cy = cy
        self.sensor_width_mm = sensor_width_mm

    def __str__(self):
        return f'width : {self.width}\n' \
            f'height: {self.height}\n' \
            f'fx: {self.fx}\n' \
            f'fy: {self.fy}\n' \
            f'cx: {self.cx}\n' \
            f'cy: {self.cy}\n' \
            f'sensor_width_mm: {self.sensor_width_mm}'

    def as_o3d(self):
        return o3d.camera.PinholeCameraIntrinsic(self.width, self.height, self.fx, self.fy, self.cx, self.cy)

    def as_numpy3x3(self):
        return np.array([[self.fx, 0, self.cx], [0, self.fy, self.cy], [0, 0, 1]])

    def as_blender(self):
        pass

    @classmethod
    def create(cls, file):
        # Read widht, height and intrinsics from yaml file
        pass


class CameraTrajectory:
    def __init__(self, camera_intrinsics, poses=[]):
        self.camera_intrinsics = camera_intrinsics
        self.poses = poses

    @classmethod
    def create(cls, camera_file, pose_file):
        # Read camera params
        self.camera_intrinsics = CameraIntrinsic.create(camera_file)
        # Read poses saved as quaternions and save as np.array 3x3


class MeshReader:
    def __init__(self, file):
        self.file = file

    def as_o3d(self):
        return o3d.io.read_triangle_mesh(self.file)

    def as_trimesh(self):
        return trimesh.load_mesh(self.file)

    def as_blender(self):
        # import bpy
        # load the file depending pn extension ply obj something else?
        # set some attributes depending on name / id?
        pass


class SceneFileReader:
    def __init__(self, root_dir, config):
        self.root_dir = root_dir
        self.scenes_dir = config.get('scenes_dir')
        self.rgb_dir = config.get('rgb_dir')
        self.depth_dir = config.get('depth_dir')
        self.camera_pose_file = config.get('camera_pose_file')
        self.camera_intrinsics_file = config.get('camera_intrinsics_file')
        self.object_pose_file = config.get('object_pose_file')
        self.object_library_file = config.get('object_library_file')
        self.associations_file = config.get('associations_file')
        self.reconstruction_dir = config.get('reconstruction_dir')

    def __str__(self):
        return f'root_dir: {self.root_dir}\n'\
            f'scenes_dir: {self.scenes_dir}\n'\
            f'rgb_dir: {self.rgb_dir}\n'\
            f'depth_dir: {self.depth_dir}\n'\
            f'camera_pose_file: {self.camera_pose_file}\n'\
            f'camera_intrinsics_file: {self.camera_intrinsics_file}\n'\
            f'object_pose_file: {self.object_pose_file}\n'\
            f'object_library_file: {self.object_library_file}\n'\
            f'associations_file: {self.associations_file}\n'\
            f'reconstruction_dir: {self.reconstruction_dir}\n'

    def readScenes():
        pass

    def readCameraInfo():
        pass

    def readObjectLibrary():
        pass

    def readPose():
        pass


def main():
    # run data loader with command line parameters
    parser = argparse.ArgumentParser(
        "Example: loading dataset items.")
    parser.add_argument("-c", "--config", type=str, default="../objects/objects.yaml",
                        help="Path to dataset information")
    args = parser.parse_args()

    # Test Scene File Loader
    cfg = configparser.ConfigParser()
    cfg.read(args.config)
    reader = SceneFileReader('/temp', cfg['General'])
    object_lib = ObjectLibrary.create(reader.object_library_file)

    # Test Object Library
    # single object access
    print("--- Single access.")
    obj = object_lib[1]
    print(obj)
    # list object access
    print("--- Multi access with indices.")
    for obj in object_lib.as_list([1, 2]):
        print(obj.id, obj.name, obj.mesh.file)
    print("--- Multi access without indices.")
    for obj in object_lib.as_list():
        print(obj.id, obj.name, obj.mesh.file)
    print("--- Filter by class.")
    # filter by class
    for obj in [val for val in object_lib.values() if val.class_id in ['bottle']]:
        print(obj.id, obj.name, obj.class_id)
    # testing SceneFileReader
    print("--- SceneFileReader.")
    print(reader)

    cam = CameraIntrinsic(1, 2, 3, 4, 5, 6, 100)
    print(cam)
    print(cam.as_numpy3x3())
    print(np.shape(cam.as_numpy3x3()))
    print(cam.sensor_width_mm)
    p1 = Pose(np.array(np.eye(4)))
    p2 = Pose([0, 0, 0, 1, 0, 0, 0])
    p3 = Pose()
    print(f'p1:\n{p1}\np2:\n{p2}\np3:\n{p3}\n')


if __name__ == "__main__":
    main()
