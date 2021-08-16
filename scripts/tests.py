import argparse
import configparser
import os
import numpy as np

import v4r_dataset_toolkit as v4r

# These calls should be refactored into unittests
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
    object_lib = reader.get_object_library()
    print(reader)

    # Test Object Library
    # single object access
    print("--- ObjectLibrary")
    print("----- Single access.")
    print("object_lib[1]")
    obj = object_lib[1]
    print(obj)
    print("object_lib[12]")
    obj = object_lib[12]
    print(obj)
    # list object access
    print("----- Multi access with indices.")
    print("for obj in object_lib.as_list([1,2])")
    for obj in object_lib.as_list([1, 2]):
        print(obj.id, obj.name, obj.mesh.file)
    print("----- Multi access without indices.")
    print("for obj in object_lib.as_list()")
    for obj in object_lib.as_list():
        #mesh file may not be supported
        #TODO: May make a property which checks this in objects
        if obj.mesh:
            print(obj.id, obj.name, obj.mesh.file)
        else:
            print(obj.id, obj.name, None)
    print("----- Filter by class.")
    print("for obj in [val for val in object_lib.values() if val.class_id in ['bottle']]")
    # filter by class
    for obj in [val for val in object_lib.values() if val.class_id in ['bottle']]:
        print(obj.id, obj.name, obj.class_id)

    # MeshReader
    print("--- MeshReader")
    print("--- Invalid")
    try:
        mesh = v4r.meshreader.MeshReader("/temp/not_there.ply")
    except FileNotFoundError as err:
        print(err)

    # Camera intrinsics
    print("--- CameraInfo")
    cam = v4r.io.CameraInfo('testcam', 1, 2, 3, 4, 5, 6)
    print(cam)
    print(cam.as_numpy3x3())
    print(np.shape(cam.as_numpy3x3()))
    print(cam.sensor_width_mm)
    print("---- CameraInfo from reader")
    print("reader.get_camera_info()")
    cam = reader.get_camera_info()
    print(cam)
    print(cam.as_numpy3x3())

    # SceneIds
    print("--- Scene Ids")
    print("reader.get_scene_ids")
    scene_ids = reader.get_scene_ids()
    print(scene_ids)

    # Pose
    print("--- Pose")
    p1 = v4r.io.Pose(np.array(np.eye(4)))
    p2 = v4r.io.Pose([0, 0, 0, 1, 0, 0, 0])
    p3 = v4r.io.Pose()
    print(f'p1:\n{p1}\np2:\n{p2}\np3:\n{p3}\n')
    print("---- Camera poses")
    print("reader.get_camera_poses(scene_ids[0]")
    cam_poses = reader.get_camera_poses(scene_ids[0])
    ccams = np.shape(cam_poses)[0]
    print(f"---- {ccams} Poses (camera) from reader")
    print(f"----- Cam 1:\n{cam_poses[0]}")
    print(f"----- Cam {ccams}:\n{cam_poses[ccams-1]}")


if __name__ == "__main__":
    main()
