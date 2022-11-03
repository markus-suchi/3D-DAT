import argparse
import configparser
import os
import v4r_dataset_toolkit as v4r
import yaml

CONFIG = {
    "debug_mode": True,
    "max_depth": 1.3,
    "voxel_size": 0.004,
    "tsdf_cubic_size": 1.5,
    "icp_method": "color",
    "icp_refinement": False,
    "save_refined": True,
    "sdf_trunc": 0.018,
    "triangles": 1000000,
    "simplify": False,
    "cluster" : False
}

def load_config(file):
    with open(file, 'r') as fp:
        return yaml.load(fp, Loader=yaml.FullLoader)
    return none
     
if __name__ == "__main__":
    parser = argparse.ArgumentParser("Integrate the whole RGBD sequence using estimated camera pose.")
    parser.add_argument("-d", "--dataset", type=str, default="./config.cfg",
                        help="Path to data to reconstruct")
    parser.add_argument("--icp_refinement", action="store_true",
                        help="Activate the ICP refinement step")
    parser.add_argument("--triangles", type=int, default=None,
                        help="Target triangles for simpilfication.")
    parser.add_argument("--icp_method", type=str, default="color",
                        help="Target triangles for simpilfication.")
    parser.add_argument("--simplify", action="store_true",
                        help="Do simplify reconstruction.")
    parser.add_argument("--cluster", action="store_true",
                        help="Use largest triangle cluster only.")
    parser.add_argument("--scene_id", type=str, default=None,
                        help="Scene identifier.")
    args = parser.parse_args()


    config = None
    if(os.path.exists(args.dataset)):
        config = load_config(args.dataset)
        if not "Reconstruction" in config:
            print(f"Configuration file {args.dataset} does not contain reconstruction parameter.")
            print("Using default parameter.")
            config=CONFIG
        else:
            config=config.get('Reconstruction')
    else:
        print(f"The config {args.dataset} file does not exist.")
        os.sys.exit(1)

    if args.triangles:
        config["triangles"]= args.triangles

    if args.icp_refinement:
        config["icp_refinement"]=True
        config["icp_method"]=args.icp_method

    if args.simplify:
        config["simplify"]=True

    if args.cluster:
        config["cluster"]=True

    print("Configuration:")
    for k, v in config.items():
        print("\t", k, ":", v)

    scene_file_reader = v4r.io.SceneFileReader.create(args.dataset)
    print("Creating Reconstructor")
    # Refine with ICP
    path_groundtruth = scene_file_reader.get_camera_info_scene_path(args.scene_id) 
    path_dataset = os.path.join(
        scene_file_reader.reconstruction_dir,
        args.scene_id)

    color_files = scene_file_reader.get_images_rgb(args.scene_id)
    depth_files = scene_file_reader.get_images_depth(args.scene_id)
    intrinsic = scene_file_reader.get_camera_info_scene(args.scene_id).as_o3d()
    poses = scene_file_reader.get_camera_poses(args.scene_id)

    reconstructor = v4r.reconstructor.Reconstructor(config=config, 
                                  color_files = color_files,
                                  depth_files = depth_files,
                                  intrinsic = intrinsic,
                                  poses = poses,
                                  path_groundtruth = path_groundtruth,
                                  path_dataset = path_dataset)

    reconstructor.create_reconstruction()
    print("Finished")
