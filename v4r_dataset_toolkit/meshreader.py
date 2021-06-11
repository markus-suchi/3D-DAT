import open3d as o3d
import trimesh


class MeshReader:
    def __init__(self, file):
        self.file = file

    def as_o3d(self):
        return o3d.io.read_triangle_mesh(self.file)

    def as_trimesh(self):
        return trimesh.load_mesh(self.file)

    def as_blender(self):
        # import bpy
        # load the file depending pn extension ply obj something else?
        # set some attributes depending on name / id?
        pass
