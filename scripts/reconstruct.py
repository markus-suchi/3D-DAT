import argparse
import configparser
import os
import v4r_dataset_toolkit as v4r
import yaml

CONFIG = {
    "debug_mode": False,
    "max_depth": 1.3,
    "voxel_size": 0.004,
    "tsdf_cubic_size": 1.5,
    "icp_method": "color",
    "icp_refinement": False,
    "save_refined": True,
    "sdf_trunc": 0.018,
    "triangles": 1000000,
    "simplify": False,
    "cluster": False
}


def load_config(file):
    with open(file, 'r') as fp:
        return yaml.load(fp, Loader=yaml.FullLoader)
    return none


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Integrate the whole RGBD sequence using estimated camera pose.")
    parser.add_argument("-d", "--dataset", type=str, default="./dataset.yaml",
                        help="Path to dataset configuration.")
    parser.add_argument("--icp_refinement", action="store_true",
                        help="Activate the ICP refinement step")
    parser.add_argument("--triangles", type=int, default=None,
                        help="Target triangles for simpilfication.")
    parser.add_argument("--icp_method", type=str, default="color",
                        help="Icp-method one of ['point_to_point','robust_icp','point_to_plane','color'].")
    parser.add_argument("--simplify", action="store_true",
                        help="Do simplify reconstruction.")
    parser.add_argument("--cluster", action="store_true",
                        help="Use largest triangle cluster only.")
    parser.add_argument("--debug_mode", action="store_true",
                        help="Visualize reconstruction.")
    parser.add_argument("--max_depth", type=float, default=None,
                        help="Set max depth in meter.")
    parser.add_argument("--voxel_size", type=float, default=None,
                        help="Set voxel size in meter.")
    parser.add_argument("--tsdf_cubic_size", type=float, default=None,
                        help="Set size of tsdf cube in meter.")
    parser.add_argument("--sdf_trunc", type=float, default=None,
                        help="Truncation value for signed distance function.")
    parser.add_argument("--scene_id", nargs='*', type=str, default=None,
                        help="Scene identifier.")
    args = parser.parse_args()

    config = None
    if(os.path.exists(args.dataset)):
        config = load_config(args.dataset)
        if not "Reconstruction" in config:
            print(
                f"Configuration file {args.dataset} does not contain reconstruction parameter.")
            print("Using default parameter.")
            config = CONFIG
        else:
            config = config.get('Reconstruction')
    else:
        print(f"The config {args.dataset} file does not exist.")
        os.sys.exit(1)

    if args.triangles:
        config["triangles"] = args.triangles

    if args.icp_refinement:
        config["icp_refinement"] = True
        config["icp_method"] = args.icp_method

    if args.simplify:
        config["simplify"] = True

    if args.cluster:
        config["cluster"] = True

    if args.debug_mode:
        config["debug_mode"] = args.debug_mode

    if args.max_depth:
        config["max_depth"] = args.max_depth

    if args.voxel_size:
        config["voxel_size"] = args.voxel_size

    if args.tsdf_cubic_size:
        config["tsdf_cubic_size"] = args.tsdf_cubic_size

    if args.sdf_trunc:
        config["sdf_trunc"] = args.sdf_trunc

    print("Configuration:")
    for k, v in config.items():
        print("\t", k, ":", v)

    scene_file_reader = v4r.io.SceneFileReader.create(args.dataset)

# check if we have a scene_id parameter
    scenes = []
    all_scenes = scene_file_reader.get_scene_ids()
    if args.scene_id:
        scenes = sorted(args.scene_id)
        # check if all scene ids are present
        diff = [x for x in scenes if x not in all_scenes]
        if diff:
            print("Error: The following scenes are not part of the dataset:")
            print(diff)
            os.sys.exit(1)
    else:
        scenes = all_scenes

    print("Creating Reconstruction")
    for scene_id in scenes:
        print(f"Processing scene: {scene_id}")
        path_groundtruth = scene_file_reader.get_camera_info_scene_path(
            scene_id)
        path_dataset = os.path.join(
            scene_file_reader.reconstruction_dir,
            scene_id)

        color_files = scene_file_reader.get_images_rgb(scene_id)
        depth_files = scene_file_reader.get_images_depth(scene_id)
        intrinsic = scene_file_reader.get_camera_info_scene(scene_id).as_o3d()
        poses = scene_file_reader.get_camera_poses(scene_id)

        reconstructor = v4r.reconstructor.Reconstructor(config=config,
                                                        color_files=color_files,
                                                        depth_files=depth_files,
                                                        intrinsic=intrinsic,
                                                        poses=poses,
                                                        path_groundtruth=path_groundtruth,
                                                        path_dataset=path_dataset)

        reconstructor.create_reconstruction()
    print("Finished")
