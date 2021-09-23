import argparse
import cv2
import matplotlib.pyplot as plt
import numpy as np
import os
import pyrender
from tqdm import tqdm
import trimesh
import yaml
import open3d as o3d
import copy


width = 1280
height = 720
# d415
fx = 923.101
fy = 922.568
cx = 629.3134765625
cy = 376.28814697265625

# d435
#fx = 909.926 
#fy = 907.9168
#cx = 643.5625
#cy = 349.01718

groundtruth_to_pyrender = np.array([[1, 0, 0, 0],
                                    [0, -1, 0, 0],
                                    [0, 0, -1, 0],
                                    [0, 0, 0, 1]])

frames = 95


def project_mesh_to_2d(models, cam_poses, model_colors):
    # --- PyRender scene setup ------------------------------------------------
    scene = pyrender.Scene(bg_color=[0, 0, 0])

    seg_node_map = {}
    # Add model mesh
    for model_idx, model in enumerate(models):
        # pyrender render flag SEG does not allow to ignore culling backfaces
        # Instead set color for the mask on the trimesh mesh
        model.visual.face_colors = model_colors[model_idx]
        pyr_mesh = pyrender.Mesh.from_trimesh(model, smooth=False)
        nm = pyrender.Node(mesh=pyr_mesh)
        scene.add_node(nm)

    # Add camera
    camera = pyrender.camera.IntrinsicsCamera(fx, fy, cx, cy)
    nc = pyrender.Node(camera=camera, matrix=np.eye(4))
    scene.add_node(nc)
    nl = pyrender.Node(matrix=np.eye(4))
    scene.add_node(nl)

   # --- Rendering -----------------------------------------------------------
    renders = []
    r = pyrender.OffscreenRenderer(width, height)
    for cam_pose in tqdm(cam_poses, desc="Reprojection rendering"):
        # different coordinate system when using renderer
        cam_pose = cam_pose.dot(groundtruth_to_pyrender)
        # Render
        scene.set_pose(nc, pose=cam_pose)
        scene.set_pose(nl, pose=cam_pose)

        img, depth = r.render(
            scene, flags=pyrender.RenderFlags.SKIP_CULL_FACES | pyrender.RenderFlags.FLAT)
        renders.append(img)

    return renders


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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Reproject models to create annotation images.")
    parser.add_argument("-d", "--dataset", type=str, default="./data",
                        help="Path to reconstructed data")
    args = parser.parse_args()

    groundtruth = "groundtruth_handeye.txt"
    camera_poses = get_poses(
        os.path.join(args.dataset, groundtruth))

    # load yaml files with paths to objects and poses
    path_blender_anno = args.dataset
    with open(os.path.join(path_blender_anno, "poses.yaml")) as fp:
        pose_anno = yaml.load(fp, Loader=yaml.FullLoader)
        object_path = os.path.split(os.path.split(args.dataset)[0])[0]
        oriented_models = load_models_from_blender_scene(
            object_path, pose_anno)

        model_id_to_colors = {
            1: [0, 255., 255.],
            2: [255., 0., 0.],
            3: [0., 255., 0.],
            4: [0., 0., 255.],
            5: [255., 255., 0.]
        }
        scene_model_ids = [model_id["id"] for model_id in pose_anno]
        print(scene_model_ids)
        model_colors = [model_id_to_colors[model_id]
                        for model_id in scene_model_ids]

        imgs_path = os.path.join(args.dataset, "rgb")
        orig_imgs = [cv2.imread("{}/{:05}.png".format(imgs_path, i+1))[..., ::-1]
                     for i in tqdm(range(frames), desc="Original images loading")]

   # Render views
    annotation_imgs = project_mesh_to_2d(
        oriented_models, camera_poses, model_colors)

    # Combined view of the annotation image and original image
    for pose_idx, anno_img in enumerate(annotation_imgs):
        plt.figure(figsize=(21, 13))
        alpha = 0.5
        masked_image = (
            1. - alpha) * orig_imgs[pose_idx].astype(float) + alpha * anno_img.astype(float)
        plt.imshow(masked_image/255.)
        plt.show()
