# install packages for blender
```
cd ~/blender-2.92.0-linux64/2.92/python/bin
./python3.7m -m ensurepip
./python3.7m -m pip install --upgrade pip
./python3.7m -m pip install --upgrade setuptools wheel
./python3.7m -m pip install -e .
```

# visualize single view in scene using pointcloud and mesh objects
```
python vis_annotation.py -c ~/temp/dataset/config.cfg -s "001"
```

# visualize object masks of single view in scene 
```
python vis_mask.py -c ~/temp/dataset/config.cfg -s "001"
```

# create virtual environment (needs >= python3.6)
```
virtualenv --python=python3.6 venv
source venv/bin/activate  # linux
python -m pip install --upgrade pip
pip install --upgrade setuptools wheel
```
# install in editable mode
```
pip install -e .
```

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
pose: 4x4 matrix


groundtruth_handeye.txt
---------------------------------------------------------------
each line contains pose in TUM format: 
id, tx, ty, tz, rx, ry, rz, rw

current view: id
translation: tx,ty,tz
rotation as quaterion: rx, ry, rz, rw
