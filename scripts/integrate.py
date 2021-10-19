import argparse
import copy
import numpy as np
import open3d as o3d
import os
from scipy.spatial.transform import Rotation as R
from tqdm import tqdm

from icp import icp_refinement


def read_rgbd_image(color_file, depth_file, convert_rgb_to_intensity, config):
    color = o3d.io.read_image(color_file)
    depth = o3d.io.read_image(depth_file)

    rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
        color,
        depth,
        depth_trunc=config["max_depth"],
        convert_rgb_to_intensity=convert_rgb_to_intensity)
    return rgbd_image


def get_rgbd_file_lists(path_dataset):
    with open(os.path.join(path_dataset, "associations.txt")) as fp:
        associations = fp.readlines()
    associations = [line.strip().split() for line in associations]

    color_files = [os.path.join(path_dataset, line[1]) for line in associations]
    depth_files = [os.path.join(path_dataset, line[0]) for line in associations]

    return color_files, depth_files


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
        pose[:3, :3] = R.from_quat(quat[i]).as_matrix()
        pose[:3, -1] = trans[i]
        pose = np.linalg.inv(pose)
        poses.append(pose)

    return poses


def save_poses(poses, path_groundtruth):
    with open(path_groundtruth, "w") as fp:
        for idx, pose in enumerate(poses):
            quat = R.from_matrix(pose[:3, :3]). as_quat()
            vals = [str(idx)] + list(np.append(pose[:3, -1], quat).astype(str))
            fp.write(" ".join(vals) + "\n")


def scalable_integrate_rgb_frames(path_dataset, path_groundtruth, intrinsic, config):
    color_files, depth_files = get_rgbd_file_lists(path_dataset)
    poses = get_poses(path_groundtruth)
    n_files = len(color_files)

    volume = o3d.pipelines.integration.ScalableTSDFVolume(
        voxel_length=config["tsdf_cubic_size"] / 512.0,
        sdf_trunc=config["sdf_trunc"],
        color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8)

    voxel_size = config["voxel_size"]

    rgbds = []
    for frame_id in range(n_files):
        rgbds.append(read_rgbd_image(color_files[frame_id],
                                     depth_files[frame_id], False, config))

    # Refine with ICP
    if config["icp_refinement"] and path_groundtruth[-11:-4] != "refined":
        icp_refinement(rgbds, poses, intrinsic, config=config)

        if config["save_refined"]:
            save_poses(poses, path_groundtruth[:-4] + "_refined.txt")

    for frame_id in tqdm(range(n_files), desc="Integration"):
        volume.integrate(rgbds[frame_id], intrinsic, poses[frame_id])

    print("Meshing out")
    mesh = volume.extract_triangle_mesh()
   
    if not config["no_simplify"]:
        print("Simplifying " + str(len(mesh.vertices)) + " vertices and " + str(len(mesh.triangles)) + " triangles")
        mesh = mesh.simplify_quadric_decimation(target_number_of_triangles=config["triangles"])
        print("Now         " + str(len(mesh.vertices)) + " vertices and " + str(len(mesh.triangles)) + " triangles")
            
        mesh.compute_vertex_normals()
        mesh.compute_vertex_normals()

    if config["cluster"]:
        print("Clustering mesh.")
        triangle_clusters, cluster_n_triangles, cluster_area = (
                    mesh.cluster_connected_triangles())
        triangle_clusters = np.asarray(triangle_clusters)
        cluster_n_triangles = np.asarray(cluster_n_triangles)

        # Keep only largest cluster
        largest_cluster_idx = cluster_n_triangles.argmax()
        triangles_to_remove = triangle_clusters != largest_cluster_idx

        mesh.remove_triangles_by_mask(triangles_to_remove)

    mesh_name = os.path.join(path_dataset, "mesh.ply")
    o3d.io.write_triangle_mesh(mesh_name, mesh, False, True)

    if config["debug_mode"]:
        o3d.visualization.draw_geometries([mesh])



CONFIG = {
    "debug_mode": True,
    "max_depth": 0.95,
    "voxel_size": 0.02,
    "tsdf_cubic_size": 1.0,
    "icp_method": "color",
    "icp_refinement": False,
    "save_refined": True,
    "sdf_trunc": 0.008,
    "triangles": 500000,
    "no_simplify": False,
    "cluster" : False
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser("Integrate the whole RGBD sequence using estimated camera pose.")
    parser.add_argument("-d", "--dataset", type=str, default="data/16_03_21/plate/",
                        help="Path to data to reconstruct")
    parser.add_argument("-g", "--groundtruth", type=str, default="data/16_03_21//empty/groundtruth_refined.txt",
                        help="Path to groundtruth camera poses")
    parser.add_argument("--icp_refinement", action="store_true",
                        help="Activate the ICP refinement step")
    parser.add_argument("--low_res", action="store_true",
                        help="Use high resolution camera intrinsics")
    parser.add_argument("--triangles", type=int, default=500000,
                        help="Target triangles for simpilfication.")
    parser.add_argument("--icp_method", type=str, default="color",
                        help="Target triangles for simpilfication.")
    parser.add_argument("--no_simplify", action="store_true",
                        help="Do not simplify reconstruction.")
    parser.add_argument("--cluster", action="store_true",
                        help="Use largest triangle cluster only.")
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


    if args.low_res:
        width = 640
        height = 480
        fx = 596.63
        fy = 596.63
        cx = 311.99
        cy = 236.76
    else:
        # High res version
        width = 1280
        height = 720
        fx = 923.101
        fy = 922.568
        cx = 629.3134765625
        cy = 376.28814697265625

    intrinsic = o3d.camera.PinholeCameraIntrinsic(width, height, fx, fy, cx, cy)
    # intrinsic = o3d.camera.PinholeCameraIntrinsic(o3d.camera.PinholeCameraIntrinsicParameters.PrimeSenseDefault) # Asus default

    scalable_integrate_rgb_frames(args.dataset, args.groundtruth, intrinsic, CONFIG)
