import mathutils
import math
import numpy as np
import bpy
import glob
import os


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

    for item in objects:
        mesh = item[0].mesh.as_bpy_mesh()
        # name the object according to id
        obj_id = str(item[0].id)
        mesh.name = obj_id + "_" + item[0].name
        obj = bpy.data.objects.new(mesh.name, mesh)
        # transform to saved pose
        obj.matrix_world = mathutils.Matrix(np.asarray(item[1]).reshape(4, 4))
        r, g, b = item[0].color
        obj.color = (r/255., g/255., b/255., 1)
        obj["v4r_id"] = obj_id
        bpy.data.collections["objects"].objects.link(obj)


def set_alpha(value=0):
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
            camera_info = SCENE_FILE_READER.get_camera_info()
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
