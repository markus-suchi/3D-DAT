import open3d as o3d
import trimesh
import os
import errno


class MeshReader:
    def __init__(self, file):
        if(os.path.exists(file)):
            self.file = file  # could check here if file exists
        else:
            self.file = None
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), file)

    def __str__(self):
        return 'mesh_file: {self.file}'

    def as_o3d(self):
        return o3d.io.read_triangle_mesh(self.file)

    def as_trimesh(self):
        return trimesh.load_mesh(self.file)

    def as_bpy_mesh(self):
        # import bpy
        # load the file depending pn extension ply obj something else?
        # set some attributes depending on name / id?
        pass

class ImageReader:
    def __init__(self, file):
        if(os.path.exists(file)):
            self.file = file  # could check here if file exists
        else:
            self.file = None
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), file)

    def __str__(self):
        return f'rgb_file: {self.file}'

    def as_o3d(self):
        return o3d.io.read_image(self.file)

    def as_bpy_image(self):
        import bpy
        return bpy.data.images.load(self.file)
