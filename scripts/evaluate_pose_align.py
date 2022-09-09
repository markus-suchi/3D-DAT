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


def load_pose(filepath):
    with open(filepath) as fp:
        for items in (yaml.load(fp, Loader=yaml.FullLoader)):
            id = items.get("id")
            pose = items.get("pose")
            if not pose:
                print(f"No pose in file {filepath}")
            else:
                return (id, pose)


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


def evaluate(groundtruth=None, prediction=None):
    assert (groundtruth and prediction is not None)

    gt = np.array(groundtruth).reshape(4, 4)
    pre = np.array(prediction).reshape(4, 4)

    gt_translation = gt[:3, 3]
    pre_translation = pre[:3, 3]

    gt_rotation = R.from_matrix(gt[:3, :3])
    pre_rotation = R.from_matrix(pre[:3, :3])

    dist = np.linalg.norm(gt_translation-pre_translation)

    rot_err = re(pre_rotation.as_matrix(), gt_rotation.as_matrix())
    return dist, rot_err


def calc_groundtruth_data(scene_id, prediction):
    gt_pose = scene_file_reader.get_object_poses(scene_id)
    prediction_file = os.path.join(
        prediction, scene_id, scene_file_reader.object_pose_file)
    obj_id, prediction_pose = load_pose(prediction_file)
    return evaluate(groundtruth=gt_pose[0][1], prediction=prediction_pose)


def create_consent_data(annotation_path, output_file):
    fmt_str = '%s'+',%s'*14
    ids = scene_file_reader.get_scene_ids()
    with open(output_file, 'w') as fp:
        for user in sorted(os.listdir(annotation_path)):
            for id in ids:
                prediction_file = os.path.join(
                    annotation_path, user, id, 'poses.yaml')
                obj_id, pose = load_pose(prediction_file)
                pose_matrix = np.array(pose).reshape(4, 4)
                location = pose_matrix[:3, 3]
                rotation = pose_matrix[:3, :3]
                arr = np.array([user, id, obj_id])
                arr = np.hstack((arr, location.flatten()))
                arr = np.hstack((arr, rotation.flatten()))
                np.savetxt(fp, [arr], fmt=fmt_str, delimiter=",")


def create_groundtruth_data(scenes, prediction_path, output_file):
    fmt_str = '%s'+',%s'*3
    with open(output_file, 'w') as fp:
        for scene_id in scenes:
            for user in sorted(os.listdir(prediction_path)):
                prediction = os.path.join(prediction_path, user)
                dist, rot = calc_groundtruth_data(scene_id, prediction)
                arr = np.array([user, scene_id, dist, rot])
                np.savetxt(fp, [arr], fmt=fmt_str, delimiter=",")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Visualize annotated data.")
    parser.add_argument("-c", "--config", type=str, required=True,
                        help="Path to dataset configuration.")
    parser.add_argument("-p", "--prediction", type=str, required=True,
                        help="Path to directory of prediction.")
    parser.add_argument("-o", "--output_dir", type=str, default='',
                        help="Output directory.")
    args = parser.parse_args()

    scene_file_reader = v4r.io.SceneFileReader.create(args.config)

    groundtruth_scenes = ['1',
                          '2', '3', '4']

    #gt_file = os.path.join(args.output_dir, 'statistics_gt.txt')
    #create_groundtruth_data(groundtruth_scenes, args.prediction, gt_file)
    consent_file = os.path.join(args.output_dir, 'statistics_consent.txt')
    create_consent_data(args.prediction, consent_file)
