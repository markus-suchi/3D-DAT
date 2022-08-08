import argparse
import os
import v4r_dataset_toolkit as v4r

CONFIG = {
    "debug_mode": True,
    "max_depth": 1.3,
    "voxel_size": 0.004,
    "tsdf_cubic_size": 1.5,
    "icp_method": "color",
    "icp_refinement": False,
    "save_refined": True,
    "sdf_trunc": 0.018,
    "triangles": 500000,
    "no_simplify": False,
    "cluster" : False
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Integrate the whole RGBD sequence using estimated camera pose.")
    parser.add_argument("-d", "--dataset", type=str, default="./config.cfg",
                        help="Path to data to reconstruct")
    parser.add_argument("--icp_refinement", action="store_true",
                        help="Activate the ICP refinement step")
    parser.add_argument("--triangles", type=int, default=500000,
                        help="Target triangles for simpilfication.")
    parser.add_argument("--icp_method", type=str, default="color",
                        help="Target triangles for simpilfication.")
    parser.add_argument("--no_simplify", action="store_true",
                        help="Do not simplify reconstruction.")
    parser.add_argument("--cluster", action="store_true",
                        help="Use largest triangle cluster only.")
    parser.add_argument("--scene_id", type=str, default=None,
                        help="Target triangles for simpilfication.")
    args = parser.parse_args()

    CONFIG["triangles"] = args.triangles

    if args.icp_refinement:
        CONFIG["icp_refinement"] = True
        CONFIG["icp_method"]=args.icp_method

    if args.no_simplify:
        CONFIG["no_simplify"] = True

    if args.cluster:
        CONFIG["cluster"] = True

    print("Configuration:")
    for k, v in CONFIG.items():
        print("\t", k, ":", v)

    scene_file_reader = v4r.io.SceneFileReader.create(args.dataset)
    print("Creating Reconstructor")
    # Refine with ICP
    path_groundtruth = os.path.join(
        scene_file_reader.root_dir,
        scene_file_reader.scenes_dir,
        args.scene_id,
        scene_file_reader.camera_pose_file)

    path_dataset = os.path.join(
        scene_file_reader.annotation_dir,
        args.scene_id)

    color_files = scene_file_reader.get_images_rgb(args.scene_id)
    depth_files = scene_file_reader.get_images_depth(args.scene_id)
    intrinsic = scene_file_reader.get_camera_info_scene(args.scene_id).as_o3d()
    poses = scene_file_reader.get_camera_poses(args.scene_id)

    reconstructor = v4r.reconstructor.Reconstructor(config=CONFIG, 
                                  color_files = color_files,
                                  depth_files = depth_files,
                                  intrinsic = intrinsic,
                                  poses = poses,
                                  path_groundtruth = path_groundtruth,
                                  path_dataset = path_dataset)

    reconstructor.get_reconstruction()
    print("Finished")
