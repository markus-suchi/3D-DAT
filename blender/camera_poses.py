import mathutils
import math
import numpy as np
import bpy
import glob

def get_poses(path_groundtruth, invert=False):                                
    with open(path_groundtruth) as fp:                          
        groundtruth = fp.readlines()                                
        groundtruth = [line.strip().split() for line in groundtruth]
                                                                
    trans = [line[1:4] for line in groundtruth]                 
    quat = [line[4:] for line in groundtruth]                   
                                                                
    poses = []                                              
    for i in range(len(groundtruth)):                           
        pose = np.zeros((4, 4))                                 
        pose[3, 3] = 1      
        pose_quat_np = np.array([quat[i][3],quat[i][0],quat[i][1],quat[i][2]], dtype=np.float32)
        pose_quat = mathutils.Quaternion(pose_quat_np).to_matrix()  
        print(pose_quat) 
        pose[:3, :3] = pose_quat
        pose[:3, -1] = trans[i]    
        if invert:  
            pose = np.linalg.inv(pose) 
        poses.append(pose)                                                                                                      
    return poses       

def get_blender_camera(K, width, height, sensor_width_in_mm):
    w = width
    h = height
    lens = K[0] *  sensor_width_in_mm / w
    shift_x = -(K[0,2] / w - 0.5)
    shift_y = (K[1,2] - 0.5 * h) / w
    return lens, shift_x, shift_y     
    
def get_blender_camera_fovx(K, width, height):
    w = width
    h = height
    fovx = 2 * math.atan( w / (2 * K[0,0]))
    fovy = 2 * math.atan( h / (2 * K[1,1]))
    shift_x = -(K[0,2] / w - 0.5)
    shift_y = (K[1,2] - 0.5 * h) / w
    return fovx, fovy, shift_x, shift_y     

def add_cameras(camera_path = "", camera_rgb_path = "", invert=False): 
    camera_poses = get_poses(camera_path, invert)
    
    groundtruth_to_blender = np.array([[1, 0, 0, 0],
                                       [0, -1, 0, 0],
                                       [0, 0, -1, 0],
                                       [0, 0, 0, 1]])

    # remove old cameras    
    if "cameras" in bpy.data.collections:
        for o in bpy.data.collections["cameras"].objects:
            print(o.name)
            if "Camera_" in o.name:
                bpy.data.objects.remove(o, do_unlink=True)
    rgb = []
    rgb = glob.glob(camera_rgb_path + "*.png")
    rgb.sort()
    
    K = np.asarray([[923.101, 0 , 629.313476], 
                    [0, 922.568, 376.28814687], 
                    [0, 0, 1]])                     
    sensor_width_in_mm = 2.7288
    width = 1280
    height = 720

    for i in range(len(camera_poses)):
      name = "Camera_" + str(i)
      
      if "cameras" not in bpy.data.collections:
          cam_collection = bpy.ops.collection.create(name  = "cameras")
          bpy.context.scene.collection.children.link(bpy.data.collections["cameras"])

      if bpy.data.collections["cameras"].objects.get(name):
          assert(False, "Tried to overwrite camera.")
      else:      
          cam1 = bpy.data.cameras.new(name)
          obj_camera = bpy.data.objects.new(name, cam1)
          camera_poses[i] = camera_poses[i].dot(groundtruth_to_blender)
          location = camera_poses[i][:3,-1]
          rotation = camera_poses[i][:3, :3]
          obj_camera.location = [location[0], location[1], location[2]]
          obj_camera.rotation_euler = mathutils.Matrix(rotation).to_euler()
        
          lens, shift_x, shift_y = get_blender_camera(K, width, height, sensor_width_in_mm)
          obj_camera.data.lens_unit = 'MILLIMETERS'
          obj_camera.data.lens = lens
          obj_camera.data.shift_x = shift_x
          obj_camera.data.shift_y = shift_y
          obj_camera.data.display_size = 0.05
          obj_camera.data.sensor_width = sensor_width_in_mm
          
          # set background image
          img = bpy.data.images.load(rgb[i])
          obj_camera.data.show_background_images = True
          bg = obj_camera.data.background_images.new()
          bg.image = img
          bg.alpha = 1.0
          bpy.data.collections["cameras"].objects.link(obj_camera)

camera_path = "/home/markus/temp/TestDataset/scenes/006/groundtruth_handeye.txt" 
scene_path = "/home/markus/temp/TestDataset/scenes/006/rgb/"

add_cameras(camera_path = camera_path, camera_rgb_path = scene_path)
