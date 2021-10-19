import argparse
import copy
import numpy as np
import open3d as o3d
import os
from scipy.spatial.transform import Rotation as R
from tqdm import tqdm

from .icp import icp_refinement

def save_poses(poses, path_groundtruth):
    with open(path_groundtruth, "w") as fp:
        for idx, pose in enumerate(poses):
            quat = R.from_matrix(pose[:3, :3]). as_quat()
            vals = [str(idx)] + list(np.append(pose[:3, -1], quat).astype(str))
            fp.write(" ".join(vals) + "\n")


class Reconstructor:
    def __init__(self, config=None, 
                 color_files=None, 
                 depth_files=None, 
                 poses=None, 
                 intrinsic=None, 
                 path_groundtruth = None,
                 path_dataset = None):
        self.config = config
        self.color_files = color_files
        self.depth_files = depth_files
        self.poses = poses
        self.intrinsic = intrinsic
        self.path_dataset = path_dataset

    def get_reconstruction(self):
            n_files = len(self.color_files)

            volume = o3d.pipelines.integration.ScalableTSDFVolume(
                voxel_length=self.config["tsdf_cubic_size"] / 512.0,
                sdf_trunc=self.config["sdf_trunc"],
                color_type=o3d.pipelines.integration.TSDFVolumeColorType.RGB8)

            voxel_size = self.config["voxel_size"]

            rgbds = []
            for i, color_file in enumerate(self.color_files):
                rgbd_image = o3d.geometry.RGBDImage.create_from_color_and_depth(
                    color_file,
                    self.depth_files[i],
                    depth_trunc=self.config["max_depth"],
                    convert_rgb_to_intensity=False)
                rgbds.append(rgbd_image)

            poses = [np.linalg.inv(pose.tf) for pose in self.poses] 

            #TODO: use refined if available
            if self.config["icp_refinement"] and path_groundtruth[-11:-4] != "refined":
                icp_refinement(rgbds, poses, intrinsic, config=self.config)

                if config["save_refined"]:
                    save_poses(poses, path_groundtruth[:-4] + "_refined.txt")

            for frame_id in tqdm(range(n_files), desc="Integration"):
                volume.integrate(rgbds[frame_id], self.intrinsic, poses[frame_id])

            print("Meshing out")
            mesh = volume.extract_triangle_mesh()
           
            if not self.config["no_simplify"]:
                print("Simplifying " + str(len(mesh.vertices)) + " vertices and " + str(len(mesh.triangles)) + " triangles")
                mesh = mesh.simplify_quadric_decimation(target_number_of_triangles=self.config["triangles"])
                print("Now         " + str(len(mesh.vertices)) + " vertices and " + str(len(mesh.triangles)) + " triangles")
                    
                mesh.compute_vertex_normals()

            if self.config["cluster"]:
                print("Clustering mesh.")
                triangle_clusters, cluster_n_triangles, cluster_area = (
                            mesh.cluster_connected_triangles())
                triangle_clusters = np.asarray(triangle_clusters)
                cluster_n_triangles = np.asarray(cluster_n_triangles)

                # Keep only largest cluster
                largest_cluster_idx = cluster_n_triangles.argmax()
                triangles_to_remove = triangle_clusters != largest_cluster_idx

                mesh.remove_triangles_by_mask(triangles_to_remove)

            mesh_name = os.path.join(self.path_dataset, "mesh.ply")
            o3d.io.write_triangle_mesh(mesh_name, mesh, False, True)

            if self.config["debug_mode"]:
                o3d.visualization.draw_geometries([mesh])


