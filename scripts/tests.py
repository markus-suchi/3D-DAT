import argparse
import configparser
import os
import numpy as np

import v4r_dataset_toolkit as v4r


def main():
    # run data loader with command line parameters
    parser = argparse.ArgumentParser(
        "Example: loading dataset items.")
    parser.add_argument("-c", "--config", type=str, default="../objects/objects.yaml",
                        help="Path to dataset information")
    args = parser.parse_args()

    # Test Scene File Loader
    print("--- SceneFileReader.")
    cfg = configparser.ConfigParser()
    cfg.read(args.config)
    reader = v4r.io.SceneFileReader(cfg['General'])
    object_lib = reader.readObjectLibrary()
    print(reader)

    # Test MeshReader
    print("--- MeshReader")
    mesh_reader = v4r.io.MeshReader('/temp/dummy.ply')
    print(mesh_reader)

    # Test Object Library
    # single object access
    print("--- ObjectLibrary")
    print("----- Single access.")
    obj = object_lib[1]
    print(obj)
    # list object access
    print("----- Multi access with indices.")
    for obj in object_lib.as_list([1, 2]):
        print(obj.id, obj.name, obj.mesh.file)
    print("----- Multi access without indices.")
    for obj in object_lib.as_list():
        print(obj.id, obj.name, obj.mesh.file)
    print("----- Filter by class.")
    # filter by class
    for obj in [val for val in object_lib.values() if val.class_id in ['bottle']]:
        print(obj.id, obj.name, obj.class_id)

    # Camera intrinsics
    print("--- CameraInfo")
    cam = v4r.io.CameraInfo('testcam', 1, 2, 3, 4, 5, 6)
    print(cam)
    print(cam.as_numpy3x3())
    print(np.shape(cam.as_numpy3x3()))
    print(cam.sensor_width_mm)
    print("--- CameraInfo from reader")
    cam = reader.readCameraInfo()
    print(cam)
    print(cam.as_numpy3x3())

    # Pose
    print("--- Pose")
    p1 = v4r.io.Pose(np.array(np.eye(4)))
    p2 = v4r.io.Pose([0, 0, 0, 1, 0, 0, 0])
    p3 = v4r.io.Pose()
    print(f'p1:\n{p1}\np2:\n{p2}\np3:\n{p3}\n')

    # SceneIds
    print("--- Scene Ids")
    print(reader.getSceneIds())


if __name__ == "__main__":
    main()
