import argparse
import numpy as np
from tqdm import tqdm
import trimesh
import open3d as o3d
import v4r_dataset_toolkit as v4r
import os
import yaml
import scipy
from scipy.spatial.transform import Rotation as R
import math
import glob

def re(R_est, R_gt):
  """Rotational Error.
  :param R_est: 3x3 ndarray with the estimated rotation matrix.
  :param R_gt: 3x3 ndarray with the ground-truth rotation matrix.
  :return: The calculated error.
  """
  assert (R_est.shape == R_gt.shape == (3, 3))
  error_cos = float(0.5 * (np.trace(R_est.dot(np.linalg.inv(R_gt))) - 1.0))

  # Avoid invalid values due to numerical errors.
  error_cos = min(1.0, max(-1.0, error_cos))

  error = math.acos(error_cos)
  error = 180.0 * error / np.pi  # Convert [rad] to [deg].
  return error

def te(t_est, t_gt):
  """Translational Error.
  :param t_est: 3x1 ndarray with the estimated translation vector.
  :param t_gt: 3x1 ndarray with the ground-truth translation vector.
  :return: The calculated error.
  """
  assert (t_est.size == t_gt.size == 3)
  error = np.linalg.norm(t_gt - t_est)
  return error

def evaluate(groundtruth = None, prediction = None):
    assert (groundtruth and prediction is not None)

    gt = np.array(groundtruth).reshape(4,4)
    pre = np.array(prediction).reshape(4,4)

    gt_translation = gt[:3,3]
    pre_translation = pre[:3,3]

    gt_rotation = R.from_matrix(gt[:3,:3])
    pre_rotation = R.from_matrix(pre[:3,:3])

    dist = np.linalg.norm(gt_translation-pre_translation) 
 
    gt_rot_xyz = gt_rotation.as_euler('XYZ', degrees=True )
    pre_rot_xyz = pre_rotation.as_euler('XYZ', degrees=True)
    rot_diff_xyz = gt_rot_xyz - pre_rot_xyz 
    rot_err = re(pre_rotation.as_matrix(), gt_rotation.as_matrix())
    print(f"Distance {dist}")
    print(f"Rotation Difference: {rot_diff_xyz}")
    print(f"Rotation Error: {rot_err}")
    return dist, rot_diff_xyz, rot_err

def calc_pose_error(scene_id, prediction):
    gt_pose = scene_file_reader.get_object_poses(scene_id)
    prediction_file = os.path.join(prediction, scene_id, scene_file_reader.object_pose_file)
    obj_id, prediction_pose = load_pose(prediction_file) 
    evaluate(groundtruth=gt_pose[0][1], prediction=prediction_pose)

import numpy as np
import csv

def load_data(input_file):
    with open(input_file, 'r') as fp:
        return list(csv.reader(fp))

def create_statistic_data(annotation_path, output_file):
    ids = scene_file_reader.get_scene_ids()
    
    user_data = {}
    with open(output_file, 'w') as fp:
        for user in os.listdir(annotation_path):
            for id in ids:
                prediction_file = os.path.join(annotation_path, user, id, 'poses.yaml') 
                obj_id, pose = load_pose(prediction_file) 
                pose_matrix = np.array(pose).reshape(4,4)
                location = pose_matrix[:3,3]
                rot = R.from_matrix(pose_matrix[:3,:3])
                rot_xyz = rot.as_euler('XYZ', degrees=True)
                print(f"{user}, {id}, {location}, {rot_xyz}") 
                fp.write(f"{user}, {id}, {location}, {rot_xyz}\n") 

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Create User Study Evaluation.")
    parser.add_argument("-i", "--input_file", type=str, default='statistics.txt',
                        help="Input data file.")
    parser.add_argument("-o", "--output_file", type=str, default='statistics.txt',
                        help="Output data file")
    args = parser.parse_args()

    data = load_data(args.input_file)
    np_data = np.asarray(data)

    # calculate mean location for each scene
    scenes = np.unique(np_data[:,1])
    for scene in scenes:
        scene_data = np_data[np.where(np_data[:,1]==scene)]
        #translation
        location = np.asarray(scene_data[:,2:5]).astype(float)
        rotation = np.asarray(scene_data[:,5:]).astype(float)
        mean = np.mean(location,axis=0)
        std = np.std(location,axis=0)
        #rotation
        mean_rot = np.mean(rotation,axis=0)
        std_rot = np.std(rotation,axis=0)
        print(f"{scene},{mean},{std},{mean_rot},{std_rot}")
        for idx, item in enumerate(location):
            dist = te(location[idx], mean)
            print(f'user_{idx},{dist*1000}')
        

    # user_data = np_data[np.where(np_data[:,0]=='02_user')]
    # print("User")
    # for entry in user_data:
        # print(entry)
    # scene_data = np_data[np.where(np_data[:,1]=='01_tutorial')]
    # print("Scene:")
    # for entry in scene_data:
        # print(entry)
    
