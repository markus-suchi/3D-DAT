import argparse
import numpy as np
from tqdm import tqdm
import trimesh
import open3d as o3d
import v4r_dataset_toolkit as v4r


def load_object_models(scene_file_reader, id):
    oriented_models = []
    # Load poses
    objects = scene_file_reader.get_object_poses(id)
    for object in tqdm(objects, desc="Loading objects."):
        scene_object = scene_file_reader.object_library[object[0].id]
        model = scene_object.mesh.as_trimesh()
        model.apply_transform(np.array(object[1]).reshape(4, 4))
        oriented_models.append(model)
    return oriented_models


def visualize_objects(pointcloud=None, oriented_models=None, camera_pose=None):
    vis = o3d.visualization.Visualizer()
    vis.create_window()

    opt = vis.get_render_option()
    opt.mesh_show_back_face = True

    vis.add_geometry(pointcloud)

    for model in oriented_models:
        open3d_model = model.as_open3d
        open3d_model.paint_uniform_color(np.random.rand(3,))
        vis.add_geometry(open3d_model)

    ctr = vis.get_view_control()
    cam_view = ctr.convert_to_pinhole_camera_parameters()
    cam_view.extrinsic = np.linalg.inv(camera_pose)
    ctr.convert_from_pinhole_camera_parameters(cam_view)
    vis.run()
    vis.destroy_window()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Visualize annotated data.")
    parser.add_argument("-d", "--dataset", type=str, required=True,
                        help="Path to dataset configuration.")
    parser.add_argument("-s", "--scene_id", type=str, required=True,
                        help="Scene identifier to visualize.")
    args = parser.parse_args()

    scene_file_reader = v4r.io.SceneFileReader.create(args.dataset)

    oriented_models = load_object_models(scene_file_reader, args.scene_id)

    camera_poses = scene_file_reader.get_camera_poses(args.scene_id)
    pointclouds = scene_file_reader.get_pointclouds(args.scene_id)
    for i, camera_pose in enumerate(camera_poses):
        visualize_objects(oriented_models=oriented_models,
                          pointcloud=pointclouds[i],
                          camera_pose=camera_pose.tf)
