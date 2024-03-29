
import argparse
import cv2
import numpy as np
import os
import sys
from tqdm import tqdm
import trimesh
import yaml
import open3d as o3d
import copy
import v4r_dataset_toolkit as v4r
# This needs to be imported before pyrender to disable
# antialiasing in mask generation
from v4r_dataset_toolkit import pyrender_wrapper
import pyrender
from PIL import Image

groundtruth_to_pyrender = np.array([[1, 0, 0, 0],
                                    [0, -1, 0, 0],
                                    [0, 0, -1, 0],
                                    [0, 0, 0, 1]])


def project_mesh_to_2d(models, cam_poses, model_colors, intrinsic):
    # --- PyRender scene setup ------------------------------------------------
    scene = pyrender.Scene(bg_color=[0, 0, 0])

    seg_node_map = {}
    # Add model mesh
    for model_idx, model in enumerate(models):
        # pyrender render flag SEG does not allow to ignore culling backfaces
        # Instead set color for the mask on the trimesh mesh
        visual = trimesh.visual.create_visual(mesh=model)
        visual.face_colors = model_colors[model_idx]
        model.visual = visual
        pyr_mesh = pyrender.Mesh.from_trimesh(model, smooth=False)
        nm = pyrender.Node(mesh=pyr_mesh)
        scene.add_node(nm)

    # Add camera
    camera = pyrender.camera.IntrinsicsCamera(intrinsic.fx,
                                              intrinsic.fy,
                                              intrinsic.cx,
                                              intrinsic.cy)
    nc = pyrender.Node(camera=camera, matrix=np.eye(4))
    scene.add_node(nc)
    nl = pyrender.Node(matrix=np.eye(4))
    scene.add_node(nl)

   # --- Rendering -----------------------------------------------------------
    renders = []
    r = pyrender.OffscreenRenderer(intrinsic.width, intrinsic.height)
    for cam_pose in tqdm(cam_poses, desc="Reprojection rendering"):
        # different coordinate system when using renderer
        cam_pose = cam_pose.dot(groundtruth_to_pyrender)
        # Render
        scene.set_pose(nc, pose=cam_pose)
        scene.set_pose(nl, pose=cam_pose)

        img, depth = r.render(
            scene,
            flags=pyrender.RenderFlags.SKIP_CULL_FACES |
            pyrender.RenderFlags.FLAT)
        renders.append(img)
    return renders


def get_masks_from_render(colors, image):
    masks = []
    img = image
    for idx, color in enumerate(colors):
        np_color = np.array(color)
        if np.shape(image)[2] == 4:
            img = cv2.cvtColor(image, cv2.COLOR_BGRA2RGB)
        else:
            img = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        mask = (img == np_color).all(-1)
        masks.append(mask)
    return masks


def get_bbox_from_masks(masks):
    bboxes = []
    for mask in masks:
        if np.any(mask):
            rows = np.any(mask, axis=1)
            cols = np.any(mask, axis=0)
            rmin, rmax = np.where(rows)[0][[0, -1]]
            cmin, cmax = np.where(cols)[0][[0, -1]]
            bboxes.append((cmin, rmin, cmax, rmax))
        else:
            bboxes.append(None)
    return bboxes


def put_text(text, img, x, y, color):
    (w, h), _ = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 1, 1)

    img = cv2.rectangle(img, (x, y - 30), (x + w, y), color, -1)
    img = cv2.putText(img, text, (x, y - 8),
                      cv2.FONT_HERSHEY_SIMPLEX, 1, [255, 255, 255], 1)


def load_object_models(scene_file_reader):
    oriented_models = []
    # Load poses
    objects = scene_file_reader.get_object_poses(args.scene_id)
    for object in tqdm(objects, desc="Loading objects"):
        scene_object = scene_file_reader.object_library[object[0].id]
        model = scene_object.mesh.as_trimesh()
        model.apply_transform(np.array(object[1]).reshape(4, 4))
        oriented_models.append(model)
    return oriented_models


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        "Reproject models to create annotation images.")
    parser.add_argument("-d", "--dataset", type=str, required=True,
                        help="Path to dataset configuration.")
    parser.add_argument("-s", "--scene_id", type=str, required=True,
                        help="Scene identifier to visualize.")
    parser.add_argument("-b", "--background", action='store_true',
                        help="Enable scene background.")
    parser.add_argument("-a", "--alpha", type=float, default=0.5,
                        help="Overlay alpha for scene background.")
    parser.add_argument("-o", "--output", type=str, default='',
                        help="Output directory for masked images.")
    parser.add_argument("-v", "--visualize", action='store_true',
                        help="Visualize scene and optionally save to file.")
    parser.add_argument("-r", "--rotate", action='store_true', default='',
                        help="Rotate image.")
    args = parser.parse_args()

    if args.output:
        if not os.path.exists(args.output):
            print(f"Output path {args.output} does not exist.")
            sys.exit()

    if not args.output and not args.visualize:
        print("You have to specify option --output or --visualize or both.\n")
        parser.print_help()
        sys.exit(1)

    scene_file_reader = v4r.io.SceneFileReader.create(args.dataset)
    camera_poses = scene_file_reader.get_camera_poses(args.scene_id)
    intrinsic = scene_file_reader.get_camera_info_scene(args.scene_id)
    objects = scene_file_reader.get_object_poses(args.scene_id)
    oriented_models = load_object_models(scene_file_reader)

    model_colors = []
    if args.visualize:
        for object in objects:
            # random color
            color = np.random.randint(256, size=3)
            color = [int(color[0]), int(color[1]), int(color[2])]
            model_colors.append(color)
    else:
        for i, object in enumerate(objects):
            i += 1
            model_colors.append([i, 0, 0])

    orig_imgs = scene_file_reader.get_images_rgb(args.scene_id)
    camera_poses = [pose.tf for pose in camera_poses]
    annotation_imgs = project_mesh_to_2d(
        oriented_models, camera_poses, model_colors, intrinsic)

    if args.visualize:
        cv2.namedWindow('Object Mask Visualization',
                        flags=cv2.WINDOW_AUTOSIZE | cv2.WINDOW_GUI_EXPANDED)
        stop = False
        for pose_idx, anno_img in enumerate(annotation_imgs):
            if stop or not cv2.getWindowProperty('Object Mask Visualization', cv2.WND_PROP_VISIBLE):
                break

            if np.shape(anno_img)[2] == 3:
                anno_img = cv2.cvtColor(anno_img, cv2.COLOR_RGB2BGRA)

            if(args.background):
                convert_flag = cv2.COLOR_RGBA2BGRA
                if np.shape(orig_imgs[pose_idx])[2] == 3:
                    convert_flag = cv2.COLOR_RGB2BGRA
                masked_image = cv2.cvtColor(np.asarray(
                    orig_imgs[pose_idx]), convert_flag)
                alpha = args.alpha

                blended = cv2.addWeighted(
                    anno_img, 1-alpha, masked_image, alpha, 0)

                if args.rotate:
                    blended = cv2.rotate(blended, cv2.ROTATE_180)
                    anno_img = cv2.rotate(anno_img, cv2.ROTATE_180)

                masks = get_masks_from_render(model_colors, anno_img)
                bboxes = get_bbox_from_masks(masks)
                for idx, bbox in enumerate(bboxes):
                    if bbox:
                        x, y, x1, y1 = bbox
                        color = [model_colors[idx][2],
                                 model_colors[idx][1], model_colors[idx][0]]
                        cv2.rectangle(blended, (x, y), (x1, y1), color, 2)
                        obj_name = objects[idx][0].name
                        put_text(obj_name, blended, x-1, y1+30, color)
                    else:
                        print("No bbox available. Object not visible.")
            else:
                blended = anno_img

            print(f"Scene: {pose_idx}")
            cv2.imshow('Object Mask Visualization', blended)

            outimg = cv2.cvtColor(blended, cv2.COLOR_BGRA2BGR)
            if args.output:
                output = os.path.join(args.output, f"mask_{pose_idx:03d}.png")
                cv2.imwrite(output, outimg)

            while cv2.getWindowProperty('Object Mask Visualization', cv2.WND_PROP_VISIBLE):
                key = cv2.waitKey(1)
                if key == ord('q'):
                    cv2.destroyAllWindows()
                    stop = True
                    break
                elif key == ord('n'):
                    break
    else:
        filepaths = scene_file_reader.get_images_rgb_path(args.scene_id)
        pbar = tqdm(enumerate(annotation_imgs), desc=f"Saving")
        for pose_idx, anno_img in pbar:
            if np.shape(anno_img)[2] == 3:
                anno_img = cv2.cvtColor(anno_img, cv2.COLOR_RGB2BGRA)
            masks = get_masks_from_render(model_colors, anno_img)

            for i, mask in enumerate(masks):
                filename = f"{objects[i][0].name}_" + \
                    f"{i:03d}_" + os.path.basename(filepaths[pose_idx])
                output_path = os.path.join(
                    args.output, filename)
                mask_image = np.array(mask) * 255
                cv2.imwrite(output_path, mask_image)
                pbar.set_description(f"Saving: {output_path}")
