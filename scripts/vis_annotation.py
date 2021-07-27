import argparse
import numpy as np
import os
from tqdm import tqdm
import trimesh
import yaml
import open3d as o3d


width = 1280
height = 720
fx = 923.101
fy = 922.568
cx = 629.3134765625
cy = 376.28814697265625


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


def load_models_from_blender_scene(object_path, blender_config):
    oriented_models = []
    for child in tqdm(blender_config, desc="Blender anno models loading"):
        fn = child["path"]
        pose = np.array(child["pose"]).reshape(4, 4)
        model = trimesh.load(os.path.join(object_path, fn))
        model.apply_transform(pose)
        oriented_models.append(model)

    return oriented_models


def visualize(rgb, depth, models, pose):
    vis = o3d.visualization.Visualizer()
    vis.create_window()

    opt = vis.get_render_option()
    opt.mesh_show_back_face = True
    rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
        rgb, depth, convert_rgb_to_intensity=False)

    prime = o3d.camera.PinholeCameraIntrinsic(width=width, height=height,
                                              fx=fx,
                                              fy=fy,
                                              cx=cx,
                                              cy=cy)

    pcd = o3d.geometry.PointCloud.create_from_rgbd_image(
        rgbd_image, prime)
    pcd = pcd.transform(pose)
    vis.add_geometry(pcd)

    for model in models:
        open3d_model = model.as_open3d
        open3d_model.paint_uniform_color(np.random.rand(3,))
        vis.add_geometry(open3d_model)

    ctr = vis.get_view_control()
    cam_view = ctr.convert_to_pinhole_camera_parameters()
    cam_view.extrinsic = np.linalg.inv(pose)
    ctr.convert_from_pinhole_camera_parameters(cam_view)
    vis.run()
    vis.destroy_window()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Visualize annotated data.")
    parser.add_argument("-d", "--data", type=str, required=True,
                        help="Path to scene")
    args = parser.parse_args()

    # load camera poses
    camera_poses = get_poses(
        os.path.join(args.data, "groundtruth_handeye.txt"))

    # load yaml files with paths to objects and poses
    with open(os.path.join(args.data, "poses.yaml")) as fp:
        pose_anno = yaml.load(fp, Loader=yaml.FullLoader)
        object_path = os.path.split(os.path.split(args.data)[0])[0]
        oriented_models = load_models_from_blender_scene(
            object_path, pose_anno)

    # visualize
    count = len(camera_poses)
    rgb_path = os.path.join(args.data, "rgb")
    rgb_imgs = [o3d.io.read_image("{}/{:05}.png".format(rgb_path, i+1))
                for i in tqdm(range(count), desc="Original images loading")]
    depth_path = os.path.join(args.data, "depth")
    depth_imgs = [o3d.io.read_image("{}/{:05}.png".format(depth_path, i+1))
                  for i in tqdm(range(count), desc="Original images loading")]

    for i in range(count):
        visualize(rgb_imgs[i], depth_imgs[i], oriented_models, camera_poses[i])
