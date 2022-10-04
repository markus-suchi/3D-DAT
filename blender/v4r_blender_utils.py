import mathutils
import math
import numpy as np
import bpy
import glob
import yaml
import os
from collections import Counter

from v4r_dataset_toolkit import autoalign
# TODO: get local used parameters like SCENE_FILE_READER and SCENE_MESH 
#       over here


# https://blender.stackexchange.com/questions/45138/buttons-for-custom-properties-dont-refresh-when-changed-by-other-parts-of-the-s
# Auto refresh for custom collection property does not work without tagging a redraw
def tag_redraw(context, space_type="PROPERTIES", region_type="WINDOW"):
    """ Redraws given windows area of specific type """
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.spaces[0].type == space_type:
                for region in area.regions:
                    if region.type == region_type:
                        region.tag_redraw()

def tag_redraw_all():
    for area in bpy.context.screen.areas:
        area.tag_redraw()


def load_objects(SCENE_FILE_READER, id):
    objects = []
    if(SCENE_FILE_READER):
        objects = SCENE_FILE_READER.get_object_poses(id)

    if "objects" not in bpy.data.collections:
        obj_collection = bpy.ops.collection.create(name="objects")
        bpy.context.scene.collection.children.link(
            bpy.data.collections["objects"])
    else:
        # Remove previous loaded objects
        # TODO: do not reimport already loaded objects, just reset position
        for o in bpy.data.collections["objects"].objects:
            m = bpy.data.meshes[o.name]
            bpy.data.objects.remove(o, do_unlink=True)
            if m.users < 1:
                bpy.data.meshes.remove(m, do_unlink=True)

    loaded_objects = bpy.context.scene.v4r_infos.object_list
    loaded_objects.clear()
    for item in objects:
        mesh = item[0].mesh.as_bpy_mesh()
        # name the object according to id
        obj_id = str(item[0].id)
        mesh.name = obj_id + "_" + item[0].name
        obj = bpy.data.objects.new(mesh.name, mesh)
        # transform to saved pose
        object_pose = np.asarray(item[1])
        obj.matrix_world = mathutils.Matrix(object_pose.reshape(4, 4))
        r, g, b = item[0].color
        obj.color = (r/255., g/255., b/255., 1)
        obj["v4r_id"] = obj_id
        obj.lock_scale = [True, True, True]
        bpy.data.collections["objects"].objects.link(obj)
        add = loaded_objects.add()
        add.id = obj_id
        add.pose = object_pose


def save_pose(SCENE_FILE_READER, id):
    full_path = os.path.join(SCENE_FILE_READER.root_dir,
                             SCENE_FILE_READER.annotation_dir,
                             id,
                             SCENE_FILE_READER.object_pose_file)

    print("Saving poses to: " + full_path)
    loaded_objects = bpy.context.scene.v4r_infos.object_list
    loaded_objects.clear()
    output_list = []

    if "objects" not in bpy.data.collections:
        # no object collection
        return

    for obj in bpy.data.collections['objects'].objects:
        print("Saving object %s, id %s." % (obj.name, obj["v4r_id"]))
        pose = np.zeros((4, 4))
        pose[:, :] = obj.matrix_world
        pose = pose.reshape(-1)
        output_list.append(
            {"id": obj["v4r_id"], "pose": pose.tolist()})
        add = loaded_objects.add()
        add.id = obj["v4r_id"]
        add.pose = pose
    
    with open(full_path, 'w') as f:
        yaml.dump(output_list, f, default_flow_style=False)

    # update loaded object list


def set_alpha(value=0):
    if "objects" in bpy.data.collections:
        for o in bpy.data.collections["objects"].objects:
            o.color[3] = value


def load_cameras(SCENE_FILE_READER, id):
    # Removing cameras based on collection rather than name
    # Could still use generated name to make sure
    camera_poses = SCENE_FILE_READER.get_camera_poses(id)
    groundtruth_to_blender = np.array([[1, 0, 0, 0],
                                       [0, -1, 0, 0],
                                       [0, 0, -1, 0],
                                       [0, 0, 0, 1]])

    # remove old cameras
    if "cameras" in bpy.data.collections:
        for o in bpy.data.collections["cameras"].objects:
            if "Camera_" in o.name:
                c = bpy.data.cameras[o.name]
                i = bpy.data.images[c.background_images[0].image.name]
                bpy.data.objects.remove(o, do_unlink=True)
                bpy.data.cameras.remove(c, do_unlink=True)
                bpy.data.images.remove(i, do_unlink=True)

    # SCENE_FILE_READER should support loading images for blender
    camera_rgb_path = os.path.join(
        SCENE_FILE_READER.root_dir, SCENE_FILE_READER.scenes_dir,
        id,
        SCENE_FILE_READER.rgb_dir)
    rgb = []
    rgb = glob.glob(camera_rgb_path + "/*.png")
    rgb.sort()

    # no active object
    bpy.ops.object.select_all(action='DESELECT')
    if camera_poses:
        if "cameras" not in bpy.data.collections:
            cam_collection = bpy.ops.collection.create(name="cameras")
            bpy.context.scene.collection.children.link(
                bpy.data.collections["cameras"])

    for i in range(len(camera_poses)):
        name = "Camera_" + str(i)

        if bpy.data.collections["cameras"].objects.get(name):
            assert(False, "Tried to overwrite camera.")
        else:
            cam = bpy.data.cameras.new(name)
            obj_camera = bpy.data.objects.new(name, cam)
            camera_pose = camera_poses[i].tf.dot(groundtruth_to_blender)
            location = camera_pose[:3, -1]
            rotation = camera_pose[:3, :3]
            obj_camera.location = [location[0], location[1], location[2]]
            obj_camera.rotation_euler = mathutils.Matrix(rotation).to_euler()

            # using blender camera with focal length in millimeters
            camera_info = SCENE_FILE_READER.get_camera_info_scene(id)
            if camera_info.sensor_width:
                obj_camera.data.lens_unit = 'MILLIMETERS'
                obj_camera.data.lens = camera_info.lens()
                obj_camera.data.sensor_width = camera_info.sensor_width
            else:
                # using blender camera with FOV(x)
                obj_camera.data.lens_unit = 'FOV'
                obj_camera.data.angle = camera_info.fov()

            # common camera properties
            obj_camera.data.shift_x = camera_info.shift_x()
            obj_camera.data.shift_y = camera_info.shift_y()
            obj_camera.data.display_size = 0.05

            # set background image
            img = bpy.data.images.load(rgb[i])
            obj_camera.data.show_background_images = True
            bg = obj_camera.data.background_images.new()
            bg.image = img
            bg.alpha = 1.0
            obj_camera.hide_select = True
            bpy.data.collections["cameras"].objects.link(obj_camera)

            # set render output for camera
            for scene in bpy.data.scenes:
                scene.render.resolution_x = camera_info.width
                scene.render.resolution_y = camera_info.height


def set_camera(camera):
    for area in bpy.context.screen.areas:
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                space.use_local_camera = True
                space.camera = camera


def get_cam_views():
    cam_views = []
    for area in bpy.context.screen.areas:
        for space in area.spaces:
            if space.type == 'VIEW_3D':
                current_perspective = space.region_3d.view_perspective
                if current_perspective == 'CAMERA':
                    cam_views.append(space.region_3d)
    return cam_views

def load_reconstruction(SCENE_FILE_READER, id):
   return SCENE_FILE_READER.get_reconstruction_align(id)


def remove_reconstruction_visual():
    reconstruction_visual_name = "reconstruction" 

    if(reconstruction_visual_name in bpy.data.objects):
        o = bpy.data.objects[reconstruction_visual_name]
        bpy.data.objects.remove(o, do_unlink=True)
    
        if(reconstruction_visual_name in bpy.data.meshes):
            m = bpy.data.meshes[reconstruction_visual_name]
            if m.users < 1:
                bpy.data.meshes.remove(m, do_unlink=True)
 

def load_reconstruction_visual(SCENE_FILE_READER, id):
    # add reconstruction visuals as blender obj
    reconstruction_visual_name = "reconstruction" 

    if "reconstruction" not in bpy.data.collections:
        obj_collection = bpy.ops.collection.create(name="reconstruction")
        bpy.context.scene.collection.children.link(
            bpy.data.collections["reconstruction"])

    remove_reconstruction_visual()
  
    new_m = SCENE_FILE_READER.get_reconstruction_visual(id)
    if(new_m):
        print("Creating new reconstruction mesh.")
        mesh = new_m.as_bpy_mesh()
        mesh.name = reconstruction_visual_name
        # name the object according to id
        obj = bpy.data.objects.new(reconstruction_visual_name, mesh)
        obj.lock_scale = [True, True, True]
        obj.hide_select = True
        bpy.data.collections["reconstruction"].objects.link(obj)
 

def has_active_object_id():
    obj = bpy.context.active_object
    return (obj and obj in bpy.context.selected_objects and "v4r_id" in obj)


def align_current_object(SCENE_FILE_READER, SCENE_MESH):
    if has_active_object_id(): 
        active = bpy.context.active_object
        current_id = active["v4r_id"]
        print(f"Align object {current_id}")
        current_pose = active.matrix_world
        current_mesh = SCENE_FILE_READER.object_library[current_id].mesh.as_o3d()
        pose, info = autoalign.auto_align(current_mesh, SCENE_MESH,init_pose=current_pose)
        active.matrix_world = mathutils.Matrix(pose)


def has_scene_changed():
    loaded_objects = bpy.context.scene.v4r_infos.object_list
    if not loaded_objects:
        print("Nothing was loaded yet")
        return False

    if bpy.data.collections.get("objects"):
        objects_available = [(item.get("v4r_id"), numpy_to_tuple(np.asarray(item.matrix_world).flatten())) 
                              for item in bpy.data.collections.get("objects").objects 
                              if item.get("v4r_id")]

        objects_loaded = [(item.id, numpy_to_tuple(np.asarray(item.pose))) 
                          for item in loaded_objects]

        return Counter(objects_available) != Counter(objects_loaded)
    else:
        print("No objects")
        return False


def numpy_to_tuple(x):
    return tuple(map(tuple,[np.round(x,5)]))

