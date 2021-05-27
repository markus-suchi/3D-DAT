Verifying annotated sample test scene:

# visualize single view in scene using pointcloud and mesh objects
python vis_annotation.py -d ~/temp/BURG/scenes/003

# visualize object masks of single view in scene 
python vis_mask.py -d ~/temp/BURG/scenes/003



# create virtual environment (needs >= python3.6)
virtualenv --python=python3.6 venv
source venv/bin/activate  # linux

# might want to upgrade pip and packages required for setup
python -m pip install --upgrade pip
pip install --upgrade setuptools wheel

# install burg_toolkit in editable mode
pip install -e .

Dependencies:
numpy
open3d
trimesh
tqdm
pyyaml


Folder and Files:
---------------------------------------------------------------
/objects                                   for each object one folder with mesh information
/scenes/001-003                            for each scene one folder containing the following infos
               /rgb                           
               /depth
               groundtruth_handeye.txt     camera poses
               pose.yaml                   object poses 


pose.yaml
---------------------------------------------------------------
id: <name>
path: <object path>/<file>
pose: 4x4 matrix


groundtruth_handeye.txt
---------------------------------------------------------------
each line contains pose in TUM format: 
id, tx, ty, tz, rx, ry, rz, rw

current view: id
translation: tx,ty,tz
rotation as quaterion: rx, ry, rz, rw


associations.txt
---------------------------------------------------------------
ignore, it is an intermediate file for reconstructions
