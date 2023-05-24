import yaml
import argparse
import configparser
import os
import v4r_dataset_toolkit as v4r

# import submodule script from instant-DexNerf
import sys
curr_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(curr_dir,"nerf/instant-DexNerf/scripts"))
import main as nerf

CONFIG = {
    "sigma_threshold": 15,
    "aabb_scale": 4,
    "train_steps": 5000,
    "view": 360
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
    parser.add_argument("--scene_id", nargs='*', type=str, default=None,
                        help="Scene identifier.")
    parser.add_argument("--sigma_threshold", type=int, default=None,
                        help="Sigma Threshold.")
    parser.add_argument("--aabb_scale", type=int, default=None,
                        help="Scale for crop_box.")
    parser.add_argument("--train_steps", type=int, default=None,
                        help="Training steps.")
    parser.add_argument("--view", type=int, default=None,
                        help="Camera views: 180 or 360 degrees.")
    args = parser.parse_args()

    config = None
    if(os.path.exists(args.dataset)):
        config = load_config(args.dataset)
        if not "Nerf" in config:
            print(
                f"Configuration file {args.dataset} does not contain Nerf parameter.")
            print("Using default parameter.")
            config = CONFIG
        else:
            config = config.get('Nerf')
    else:
        print(f"The config {args.dataset} file does not exist.")
        os.sys.exit(1)

    if args.sigma_threshold:
        config["sigma_threshold"] = args.sigma_threshold

    if args.aabb_scale:
        config["aabb_scale"] = args.aabb_scale

    if args.train_steps:
        config["train_steps"] = args.train_steps

    if args.view:
        config["view"] = args.view

    if config["view"] not in [180, 360]:
        view_value = config["view"]
        print(
            f"Error: The config paramter view for degrees of camera views {view_value} is invalid. Only 180 or 360 allowed.")
        os.sys.exit(1)

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

    print("Creating depth images from NeRF")
    for scene_id in scenes:
        print(f"Processing scene: {scene_id}")
        path_groundtruth = scene_file_reader.get_camera_info_scene_path(
            scene_id)
        scene_dir = os.path.join(
            scene_file_reader.root_dir, scene_file_reader.scenes_dir, scene_id)
        intrinsic = scene_file_reader.get_camera_info_scene(scene_id)
        nerf_intrinsic_file = os.path.join(scene_dir, "intrinsics.txt")
        with open(nerf_intrinsic_file, 'w') as fp:
            fp.write("%d %d %.12f %.12f %.12f %.12f %.12f %.12f %.12f %.12f %.12f %d\n" % (
                intrinsic.width, intrinsic.height, intrinsic.fx, 0.0, intrinsic.cx, 0.0, intrinsic.fy, intrinsic.cy, 0.0, 0.0, 1.0, config[
                    "view"]
            ))
            fp.flush()

        nerf.create_depthmaps(scene_dirs=[scene_dir], img_dir=scene_file_reader.rgb_dir, depth_dir=scene_file_reader.depth_dir, sigma_thrsh=config["sigma_threshold"],
                              aabb_scale=config["aabb_scale"], train_steps=config["train_steps"])

    print("Finished")
