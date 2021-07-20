import open3d as o3d
import os
import numpy as np
import yaml

from .objects import ObjectLibrary
from .meshreader import MeshReader


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

    # from list tx,ty,tz,rw,rx,ry,rz
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

# Need to get pose array for camera(s)


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

# Need to get pose for annotated objects


class CameraInfo:
    def __init__(self, name=None, width=None, height=None,
                 fx=None, fy=None, cx=None, cy=None,
                 sensor_width_mm=None):
        self.name = name
        self.width = width
        self.height = height
        self.fx = fx
        self.fy = fy
        self.cx = cx
        self.cy = cy
        self.sensor_width_mm = sensor_width_mm

    def __str__(self):
        return f'name: {self.name}\n' \
            f'width : {self.width}\n' \
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
        # TODO: Either create the blender camera here and import bpy
        #       or have a blender class which does it and takes this here as input
        #       or call the blender class here and return it
        #       Needs to check if blender is actual available
        pass

    @classmethod
    def create(cls, file):
        # Read width, height and intrinsics from yaml file
        with open(file, 'r') as fp:
            cam = yaml.load(fp, Loader=yaml.FullLoader)
            return cls(cam.get('name'),
                       cam.get('image_width'),
                       cam.get('image_height'),
                       cam.get('camera_matrix')[0],
                       cam.get('camera_matrix')[4],
                       cam.get('camera_matrix')[2],
                       cam.get('camera_matrix')[5],
                       cam.get('sensor_width_mm'))
        return None


class CameraTrajectory:
    def __init__(self, camera_info, poses=[]):
        self.camera_info = camera_info
        self.poses = poses

    @classmethod
    def create(cls, camera_file, pose_file):
        # Read camera params
        self.camera_info = CameraInfo.create(camera_file)
        # Read poses saved as quaternions and save as np.array 3x3


class Scene:
    def __init__(self, scene_id=None, rgb=None, depth=None, cameras=None, objects=None, markers=None, reconstruction_file=None):
        self.scene_id = scene_id
        self.rgb_files = rgb_files or []  # o3d image
        self.depth_files = depth_files or []  # o3d image
        self.cameras = cameras or []  # o3d camera trajectory
        # TODO: objects/object id with numpy 4x4 array (saved as quaternion)
        self.objects = objects or []
        self.markers = markers or []  # numpy 4x4 array (saved as quaternion)
        self.reconstruction = MeshReader(mesh_file)


class SceneFileReader:
    def __init__(self, config):
        self.root_dir = config.get('root_dir')
        self.scenes_dir = config.get('scenes_dir')
        self.rgb_dir = config.get('rgb_dir')
        self.depth_dir = config.get('depth_dir')
        self.camera_pose_file = config.get('camera_pose_file')
        self.camera_intrinsics_file = config.get('camera_intrinsics_file')
        self.object_library_file = config.get('object_library_file')
        self.associations_file = config.get('associations_file')
        # How to separate recordings from annotations?
        self.object_pose_file = config.get('object_pose_file')
        self.reconstruction_file = config.get('reconstruction_file')
        self.mask_dir = config.get('mask_dir')

    def __str__(self):
        return f'root_dir: {self.root_dir}\n'\
            f'scenes_dir: {self.scenes_dir}\n'\
            f'rgb_dir: {self.rgb_dir}\n'\
            f'depth_dir: {self.depth_dir}\n'\
            f'camera_pose_file: {self.camera_pose_file}\n'\
            f'camera_intrinsics_file: {self.camera_intrinsics_file}\n'\
            f'object_library_file: {self.object_library_file}\n'\
            f'associations_file: {self.associations_file}\n'\
            f'object_pose_file: {self.object_pose_file}\n'\
            f'reconstruction_file: {self.reconstruction_file}\n'\
            f'mask_dir: {self.mask_dir}'

    def readCameraInfo(self):
        full_path = os.path.join(
            self.root_dir, self.scenes_dir, self.camera_intrinsics_file)
        return CameraInfo.create(full_path)

    def readObjectLibrary(self):
        return ObjectLibrary.create(self.object_library_file)

    def getSceneIds(self):
        full_path = os.path.join(self.root_dir, self.scenes_dir)
        return sorted([f.name for f in os.scandir(full_path) if f.is_dir()])

    def readScene(self, id):
        # check if id is in this datasets scene id list

        # access to specific scene should be a function
        # access to specific rgbs/depths should be loaded on demand
        pass
