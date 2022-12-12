import open3d as o3d
import os
import numpy as np
import yaml
import glob
import math
import errno

from .objects import ObjectLibrary
from .meshreader import MeshReader


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
    def __init__(self, scene_id, pose=np.eye(4)):
        self.id = scene_id             # id of object in objectlibrary
        self.pose = pose         # pose of the object


class Scene:
    def __init__(self, scene_id=None, rgb=None, depth=None, cameras=None, objects=None, reconstruction_file=None):
        self.scene_id = scene_id
        self.rgb_files = rgb_files or []  # o3d image
        self.depth_files = depth_files or []  # o3d image
        self.cameras = cameras or []  # o3d camera trajectory
        # objects/object id with numpy 4x4 array (saved as quaternion)
        self.objects = objects or []
        self.reconstruction = MeshReader(
            reconstruction_file) if reconstruction_file else None


class SceneFileReader:
    def __init__(self, config):
        self.root_dir = config.get('root_dir')
        self.scenes_dir = config.get('scenes_dir','scenes')
        self.rgb_dir = config.get('rgb_dir','rgb')
        self.depth_dir = config.get('depth_dir','depth')
        self.camera_pose_file = config.get('camera_pose_file')
        self.camera_intrinsics_file = config.get('camera_intrinsics_file')
        self.object_library_file = config.get('object_library_file')
        self.object_pose_file = config.get('object_pose_file','poses.yaml')
        self.reconstruction_dir = config.get('reconstruction_dir')
        self.reconstruction_file = 'reconstruction.ply'
        self.reconstruction_visual_file = 'reconstruction_visual.ply'
        self.reconstruction_align_file = 'reconstruction_align.ply'
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
            with open(config_file, 'r') as fp:
                cfg = yaml.load(fp, Loader=yaml.FullLoader)
                # check if we have general settings
                if not cfg.get('General'):
                    return None

                if not cfg.get('General').get('root_dir'):
                    cfg['General']['root_dir']=os.path.dirname(os.path.abspath(config_file))

                reconstruction_dir =  cfg.get('General').get('reconstruction_dir') or "reconstructions"
                if not os.path.isabs(reconstruction_dir):
                    cfg['General']['reconstruction_dir']=os.path.join(cfg['General']['root_dir'],reconstruction_dir)
                else:
                    cfg['General']['reconstruction_dir']=reconstruction_dir

                annotation_dir =  cfg.get('General').get('annotation_dir') or "annotations"
                if not os.path.isabs(annotation_dir):
                    cfg['General']['annotation_dir']=os.path.join(cfg['General']['root_dir'],annotation_dir)
                else:
                    cfg['General']['annotation_dir']=annotation_dir

                object_library_file =  cfg.get('General').get('object_library_file') or "objects/objects.yaml"
                if not os.path.isabs(object_library_file):
                    cfg['General']['object_library_file']=os.path.join(cfg['General']['root_dir'],object_library_file)
                else:
                    cfg['General']['object_library_file']=object_library_file

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
            f'object_pose_file: {self.object_pose_file}\n'\
            f'reconstruction_dir: {self.reconstruction_dir}\n'\
            f'reconstruction_file: {self.reconstruction_file}\n'\
            f'reconstruction_visual_file: {self.reconstruction_visual_file}\n'\
            f'reconstruction_align_file: {self.reconstruction_align_file}\n'\
            f'annotation_dir: {self.annotation_dir}\n'\
            f'mask_dir: {self.mask_dir}'


    def get_camera_info_scene_path(self, scene_id):
        full_path_scene_cam = os.path.join(
            self.root_dir, self.scenes_dir, scene_id, self.camera_intrinsics_file)
        
        return full_path_scene_cam


    def get_camera_info_scene(self, scene_id):
        full_path_scene_cam = self.get_camera_info_scene_path(scene_id)

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

    def get_camera_poses(self, scene_id):
        # check if id is in this datasets scene id list
        full_path = os.path.join(
            self.root_dir, self.scenes_dir, scene_id, self.camera_pose_file)
        with open(full_path) as fp:
            pose_lines = fp.readlines()
        # The recorded poses adds line entries -> disregard first entry
        return [Pose(line.strip().split()[1:], wxyz=False) for line in pose_lines]

    def get_images_rgb(self, scene_id):
        files = self.get_images_rgb_path(scene_id)
        return [o3d.io.read_image(file) for file in files]

    def get_images_rgb_path(self, scene_id):
        full_path = os.path.join(
            self.root_dir, self.scenes_dir, scene_id, self.rgb_dir)

        extensions = ('.png', '.jpg')
        files = get_file_list(full_path, extensions)
        files.sort()
        return files

    def get_images_depth(self, scene_id):
        files = self.get_images_depth_path(scene_id)
        return [o3d.io.read_image(file) for file in files]

    def get_images_depth_path(self, scene_id):
        full_path = os.path.join(
            self.root_dir, self.scenes_dir, scene_id, self.depth_dir)

        extensions = ('.png')
        files = get_file_list(full_path, extensions)
        files.sort()
        return files 

    def get_pointclouds(self, scene_id):
        # return rgbd image reader which does not load images right away?
        # at loading it will use camera info, rgb and depth to create the rgbd image
        # with the help of open3d (maybe just the mesh?)
        rgb_images = self.get_images_rgb(scene_id)
        depth_images = self.get_images_depth(scene_id)
        camera_info = self.get_camera_info_scene(scene_id).as_o3d()
        camera_poses = self.get_camera_poses(scene_id)
        pointclouds = []
        for i, camera_pose in enumerate(camera_poses):
            rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
                rgb_images[i], depth_images[i], convert_rgb_to_intensity=False)
            pcd = o3d.geometry.PointCloud.create_from_rgbd_image(
                rgbd_image, camera_info)
            pointclouds.append(pcd.transform(camera_pose.tf))

        return pointclouds

    def get_object_poses(self, scene_id):
        full_path = os.path.join(
            self.root_dir, self.annotation_dir, scene_id, self.object_pose_file)

        objects = []
        if os.path.exists(full_path):
            with open(full_path) as fp:
                for items in (yaml.load(fp, Loader=yaml.FullLoader)):
                    scene_id = items.get("id")
                    pose = items.get("pose")
                    if not pose:
                        pose = np.eye(4).tolist()
                    objects.append([self.object_library[scene_id], pose])
        return objects

    def get_reconstruction(self, scene_id):
        full_path = os.path.join(
            self.reconstruction_dir, scene_id, self.reconstruction_file)
        if(os.path.exists(full_path)):
            return MeshReader(full_path)
        else:
            print(f"File {full_path} for reconstruction does not exist.")
            return None

    def get_reconstruction_visual(self, scene_id):
        full_path = os.path.join(
            self.reconstruction_dir, scene_id, self.reconstruction_visual_file)
        if(os.path.exists(full_path)):
            return MeshReader(full_path)
        else:
            print(f"File {full_path} for visualizing reconstruction does not exist.")
            return None

    def get_reconstruction_align(self, scene_id):
        full_path = os.path.join(
            self.reconstruction_dir, scene_id, self.reconstruction_align_file)
        if(os.path.exists(full_path)):
            return o3d.io.read_point_cloud(full_path)
        else:
            print(f"File {full_path} for  auto-align does not exist.")
            return None

