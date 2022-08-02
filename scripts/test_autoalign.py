import argparse
import os
import v4r_dataset_toolkit as v4r
import open3d as o3d
import copy
import numpy as np
import yaml

def draw_registration_result_original_color(source, target, transformation):
    source_temp = copy.deepcopy(source)
    target_temp = copy.deepcopy(target)
    source_temp.transform(transformation)
    o3d.visualization.draw_geometries([source_temp, target_temp])


def save_poses(list_poses, scene_id):
    full_path = "/home/markus/temp/BopTestDataset/annotations/"+scene_id+"/poses.yaml"
    output_list = []
    for i in list_poses:
        pose = i[1]
        output_list.append(
            {"id": i[0].id, "pose": pose})

    with open(full_path, 'w') as f:
        yaml.dump(output_list, f, default_flow_style=False)


if __name__ == "__main__":

    #o3d.utility.set_verbosity_level(o3d.utility.VerbosityLevel.Debug)
    scene_id = '003'
    object_id = '4'

    parser = argparse.ArgumentParser(
        'Align object with given id to given scene.')
    parser.add_argument("-s", "--scene_id", type=str, default=scene_id,
                        help="Target triangles for simpilfication.")
    parser.add_argument("-o", "--object_id", type=str, default=object_id,
                        help="Target triangles for simpilfication.")
    args = parser.parse_args()

    scene_id = args.scene_id
    object_id = args.object_id

    reconstruction_file = "/home/markus/temp/BopTestDataset/annotations/" + \
        scene_id+"/reconstruction.ply"
    dataset = "/home/markus/temp/BopTestDataset/config_bop.cfg"

    print("Read reconstruction")
    pcd_scene = o3d.io.read_triangle_mesh(reconstruction_file)
    print("Read object mesh")
    scene_file_reader = v4r.io.SceneFileReader.create(dataset)
    obj_library = scene_file_reader.get_object_library()
    object_mesh = obj_library[object_id].mesh.as_o3d()
    list_poses = scene_file_reader.get_object_poses(scene_id)
    object_pose = np.eye(4)
    for i in list_poses:
        if i[0].id == object_id:
            print("found object")
            object_pose = np.resize(i[1], (4, 4))

    draw_registration_result_original_color(
        object_mesh, pcd_scene, object_pose)

    print("object_pose")
    print(object_pose)

    print("Auto Align")
    trans, info = v4r.autoalign.auto_align(
        object_mesh, pcd_scene, init_pose=object_pose)
    print("ready")

    # set new pose for object
    for i in list(list_poses):
        if i[0].id == object_id:
            print("found object")
            i[1] = trans.reshape(-1).tolist()

    print("object_pose")
    print(trans)

    save_poses(list_poses, scene_id)
