import glob
import open3d as o3d
import os
import numpy as np

from v4r_dataset_toolkit.objects import ObjectLibrary
from v4r_dataset_toolkit.meshreader import MeshReader


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
            f'reconstruction_dir: {self.reconstruction_dir}'

    def readScenes():
        pass

    def readCameraInfo():
        pass

    def readObjectLibrary():
        pass

    def readPose():
        pass
