# 3D-DAT Annotation Tool

This tool provides an easy way to annotate poses of objects within a table top scene.
It provides a blender front-end and a dataset-api for importing & annotating recorded data and object models.
The recorded data has to include the following informations:
1. rgb images from multiple views
2. camera poses from each view
3. camera intrinsics
4. object models
5. [optional] depth images from each view, necessary for auto-align feature

## Installation
Here we describe the necessary steps to install the annotation toolkit.

### Install blender
We tested the tools with blender version 2.92 (but higher versions should work too).
Download and extract blender 2.92:
```
cd ~
wget https://download.blender.org/release/Blender2.92/blender-2.92.0-linux64.tar.xz
tar -xf blender-2.92.0-linux64.tar.xz
rm blender-2.92.0-linux64.tar.xz
```
Adjust the paths to the desired extracted location.

You can start blender now from the command line. Note that you only see console outputs when you start it from command line which is also useful for debugging.

### Install annotation tool as blender addon

Clone the repository, add it to blender add ons:
```
cd ~
git clone --recursive git@github.com:markus-suchi/3d-dat.git
cd blender-2.92.0-linux64/2.92/scripts/addons
ln -s ~/3d-dat/ 3d-dat
```

Install dependencies in blender python:
```
cd ~/blender-2.92.0-linux64/2.92/python/bin
./python3.7m -m ensurepip
./python3.7m -m pip install --upgrade pip
./python3.7m -m pip install --upgrade setuptools wheel
./python3.7m -m pip install ~/3d-dat
```

#### Activate the blender addon
- Start blender
- Open "Edit" -> "Preferences..."
- Go to "Add-ons", activate "Testing" tab at the top
- Click on the checkbox to activate "User Interface: 3D-DAT - Annotation Plugin" and close preferences

## Folder structure and Config-Files:
We give a brief example of a possible folder structure which can be handled by our tools, and use it to describe corresponding configuration files.
```
/dataset
         dataset.yaml                              dataset config file
        /objects                                   for each object one folder with mesh information
               object_library.yaml                 object library configuration file
               /object_1
                        /object_1.ply              mesh file in ply format
        /scenes                                    for each scene one folder 
                /001                               scene identifier folder
                    /rgb                           images (png or jpg) 
                        /000001.png                Sortable by filename should reflect chronological order which matches recordings of views
                        ..
                        /000100.png
                    /depth                         depth-images (openni-format: uint16 in mm)
                        /000001.png                 
                        ..
                        /000100.png
                    groundtruth_handeye.txt        camera poses               

/annotations
            /001                                   corrsponding scene identifier folder
                /pose.yaml
/reconstructions/001                               reconstructions used for auto-alignment
                /reconstruction.ply
                /reconstruction_align.ply
                /reconstruction_visual.ply
```
Camera poses should adhere to the following format:

groundtruth_handeye.txt
```
each line contains pose in TUM format: 
id, tx, ty, tz, rx, ry, rz, rw

current view: id
translation: tx,ty,tz
rotation as quaterion: rx, ry, rz, rw
```

Annotations results are stored in a yaml file:

pose.yaml
```
id: '<name>'
pose: 4x4 matrix (flattened, 16 entries)
```

Two config files are necessary to properly describe a dataset.
1. dataset config file: contains configuration for the location of images, annotations and reconstructions
2. object library file: contains configuration for object models

dataset.yaml (all path can be absolute or relative to this config file):
```
---
General:                                                        #general settings for datasets
    scenes_dir: scenes                                          #folder of the scene data, each subfolder (scene_identifier) contains one scene record
    rgb_dir: rgb                                                #subfolder of scene_dir/scene_identifier for image data
    depth_dir: depth                                            #subfolder of scene_dir/scene_identifier for depth data
    camera_intrinsics_file: camera.yaml                         #camera intrinsic file (in scene folder or scene identifier subfolder)  
    camera_pose_file: groundtruth_handeye.txt                   #camera poses file in scene_dir/scene_identifier
    object_library_file: objects/object_library.yaml            #path to object_library config
    annotation_dir: annotations                                 #subfolder for annotation data
    object_pose_file: poses.yaml                                #name of annotated poses file within annotation_dir
    mask_dir: masks                                             #folder for generated masks within annotation_dir
    reconstruction_dir: reconstructions                         #folder to place reconstructions for align feature
    
Reconstruction:                                                 #settings for reconstructions
    debug_mode: False                                           #visualize debug output
    max_depth: 1.3                                              #trehshold max depth values
    voxel_size: 0.004                                           #voxel size for TSDF volume
    tsdf_cubic_size: 1.5                                        #dimensions of TSDF volume
    icp_method: color                                           #icp_methods: see open3D options    
    sdf_trunc: 0.018                                            #truncate threshold
    simplify: False                                             #downsample resulting mesh using number of traingles entry
    triangles: 100000                                           #resulting triangles for mesh (lower will downsample more)                
    cluster: False                                              #save only largest cluster after reconstruction
```

The entries of the object library describe the objects used in the scene.

object_library.yaml (paths relative to this config file):
```
- id : 'object_1'                                                #unique identifier string for this object
  name: test object                                              #descriptive name of the object
  mesh: object_1/object_1.ply                                    #path to mesh (supports ply files and vertex coloring if present)
  class: test                                                    #grouping to class names
  description: Example object for documentation.                 #additional description
  color: [255,0,0]                                               #default color for visualising in blender
  scale: 0.001                                                   #rescaling factor to meters
...
```

## Usage
Annotation can start without auto-align right away. 
If you want the assistant to be active (recommended), 
the following commands will create the necessary files.

### create auto-align data 
For this feature it is necessary to provide depth images of your recorded view. 
You can use data recorded from a depth camera or use our NERF-based depth image generator to create depth from rgb images of your recordings.

#### create depth images using NERF
Soon to come...

#### create reconstructions
The depth data is used to generate reconstructions of the scene. They can be generated for a specific scene using the command below.
```
./python3.7m ~/3d-dat/scripts/reconstruct.py -d <path_to_dataset_config_file> -- scene_id '<scene_identifier>'
```
After generating all the reconstructions for the scenes the data is ready for annotation.

### Annotation
- Choose "File" -> "New" -> "3D-DAT"
- In the main window to the top right expand the Property Window
- Select "3D-DAT" to see the addon menu

Get started by:
- Click "Load Dataset" and choose a dataset config file
- In the Dropdown Scene menu choose a scene and click "Import Scene"
- Add objects to the scene by selecting objects from the "Object Library"
- **Attention: After the import toggle view to cameras using "NUMPAD 0"**
- Use blenders translate and rotate widgets to place the object within a scene
- Use CTRL-Shift arrow keys or Shift Mouswheel to scroll through views
- After rough aligment use the "Align" button
- Repeat placement and "Align" to improve until you are satisfied with the result
- Click "Save Objects" to finish the annotation

## Scripts
Here we describe some example scripts which are used to visualize or generate additional annotated data.
### visualize single view in scene using pointcloud and mesh objects
```
python vis_annotation.py -c ~/dataset/dataset.yaml -s "001"
```

### visualize & save object masks of single view in scene 
```
python vis_mask.py -c ~/dataset/dataset.yaml -s "001" -v
```

