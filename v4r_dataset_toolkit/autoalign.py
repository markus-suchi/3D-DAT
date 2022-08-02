import numpy as np
import open3d as o3d
from tqdm import tqdm
from v4r_dataset_toolkit.icp import multiscale_icp
import copy


def draw_registration_result_original_color(source, target, transformation):
    source_temp = copy.deepcopy(source)
    target_temp = copy.deepcopy(target)
    source_temp.transform(transformation)
    o3d.visualization.draw_geometries([source_temp, target_temp])


def sample_pointcloud(mesh, uniform_points=4500, poisson_points=4500):
    pcd = mesh.sample_points_uniformly(number_of_points=uniform_points)
    pcd = mesh.sample_points_poisson_disk(
        number_of_points=poisson_points, pcl=pcd)
    return pcd


def plane_reconstruct(incloud, min_number_points=40000):
    # Find all planes and sample them
    while(True):
        plane_model, inliers = incloud.segment_plane(
            distance_threshold=0.01, ransac_n=3, num_iterations=1000)
        number_of_points = len(inliers)
        if(number_of_points < min_number_points):
            print("Found a plane. Adding points to point cloud")
            incloud = incloud.select_by_index(inliers, invert=True)
        else:
            return incloud


def auto_align(object_mesh, scene_mesh, init_pose=np.identity(4)):
    # Aligning scene to object performs better than object to scene

    target_pcd = sample_pointcloud(object_mesh, 10000, 10000)
    source_pcd = sample_pointcloud(scene_mesh, 100000, 100000)

    transform = np.linalg.inv(init_pose)

    point_to_plane = True
    point_to_point = True

    if(point_to_plane):
        config = {'icp_method': 'point_to_plane',
                  'voxel_size': 0.01}

        voxel_size = config["voxel_size"]

        transform, information_mat = multiscale_icp(
            source_pcd,
            target_pcd,
            [voxel_size/4.0],
            [300],
            config,
            init_transformation=transform)

    if(point_to_point):
        config = {'icp_method': 'point_to_point',
                  'voxel_size': 0.004}

        voxel_size = config["voxel_size"]

        transform, information_mat = multiscale_icp(
            source_pcd,
            target_pcd,
            [2*voxel_size, voxel_size, voxel_size/2.0, voxel_size/4.0],
            [300, 300, 300, 300],
            config,
            init_transformation=transform)

    transform = np.linalg.inv(transform)
    return transform, information_mat
