import open3d as o3d
import trimesh
import os
import errno


class MeshReader:
    def __init__(self, file, scale=1):
        if(os.path.exists(file)):
            self.file = file  # could check here if file exists
            self.scale = scale
        else:
            self.file = None
            raise FileNotFoundError(
                errno.ENOENT, os.strerror(errno.ENOENT), file)

    def __str__(self):
        return 'mesh_file: {self.file}'

    def as_o3d(self):
        return o3d.io.read_triangle_mesh(self.file).scale(self.scale, [0, 0, 0])

    def as_trimesh(self):
        scale_matrix = trimesh.transformations.scale_matrix(self.scale, [
                                                            0, 0, 0])
        return trimesh.load_mesh(self.file).apply_transform(scale_matrix)

    def as_bpy_mesh(self):
        import bpy
        import mathutils
        from io_mesh_ply import import_ply

        mesh = None
        # load the file depending pn extension ply obj something else?
        if self.file.endswith('.obj'):
            # load an .obj file:
            print("wavefront obj files not yet supported")
            raise ValueError(f"File %s not supported", self.file)
            # bpy.ops.import_scene.obj(filepath=self.file)
        elif self.file.endswith('.ply'):
            mesh = import_ply.load_ply_mesh(self.file, "dummy")
            scale_matrix = mathutils.Matrix().Scale(float(self.scale), 4)
            mesh.transform(scale_matrix)

            # add a default material to ply file
            #mat = bpy.data.materials.new(name="ply_material")
            #mat.use_nodes = True
            #loaded_objects = list(set(bpy.context.selected_objects) - previously_selected_objects)
            # for obj in loaded_objects:
            #    obj.data.materials.append(mat)
        else:
            raise ValueError("File %s not supported" % self.file)

        return mesh


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
