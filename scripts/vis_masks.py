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

import v4r_dataset_toolkit as v4r


groundtruth_to_pyrender = np.array([[1, 0, 0, 0],
                                    [0, -1, 0, 0],
                                    [0, 0, -1, 0],
                                    [0, 0, 0, 1]])

frames = 64


def project_mesh_to_2d(models, cam_poses, model_colors, intrinsic):
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
    camera = pyrender.camera.IntrinsicsCamera(intrinsic.fx,
                                              intrinsic.fy,
                                              intrinsic.cx,
                                              intrinsic.cy)
    nc = pyrender.Node(camera=camera, matrix=np.eye(4))
    scene.add_node(nc)
    nl = pyrender.Node(matrix=np.eye(4))
    scene.add_node(nl)

   # --- Rendering -----------------------------------------------------------
    renders = []
    r = pyrender.OffscreenRenderer(intrinsic.width, intrinsic.height)
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


def load_object_models(scene_file_reader):
    oriented_models = []
    # Load poses
    objects = scene_file_reader.get_object_poses(args.scene_id)
    for object in tqdm(objects, desc="Loading objects."):
        scene_object = scene_file_reader.object_library[object[0].id]
        model = scene_object.mesh.as_trimesh()
        model.apply_transform(np.array(object[1]).reshape(4, 4))
        oriented_models.append(model)
    return oriented_models


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Reproject models to create annotation images.")
    parser.add_argument("-c", "--config", type=str, required=True,
                        help="Path to reconstructed data")
    parser.add_argument("-s", "--scene_id", type=str, required=True,
                        help="Scene identifier to visualize.")
    args = parser.parse_args()

    scene_file_reader = v4r.io.SceneFileReader.create(args.config)
    camera_poses = scene_file_reader.get_camera_poses(args.scene_id)
    intrinsic = scene_file_reader.get_camera_info()
    objects = scene_file_reader.get_object_poses(args.scene_id)
    object_library = scene_file_reader.get_object_library()

    oriented_models = load_object_models(scene_file_reader)

    model_colors = []
    for object in objects:
        scene_object = scene_file_reader.object_library[object[0].id]
        model_colors.append(scene_object.color)

    orig_imgs = scene_file_reader.get_images_rgb(args.scene_id)
    camera_poses = [pose.tf for pose in camera_poses]
    annotation_imgs = project_mesh_to_2d(
        oriented_models, camera_poses, model_colors, intrinsic)

    for pose_idx, anno_img in enumerate(annotation_imgs):
        plt.figure(figsize=(21, 13))
        alpha = 0.5
        masked_image = (
            1. - alpha) * np.asarray(orig_imgs[pose_idx]) + alpha * anno_img.astype(float)
        plt.imshow(masked_image/255.)
        plt.show()
