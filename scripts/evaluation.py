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
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns

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
 
    rot_diff_xyz = gt_rot_xyz - pre_rot_xyz 
    rot_err = re(pre_rotation.as_matrix(), gt_rotation.as_matrix())
    print(f"Distance {dist}")
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
    parser.add_argument("-i", "--input_dir", type=str, default='statistics.txt',
                        help="Input data dir.")
    parser.add_argument("-o", "--output_dir", type=str, default='statistics.txt',
                        help="Output data dir")
    args = parser.parse_args()


    auto = True

    #Consent data plots
    consent_data = os.path.join(args.input_dir, 'statistics_consent.txt')
    data = load_data(consent_data)
    np_data = np.asarray(data)

    data = []
    # calculate mean location for each scene
    scenes = np.unique(np_data[:,1])
    for scene in scenes:
        scene_data = np_data[np.where(np_data[:,1]==scene)]
        #translation
        users = scene_data[:,0]
        object_id = scene_data[0,2]
        location = np.asarray(scene_data[:,3:6]).astype(float)
        rotation = np.asarray(scene_data[:,6:]).astype(float).reshape(-1,3,3)
        mean = np.mean(location,axis=0)
        std = np.std(location,axis=0)
        #rotation
        mean_rot = R.from_matrix(rotation).mean().as_matrix().reshape(3,3)
        for idx, item in enumerate(scene_data):
            dist = te(location[idx], mean)
            rot_err = re(rotation[idx], mean_rot)
            row = [users[idx], scene, int(object_id), dist*1000, rot_err]
            data.append(row)

        # write out means for visualization
        mean_pose = np.eye(4)
        mean_pose[:3,:3] = mean_rot
        mean_pose[:3,3] = mean
        mean_file = os.path.join(args.output_dir,'mean_user', scene,"poses.yaml")
        os.makedirs(os.path.dirname(mean_file), exist_ok=True)
        with open(mean_file, 'w') as fp:
            yaml.dump([{"id": int(object_id), "pose": mean_pose.reshape(-1).tolist()}], fp, default_flow_style=False)

    df = pd.DataFrame(data, columns = ['user', 'scene', 'object', 'translation [mm]', 'rotation [degrees]'])
    print(df)
    # User 
    fig, ax = plt.subplots()
    df_long = pd.melt(df, id_vars = ['user'], value_vars = ['translation [mm]','rotation [degrees]'], var_name = ['scene'])
    ax = sns.boxplot(data=df_long,x='value', y='user', hue='scene', fliersize=1,palette="Blues", width = 0.5,
                     medianprops=dict(color="red", alpha=0.7), linewidth=0.7, autorange = auto, whis=100.)
    plt.suptitle("User Consent")
    ax.get_legend().set_title('')
    ax.set(xlabel="error")
    save_file = os.path.join(args.output_dir, '3DSADT-user-consent.png')
    plt.tight_layout()
    plt.savefig(save_file, dpi=300)


    # Scene 
    fig, ax = plt.subplots()
    df_long = pd.melt(df, id_vars = ['scene'], value_vars = ['translation [mm]','rotation [degrees]'], var_name = ['user'])
    ax = sns.boxplot(data=df_long,x='value', y='scene', hue='user', fliersize=1,palette="Blues", width = 0.5,
                     medianprops=dict(color="red", alpha=0.7), linewidth=0.7, autorange = auto, whis=100.)
    plt.suptitle("Scene Consent")
    ax.get_legend().set_title('')
    ax.set(xlabel="error")
    save_file = os.path.join(args.output_dir, '3DSADT-scene-consent.png')
    plt.tight_layout()
    plt.savefig(save_file, dpi=300)



    #Groundtruth data plots
    synthetic_data = os.path.join(args.input_dir, 'statistics_gt.txt')
    data = load_data(synthetic_data)
    np_data = np.asarray(data)

    data = []
    scenes = np.unique(np_data[:,1])
    for scene in scenes:
        scene_data = np_data[np.where(np_data[:,1]==scene)]
        #translation
        users = scene_data[:,0]
        object_id = scene_data[:,2]
        for idx, item in enumerate(scene_data):
            data.append([users[idx], scene, scene_data[idx,2].astype(float)*1000, scene_data[idx,3].astype(float)])

    df = pd.DataFrame(data, columns = ['user', 'scene', 'translation [mm]', 'rotation [degrees]'])
    print(df)

    # User 
    fig, ax = plt.subplots()
    df_long = pd.melt(df, id_vars = ['user'], value_vars = ['translation [mm]','rotation [degrees]'], var_name = ['scene'])
    ax = sns.boxplot(data=df_long,x='value', y='user', hue='scene', fliersize=1,palette="Greens", width = 0.5,
                     medianprops=dict(color="red", alpha=0.7), linewidth=0.7, autorange = auto, whis=100.)
    plt.suptitle("User Synthetic Groundtruth", )
    ax.get_legend().set_title('')
    ax.set(xlabel="error")
    save_file = os.path.join(args.output_dir, '3DSADT-user-gt.png')
    plt.tight_layout()
    plt.savefig(save_file, dpi=300)


    # Scene 
    fig, ax = plt.subplots()
    df_long = pd.melt(df, id_vars = ['scene'], value_vars = ['translation [mm]','rotation [degrees]'], var_name = ['user'])
    ax = sns.boxplot(data=df_long,x='value', y='scene', hue='user', fliersize=1,palette="Greens", width = 0.5,
                     medianprops=dict(color="red", alpha=0.7), linewidth=0.7, autorange = auto, whis=100.)
    plt.suptitle("Scene Synthetic Groundtruth")
    ax.get_legend().set_title('')
    ax.set(xlabel="error")
    save_file = os.path.join(args.output_dir, '3DSADT-scene-gt.png')
    plt.tight_layout()
    plt.savefig(save_file, dpi=300)

