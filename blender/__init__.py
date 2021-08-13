bl_info = {
    "author": "Markus Suchi",
    "name": "V4R - Annotation Plugin",
    "description": "Tools for annotating RGBD-data",
    "warning": "",
    "version": (0, 1),
    "blender": (2, 92, 0), 
    "support": 'TESTING',
    "category": 'User Interface'
}

if "bpy" in locals():
    import importlib
    importlib.reload(v4r_annotation_tool)
    importlib.reload(v4r_dataset_toolkit)
else:
    from . import v4r_dataset_toolkit as v4r
    from . import v4r_annotation_tool


#### REGISTER ###
def register():
    v4r_annotation_tool.register()

def unregister():
    v4r_annotation_tool.unregister()


if __name__ == "__main__":
    register()
