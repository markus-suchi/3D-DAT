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

def load_pose(filepath):
    with open(filepath) as fp:
        for items in (yaml.load(fp, Loader=yaml.FullLoader)):
            id = items.get("id")
            pose = items.get("pose")
            if not pose:
                print(f"No pose in file {filepath}") 
            else:
                return (id, pose)

def evaluate(groundtruth = None, prediction = None):
    if groundtruth == None or prediction == None:
        print("For comparision groundtruth and prediction poses are required.")
        return

    gt = np.array(groundtruth).reshape(4,4)
    pre = np.array(prediction).reshape(4,4)

    gt_translation = gt[:3,3]
    pre_translation = pre[:3,3]

    gt_rotation = R.from_matrix(gt[:3,:3])
    pre_rotation = R.from_matrix(pre[:3,:3])

    # print("GT ----")
    # print(gt)
    # print("----")
    # print(gt_translation)
    # print("----")
    # print(gt_rotation.as_matrix())
    # print("PRE ----")
    # print(pre)
    # print("----")
    # print(pre_translation)
    # print("----")
    # print(pre_rotation.as_matrix())
    dist = np.linalg.norm(gt_translation-pre_translation) 
 
    gt_rot_xyz = gt_rotation.as_euler('XYZ', degrees=True )
    pre_rot_xyz = pre_rotation.as_euler('XYZ', degrees=True)

    # print("gt_euler_rot")
    # print(gt_rot_xyz)
    # print("pre_euler_rot")
    # print(pre_rot_xyz)
    # print("gt_euler_quat")
    # print(gt_rotation.as_quat())
    # print("pre_euler_quat")
    # print(pre_rotation.as_quat())
    rot_diff = gt_rot_xyz - pre_rot_xyz 
    print(f"Distance {dist}")
    print(f"Rotation Difference: {rot_diff}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Visualize annotated data.")
    parser.add_argument("-c", "--config", type=str, required=True,
                        help="Path to dataset configuration.")
    parser.add_argument("-p", "--prediction", type=str, required=True,
                        help="Path to directory of prediction.")
    parser.add_argument("-s", "--scene_id", type=str, default='',
                        help="Scene identifier to evaluate.")
    args = parser.parse_args()

    scene_file_reader = v4r.io.SceneFileReader.create(args.config)

    if args.scene_id:
        print(f'Evaluating scene {args.scene_id}:')
        gt_pose = scene_file_reader.get_object_poses(args.scene_id)
        prediction_file = os.path.join(args.prediction, args.scene_id, "poses.yaml")
        obj_id, prediction_pose = load_pose(prediction_file) 
        evaluate(groundtruth=gt_pose[0][1], prediction=prediction_pose)
