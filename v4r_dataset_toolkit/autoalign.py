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


def auto_align(object_mesh, scene_mesh, init_pose=np.identity(4)):

    source_pcd = sample_pointcloud(object_mesh, 10000, 10000)
    #source_pcd = sample_pointcloud(scene_mesh, 100000, 100000)
    target_pcd = scene_mesh

    transform = init_pose

    point_to_plane = True
    point_to_point = True

    if(point_to_plane):
        config = {'icp_method': 'point_to_plane',
                  'voxel_size': 0.004}

        voxel_size = float(config.get("voxel_size"))

        transform, information_mat = multiscale_icp(
            source_pcd,
            target_pcd,
            [voxel_size],
            [300],
            config,
            init_transformation=transform)

    if(point_to_point):
        config = {'icp_method': 'point_to_point',
                  'voxel_size': 0.004}

        voxel_size = float(config.get("voxel_size"))

        transform, information_mat = multiscale_icp(
            source_pcd,
            target_pcd,
            [2*voxel_size, voxel_size, voxel_size/2.0, voxel_size/4.0],
            [300, 300, 300, 300],
            config,
            init_transformation=transform)

    return transform, information_mat
