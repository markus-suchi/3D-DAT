from collections import UserDict
import itertools
import numpy as np
import os
import yaml

from .meshreader import MeshReader

# Decide which attributes are optional
# Idea: Minimal is id and mesh file


class Object:
    def __init__(self, id=None, name=None, class_id=None, description=None, mesh_file=None, color=[0, 0, 0], scale=1):
        self.id = id
        self.name = name
        self.class_id = class_id
        self.scale = scale
        self.description = description
        self.mesh = MeshReader(mesh_file, self.scale) if mesh_file else None
        self.color = color

    def __str__(self):
        if self.mesh is None:
            mesh_string = None
        else:
            mesh_string = self.mesh.file

        return f'id: {self.id}\n' \
            f'name: {self.name}\n' \
            f'class: {self.class_id}\n' \
            f'description: {self.description}\n' \
            f'color: {self.color}\n' \
            f'mesh file: {mesh_string}\n' \
            f'scale: {self.scale}'


class ObjectLibrary(UserDict):
    @classmethod
    def create(cls, path):
        with open(path) as fp:
            root, _ = os.path.split(path)
            object_dict = cls()
            for obj in yaml.load(fp, Loader=yaml.FullLoader):
                # check mesh
                mesh = obj.get('mesh')
                scale = obj.get('scale')
                object_dict[obj['id']] = Object(id=obj['id'],
                                                name=obj.get('name'),
                                                class_id=obj.get('class'),
                                                description=obj.get(
                                                    'description'),
                                                color=obj.get('color'),
                                                mesh_file=os.path.join(root, mesh) if mesh else None,
                                                scale=scale if scale else 1)
            return object_dict

    def as_list(self, ids=None):
        return list(map(self.__getitem__, ids or [])) or list(self.values())
