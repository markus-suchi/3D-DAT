import numpy as np
import open3d as o3d
from tqdm import tqdm
import copy

flip_transform = [[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]]

def draw_registration_result_original_color(source, target, transformation):
    source_temp = copy.deepcopy(source)
    target_temp = copy.deepcopy(target)
    source_temp.transform(transformation)
    source_temp.transform(flip_transform)
    target_temp.transform(flip_transform)
    o3d.visualization.draw_geometries([source_temp, target_temp])


def multiscale_icp(source,
                   target,
                   voxel_size,
                   max_iter,
                   config,
                   init_transformation=np.identity(4)):
    current_transformation = init_transformation
    for i, scale in enumerate(range(len(max_iter))):  # multi-scale approach
        iter = max_iter[scale]
        distance_threshold = float(config.get("voxel_size")) * 1.4  
        # print("voxel_size %f" % voxel_size[scale])
        source_down = source.voxel_down_sample(voxel_size[scale])
        target_down = target.voxel_down_sample(voxel_size[scale])

        if config.get("icp_method") == "point_to_point":
            result_icp = o3d.pipelines.registration.registration_icp(
                source_down, target_down, distance_threshold,
                current_transformation,
                o3d.pipelines.registration.TransformationEstimationPointToPoint(),
                o3d.pipelines.registration.ICPConvergenceCriteria(
                    max_iteration=iter,
                    relative_fitness=1e-6,
                    relative_rmse=1e-6,
                        ))
        elif config.get("icp_method") == "robust_icp":
            print("Robust ICP")
            conv_criteria =  o3d.pipelines.registration.ICPConvergenceCriteria(
                        relative_fitness=1e-6,
                        relative_rmse=1e-6,
                        max_iteration=iter)
             
            result_icp = o3d.pipelines.registration.registration_generalized_icp(
                source_down, target_down, distance_threshold,
                init = current_transformation,
                estimation_method = o3d.pipelines.registration.TransformationEstimationForGeneralizedICP(),
                criteria = conv_criteria)
            print(result_icp)
        else:
            source_down.estimate_normals(
                o3d.geometry.KDTreeSearchParamHybrid(radius=voxel_size[scale] *
                                                     2.0,
                                                     max_nn=30))
            target_down.estimate_normals(
                o3d.geometry.KDTreeSearchParamHybrid(radius=voxel_size[scale] *
                                                     2.0,
                                                     max_nn=30))
            if config.get("icp_method") == "point_to_plane":
                # check if pointcloud has normals
                result_icp = o3d.pipelines.registration.registration_icp(
                    source_down, target_down, distance_threshold,
                    current_transformation,
                    o3d.pipelines.registration.TransformationEstimationPointToPlane(),
                    o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=iter,
                                                                      relative_fitness=1e-6,
                                                                      relative_rmse=1e-6))
            elif config.get("icp_method") == "color":
                conv_criteria =  o3d.pipelines.registration.ICPConvergenceCriteria(
                        relative_fitness=1e-6,
                        relative_rmse=1e-6,
                        max_iteration=iter)
                result_icp = o3d.pipelines.registration.registration_colored_icp(
                    source=source_down, 
                    target=target_down, 
                    max_correspondence_distance=voxel_size[scale],
                    init=current_transformation, 
                    criteria=conv_criteria
                    )
            else:
                raise TypeError("Method %s not supported." % config["icp_method"])

        current_transformation = result_icp.transformation
        if i == len(max_iter) - 1:
            information_matrix = o3d.pipelines.registration.get_information_matrix_from_point_clouds(
                source_down, target_down, voxel_size[scale] * 1.4,
                result_icp.transformation)

    return (result_icp.transformation, information_matrix)


def icp_refinement(rgbds, poses, intrinsic, config):
    voxel_size = float(config.get("voxel_size"))

    for frame_id in tqdm(range(1, len(rgbds), 1), desc="Refinement"):
        source = o3d.geometry.PointCloud.create_from_rgbd_image(
            rgbds[frame_id-1],
            intrinsic,
            poses[frame_id-1])

        target = o3d.geometry.PointCloud.create_from_rgbd_image(
            rgbds[frame_id],
            intrinsic,
            poses[frame_id])

        transfo, information_mat = multiscale_icp(
            source,
            target,
            [2*voxel_size, voxel_size, voxel_size/2.0, voxel_size/4.0],
            [100, 50, 30, 14],
            config,
            init_transformation=np.identity(4))

        poses[frame_id] = np.dot(poses[frame_id], transfo)
