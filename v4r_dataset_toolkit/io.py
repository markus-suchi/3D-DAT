import open3d as o3d
import os
import numpy as np
import yaml
import glob
import configparser
import math
import errno

from .objects import ObjectLibrary
from .meshreader import MeshReader

# There are 3 different entities which require poses
# 1. Cameras: Camerinfo + Pose vector
# 2. Object: ObjectId + Pose
# 3. Marker: MarkerId/Name + Pose vector
# If Camera is not registered, the camera pose can be retrieved by the inverse of the marker pose
# Markers can also be used to retrieve reference point in world coordinates
# a) groundtruth_handeye.txt has all the poses for regeistered cameras with
# the base of the arm as the origin.
# b) groundtruth.txt marker on markersheet with rgb camera frame as the origin.
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


def get_file_list(path, extensions):
    file_list = []
    for root, dirs, files in os.walk(path):
        for filename in files:
            if any(filename.endswith(extension) for extension in extensions):
                filepath = os.path.join(root, filename)
                file_list.append(filepath)

    return file_list


class Pose:
    def __init__(self, values=None, wxyz=True):
        if type(values) == list:
            if wxyz:
                self.set(values)
            else:
                self.set_txyzw(values)
        elif type(values) == np.ndarray:
            self.set_numpy4x4(values)
        elif values == None:
            self.tf = np.eye(4)
        else:
            raise ValueError("Pose unsupported type.")

    # from list tx,ty,tz,rw,rx,ry,rz
    def set(self, tf):
        if(len(tf) == 7):
            self.tf = np.zeros((4, 4))
            self.tf[3, 3] = 1
            self.tf[:3, -1] = tf[0:3]
            self.tf[:3, :3] = o3d.geometry.get_rotation_matrix_from_quaternion(
                tf[3:])
        else:
            raise ValueError("Pose unsupported type.")

    # from list tx,ty,tz,rx,ry,rz,rw
    def set_txyzw(self, tf):
        if(len(tf) == 7):
            self.tf = np.zeros((4, 4))
            self.tf[3, 3] = 1
            self.tf[:3, -1] = tf[0:3]
            self.tf[:3, :3] = o3d.geometry.get_rotation_matrix_from_quaternion(
                np.array([tf[6], tf[3], tf[4], tf[5]]))
        else:
            raise ValueError("Pose unsupported type.")

    def set_numpy4x4(self, tf):
        if(np.shape(tf) == (4, 4)):
            self.tf = tf
        else:
            raise ValueError("Pose unsupported type.")

    def rotation(self):
        return self.tf[:3, :3]

    def translation(self):
        return self.tf[:3, -1]

    def __str__(self):
        return self.tf.__str__()


class CameraInfo:
    def __init__(self, name=None, width=None, height=None,
                 fx=None, fy=None, cx=None, cy=None,
                 sensor_width=None):
        self.name = name
        self.width = width
        self.height = height
        self.fx = fx
        self.fy = fy
        self.cx = cx
        self.cy = cy
        self.sensor_width = sensor_width

    def __str__(self):
        return f'name: {self.name}\n' \
            f'width : {self.width}\n' \
            f'height: {self.height}\n' \
            f'fx: {self.fx}\n' \
            f'fy: {self.fy}\n' \
            f'cx: {self.cx}\n' \
            f'cy: {self.cy}\n' \
            f'sensor_width: {self.sensor_width}'

    def as_o3d(self):
        return o3d.camera.PinholeCameraIntrinsic(self.width, self.height, self.fx, self.fy, self.cx, self.cy)

    def as_numpy3x3(self):
        return np.array([[self.fx, 0, self.cx], [0, self.fy, self.cy], [0, 0, 1]])

    def lens(self):
        if self.sensor_width:
            lens = self.fx * self.sensor_width / self.width
        else:
            lens = None

        return lens

    def shift_x(self):
        return -(self.cx / self.width - 0.5)

    def shift_y(self):
        return (self.cy - 0.5 * self.height) / self.width

    def fov(self):
        return 2 * math.atan(self.width / (2 * self.fx))

    @classmethod
    def create(cls, file):
        # Read width, height and intrinsics from yaml file
        with open(file, 'r') as fp:
            cam = yaml.load(fp, Loader=yaml.FullLoader)
            return cls(name=cam.get('name'),
                       width=cam.get('image_width'),
                       height=cam.get('image_height'),
                       fx=cam.get('camera_matrix')[0],
                       fy=cam.get('camera_matrix')[4],
                       cx=cam.get('camera_matrix')[2],
                       cy=cam.get('camera_matrix')[5],
                       sensor_width=cam.get('sensor_width'))
        return None


class CameraTrajectory:
    def __init__(self, camera_info, poses=[]):
        self.camera_info = camera_info
        self.poses = poses

    @classmethod
    def create(cls, camera_file, pose_file):
        # Read camera params.
        # TODO: Think of nested settings: global or per scene camera intrinsics
        self.camera_info = CameraInfo.create(camera_file)
        # Read poses, now they are different than object poses
        # camera: plane text, id, quaternion   object: yaml file id, 4x4 matrix


class ObjectPose:
    def __init__(self, id, pose=np.eye(4)):
        self.id = id             # id of object in objectlibrary
        self.pose = pose         # pose of the object


class Scene:
    def __init__(self, scene_id=None, rgb=None, depth=None, cameras=None, objects=None, markers=None, reconstruction_file=None):
        self.scene_id = scene_id
        self.rgb_files = rgb_files or []  # o3d image
        self.depth_files = depth_files or []  # o3d image
        self.cameras = cameras or []  # o3d camera trajectory
        # objects/object id with numpy 4x4 array (saved as quaternion)
        self.objects = objects or []
        # numpy 4x4 array (saved as quaternion), can there be several markers? Only use this if no cameras?
        self.markers = markers or []
        self.reconstruction = MeshReader(
            reconstruction_file) if reconstruction_file else None


class SceneFileReader:
    def __init__(self, config):
        self.root_dir = config.get('root_dir')
        self.scenes_dir = config.get('scenes_dir')
        self.rgb_dir = config.get('rgb_dir')
        self.depth_dir = config.get('depth_dir')
        self.camera_pose_file = config.get('camera_pose_file')
        self.camera_intrinsics_file = config.get('camera_intrinsics_file')
        self.object_library_file = config.get('object_library_file')
        # The associations file is a list of corresponding depth and rgb images
        # It is used for standalone script to create reconsturctions
        # TODO: re-evaluate if this is still needed after io is complete
        self.associations_file = config.get('associations_file')
        # How to separate recordings from annotations?
        self.object_pose_file = config.get('object_pose_file')
        self.reconstruction_file = config.get('reconstruction_file')
        self.mask_dir = config.get('mask_dir')
        self.scene_ids = self.get_scene_ids()
        self.object_library = self.get_object_library()
        self.annotation_dir = config.get('annotation_dir')
        self.object_scale = config.get('object_scale')
        if not self.object_scale:
            self.object_scale = 1

    @classmethod
    def create(cls, config_file):
        if(os.path.exists(config_file)):
            cfg = configparser.ConfigParser()
            # Check if file exists
            cfg.read(config_file)
            return SceneFileReader(cfg['General'])
        else:
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), config_file)

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
            f'annotation_dir: {self.annotation_dir}\n'\
            f'mask_dir: {self.mask_dir}'

    # def get_camera_info(self):
        # full_path = os.path.join(
            # self.root_dir, self.scenes_dir, self.camera_intrinsics_file)
        # return CameraInfo.create(full_path)

    def get_camera_info_scene(self, id):
        full_path = os.path.join(
            self.root_dir, self.scenes_dir, self.camera_intrinsics_file)

        full_path_scene_cam = os.path.join(
            self.root_dir, self.scenes_dir, id, self.camera_intrinsics_file)

        if os.path.exists(full_path_scene_cam):
            return CameraInfo.create(full_path_scene_cam)
        elif os.path.exists(full_path):
            return CameraInfo.create(full_path)
        else:
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), full_path)

    def get_object_library(self):
        return ObjectLibrary.create(self.object_library_file)

    def get_scene_ids(self):
        full_path = os.path.join(self.root_dir, self.scenes_dir)
        return sorted([f.name for f in os.scandir(full_path) if f.is_dir()])

    def get_camera_poses(self, id):
        # check if id is in this datasets scene id list
        full_path = os.path.join(
            self.root_dir, self.scenes_dir, id, self.camera_pose_file)
        with open(full_path) as fp:
            pose_lines = fp.readlines()
        # The recorded poses adds line entries -> disregard first entry
        return [Pose(line.strip().split()[1:], wxyz=False) for line in pose_lines]

    def get_images_rgb(self, id):
        files = self.get_images_rgb_path(id)
        return [o3d.io.read_image(file) for file in files]

    def get_images_rgb_path(self, id):
        full_path = os.path.join(
            self.root_dir, self.scenes_dir, id, self.rgb_dir)

        extensions = ('.png', '.jpg')
        files = get_file_list(full_path, extensions)
        files.sort()
        return files

    def get_images_depth(self, id):
        files = self.get_images_depth_path(id)
        return [o3d.io.read_image(file) for file in files]

    def get_images_depth_path(self, id):
        full_path = os.path.join(
            self.root_dir, self.scenes_dir, id, self.depth_dir)

        extensions = ('.png')
        files = get_file_list(full_path, extensions)
        files.sort()
        return files 

    def get_pointclouds(self, id):
        # return rgbd image reader which does not load images right away?
        # at loading it will use camera info, rgb and depth to create the rgbd image
        # with the help of open3d (maybe just the mesh?)
        rgb_images = self.get_images_rgb(id)
        depth_images = self.get_images_depth(id)
        camera_info = self.get_camera_info_scene(id).as_o3d()
        camera_poses = self.get_camera_poses(id)
        pointclouds = []
        for i, camera_pose in enumerate(camera_poses):
            rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
                rgb_images[i], depth_images[i], convert_rgb_to_intensity=False)
            pcd = o3d.geometry.PointCloud.create_from_rgbd_image(
                rgbd_image, camera_info)
            pointclouds.append(pcd.transform(camera_pose.tf))

        return pointclouds

    def get_object_poses(self, id):
        full_path = os.path.join(
            self.root_dir, self.annotation_dir, id, self.object_pose_file)

        objects = []
        with open(full_path) as fp:
            for items in (yaml.load(fp, Loader=yaml.FullLoader)):
                id = items.get("id")
                pose = items.get("pose")
                if not pose:
                    pose = np.eye(4).tolist()
                objects.append([self.object_library[id], pose])
        return objects

    def get_scene(self, id):
        # check if id is in this datasets scene id list
        # access to specific scene should be a function
        # access to specific rgbs/depths should be loaded on demand
        pass

    def create_reconstruction(self, id):
        # create reconstruction.ply file for scene
        pass

    def get_reconstruction(self, id):
        # read reconstruction for scene
        pass
